# Copyright (C) 2018 AT&T
# Copyright (C) 2016 Midokura SARL.
# Copyright (C) 2015 Ericsson AB
# Copyright (c) 2015 Gigamon
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

from neutron_lib.api.definitions import portbindings
from neutron_lib import constants
from neutron_lib import exceptions as n_exc
from neutron_lib import rpc as n_rpc

from neutron_taas.common import constants as taas_consts
from neutron_taas.common import topics
from neutron_taas.services.taas import service_drivers
from neutron_taas.services.taas.service_drivers import (service_driver_context
                                                        as sd_context)
from neutron_taas.services.taas.service_drivers import taas_agent_api
from neutron_taas.services.taas.taas_plugin import TaasPlugin

from oslo_config import cfg
from oslo_log import log as logging
from oslo_utils import excutils

LOG = logging.getLogger(__name__)


class TaasCallbacks(object):

    def __init__(self, rpc_driver, plugin):
        super(TaasCallbacks, self).__init__()
        self.rpc_driver = rpc_driver
        self.plugin = plugin
        return

    def sync_tap_resources(self, context, sync_tap_res, host):
        """Handle Rpc from Agent to sync up Tap resources."""
        LOG.debug("In RPC Call for Sync Tap Resources: MSG=%s" % sync_tap_res)

        # Get list of configured tap-services
        active_tss = self.plugin.get_tap_services(
            context,
            filters={'status': [constants.ACTIVE]})

        for ts in active_tss:
            # If tap-service port is bound to a different host than the one
            # which sent this RPC, then continue.
            ts_port = self.plugin._get_port_details(
                context, ts['port_id'])
            if ts_port['binding:host_id'] != host:
                continue

            driver_context = sd_context.TapServiceContext(self.plugin,
                                                          context, ts)
            try:
                self.rpc_driver.create_tap_service_postcommit(driver_context)
            except Exception:
                with excutils.save_and_reraise_exception():
                    LOG.error("Failed to create tap service on driver,"
                              "deleting tap_service %s", ts['id'])
                    super(TaasPlugin, self.plugin).delete_tap_service(
                        context, ts['id'])

            # Get all the active tap flows for current tap-service
            active_tfs = self.plugin.get_tap_flows(
                context,
                filters={'tap_service_id': [ts['id']],
                         'status': [constants.ACTIVE]})

            # Filter out the tap flows associated with distinct tap services
            for tf in active_tfs:
                driver_context = sd_context.TapFlowContext(self.plugin,
                                                           context, tf)
                try:
                    self.rpc_driver.create_tap_flow_postcommit(driver_context)
                except Exception:
                    with excutils.save_and_reraise_exception():
                        LOG.error("Failed to create tap flow on driver,"
                                  "deleting tap_flow %s", tf['id'])
                        super(TaasPlugin, self.plugin).delete_tap_flow(
                            context, tf['id'])


