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

from neutron.common import rpc as n_rpc
from neutron_lib import exceptions as n_exc
from neutron_taas.common import topics
from neutron_taas.services.taas import service_drivers
from neutron_taas.services.taas.service_drivers import taas_agent_api

from oslo_config import cfg
from oslo_log import log as logging

LOG = logging.getLogger(__name__)


class TaasRpcDriver(service_drivers.TaasBaseDriver):
    """Taas Rpc Service Driver class"""

    def __init__(self, service_plugin):
        LOG.debug("Loading TaasRpcDriver.")
        super(TaasRpcDriver, self).__init__(service_plugin)
        self.endpoints = [taas_agent_api.TaasCallbacks(service_plugin)]
        self.conn = n_rpc.create_connection()
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
        # Send RPC message to both the source port host and
        # tap service(destination) port host
        rpc_msg = {'tap_flow': tf,
                   'port_mac': port_mac,
                   'taas_id': taas_id,
                   'port': port}

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
        # Send RPC message to both the source port host and
        # tap service(destination) port host
        rpc_msg = {'tap_flow': tf,
                   'port_mac': port_mac,
                   'taas_id': taas_id,
                   'port': port}

        self.agent_rpc.delete_tap_flow(context._plugin_context, rpc_msg, host)
        return