class TaasRpcDriver(service_drivers.TaasBaseDriver):
    """Taas Rpc Service Driver class"""

    def __init__(self, service_plugin):
        LOG.debug("Loading TaasRpcDriver.")
        super(TaasRpcDriver, self).__init__(service_plugin)
        self.endpoints = [TaasCallbacks(self, service_plugin)]
        self.conn = n_rpc.Connection()
        self.conn.create_consumer(topics.TAAS_PLUGIN,
                                  self.endpoints, fanout=False)

        self.conn.consume_in_threads()

        self.agent_rpc = taas_agent_api.TaasAgentApi(
            topics.TAAS_AGENT,
            cfg.CONF.host
        )

        return

    def _get_taas_id(self, context, tf):
        ts = self.service_plugin.get_tap_service(context,
                                                 tf['tap_service_id'])
        taas_id = (self.service_plugin.get_tap_id_association(
            context,
            tap_service_id=ts['id']))['taas_id']
        return taas_id

    def create_tap_service_precommit(self, context):
        ts = context.tap_service
        tap_id_association = context._plugin.create_tap_id_association(
            context._plugin_context, ts['id'])
        context.tap_id_association = tap_id_association

    def create_tap_service_postcommit(self, context):
        """Send tap service creation RPC message to agent.

        This RPC message includes taas_id that is added vlan_range_start to
        so that taas-ovs-agent can use taas_id as VLANID.
        """
        # Get taas id associated with the Tap Service
        ts = context.tap_service
        tap_id_association = context.tap_id_association
        taas_vlan_id = tap_id_association['taas_id']
        port = self.service_plugin._get_port_details(context._plugin_context,
                                                     ts['port_id'])
        host = port['binding:host_id']

        rpc_msg = {'tap_service': ts,
                   'taas_id': taas_vlan_id,
                   'port': port}

        self.agent_rpc.create_tap_service(context._plugin_context,
                                          rpc_msg, host)
        return

    def delete_tap_service_precommit(self, context):
        pass

    def delete_tap_service_postcommit(self, context):
        """Send tap service deletion RPC message to agent.

        This RPC message includes taas_id that is added vlan_range_start to
        so that taas-ovs-agent can use taas_id as VLANID.
        """
        ts = context.tap_service
        tap_id_association = context.tap_id_association
        taas_vlan_id = tap_id_association['taas_id']

        try:
            port = self.service_plugin._get_port_details(
                context._plugin_context,
                ts['port_id'])
            host = port['binding:host_id']
        except n_exc.PortNotFound:
            # if not found, we just pass to None
            port = None
            host = None

        rpc_msg = {'tap_service': ts,
                   'taas_id': taas_vlan_id,
                   'port': port}

        self.agent_rpc.delete_tap_service(context._plugin_context,
                                          rpc_msg, host)
        return

    def create_tap_flow_precommit(self, context):
        pass

    def create_tap_flow_postcommit(self, context):
        """Send tap flow creation RPC message to agent."""
        tf = context.tap_flow
        taas_id = self._get_taas_id(context._plugin_context, tf)
        # Extract the host where the source port is located
        port = self.service_plugin._get_port_details(context._plugin_context,
                                                     tf['source_port'])
        host = port['binding:host_id']
        port_mac = port['mac_address']
        # Extract the tap-service port
        ts = self.service_plugin.get_tap_service(context._plugin_context,
                                                 tf['tap_service_id'])
        ts_port = self.service_plugin._get_port_details(
            context._plugin_context, ts['port_id'])

        # Send RPC message to both the source port host and
        # tap service(destination) port host
        rpc_msg = {'tap_flow': tf,
                   'port_mac': port_mac,
                   'taas_id': taas_id,
                   'port': port,
                   'tap_service_port': ts_port}

        self.agent_rpc.create_tap_flow(context._plugin_context, rpc_msg, host)
        return

    def delete_tap_flow_precommit(self, context):
        pass

    def delete_tap_flow_postcommit(self, context):
        """Send tap flow deletion RPC message to agent."""
        tf = context.tap_flow
        taas_id = self._get_taas_id(context._plugin_context, tf)
        # Extract the host where the source port is located
        port = self.service_plugin._get_port_details(context._plugin_context,
                                                     tf['source_port'])
        host = port['binding:host_id']
        port_mac = port['mac_address']
        # Extract the tap-service port
        ts = self.service_plugin.get_tap_service(context._plugin_context,
                                                 tf['tap_service_id'])
        ts_port = self.service_plugin._get_port_details(
            context._plugin_context, ts['port_id'])

        src_vlans_list = []
        vlan_filter_list = []

        if port.get(portbindings.VNIC_TYPE) == portbindings.VNIC_DIRECT:
            # Get all the tap Flows that are associated with the Tap service
            active_tfs = self.service_plugin.get_tap_flows(
                context._plugin_context,
                filters={'tap_service_id': [tf['tap_service_id']],
                         'status': [constants.ACTIVE]},
                fields=['source_port', 'vlan_filter'])

            for tap_flow in active_tfs:
                source_port = self.service_plugin._get_port_details(
                    context._plugin_context, tap_flow['source_port'])

                LOG.debug("taas: active TF's source_port %(source_port)s",
                          {'source_port': source_port})

                src_vlans = ""
                if source_port.get(portbindings.VIF_DETAILS):
                    src_vlans = source_port[portbindings.VIF_DETAILS].get(
                        portbindings.VIF_DETAILS_VLAN)

                # If no VLAN filter configured on source port,
                # then include all vlans
                if not src_vlans or src_vlans == '0':
                    src_vlans = taas_consts.VLAN_RANGE

                src_vlans_list.append(src_vlans)

                vlan_filter = tap_flow['vlan_filter']
                # If no VLAN filter configured for tap-flow,
                # then include all vlans
                if not vlan_filter:
                    vlan_filter = taas_consts.VLAN_RANGE

                vlan_filter_list.append(vlan_filter)

        # Send RPC message to both the source port host and
        # tap service(destination) port host
        rpc_msg = {'tap_flow': tf,
                   'port_mac': port_mac,
                   'taas_id': taas_id,
                   'port': port,
                   'tap_service_port': ts_port,
                   'source_vlans_list': src_vlans_list,
                   'vlan_filter_list': vlan_filter_list}

        self.agent_rpc.delete_tap_flow(context._plugin_context, rpc_msg, host)
        return
