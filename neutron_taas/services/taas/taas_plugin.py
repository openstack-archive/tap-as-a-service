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


from oslo_config import cfg
# from oslo import messaging
import oslo_messaging as messaging

from neutron.common import rpc as n_rpc
from neutron.common import topics
from neutron_taas.db import taas_db
from neutron_taas.extensions import taas as taas_ex
from oslo_log import log as logging

LOG = logging.getLogger(__name__)


class TaasCallbacks(object):
    """Currently there are no callbacks to the Taas Plugin."""

    def __init__(self, plugin):
        super(TaasCallbacks, self).__init__()
        self.plugin = plugin
        return


class TaasAgentApi(object):
    """RPC calls to agent APIs"""

    def __init__(self, topic, host):
        self.host = host
        target = messaging.Target(topic=topic, version='1.0')
        self.client = n_rpc.get_client(target)
        return

    def create_tap_service(self, context, tap_service, host):
        LOG.debug("In RPC Call for Create Tap Service: Host=%s, MSG=%s" %
                  (host, tap_service))

        cctxt = self.client.prepare(fanout=True)
        cctxt.cast(context, 'create_tap_service', tap_service=tap_service,
                   host=host)

        return

    def create_tap_flow(self, context, tap_flow_msg, host):
        LOG.debug("In RPC Call for Create Tap Flow: Host=%s, MSG=%s" %
                  (host, tap_flow_msg))

        cctxt = self.client.prepare(fanout=True)
        cctxt.cast(context, 'create_tap_flow', tap_flow_msg=tap_flow_msg,
                   host=host)

        return

    def delete_tap_service(self, context, tap_service, host):
        LOG.debug("In RPC Call for Delete Tap Service: Host=%s, MSG=%s" %
                  (host, tap_service))

        cctxt = self.client.prepare(fanout=True)
        cctxt.cast(context, 'delete_tap_service', tap_service=tap_service,
                   host=host)

        return

    def delete_tap_flow(self, context, tap_flow_msg, host):
        LOG.debug("In RPC Call for Delete Tap Flow: Host=%s, MSG=%s" %
                  (host, tap_flow_msg))

        cctxt = self.client.prepare(fanout=True)
        cctxt.cast(context, 'delete_tap_flow', tap_flow_msg=tap_flow_msg,
                   host=host)

        return


class TaasPlugin(taas_db.Tass_db_Mixin):

    supported_extension_aliases = ["taas"]
    path_prefix = "/taas"
    def __init__(self):

        LOG.debug("TAAS PLUGIN INITIALIZED")
        self.endpoints = [TaasCallbacks(self)]

        self.conn = n_rpc.create_connection(new=True)
        self.conn.create_consumer(
            topics.TAAS_PLUGIN, self.endpoints, fanout=False)
        self.conn.consume_in_threads()

        self.agent_rpc = TaasAgentApi(
            topics.TAAS_AGENT,
            cfg.CONF.host
        )

        return

    def create_tap_service(self, context, tap_service):
        LOG.debug("create_tap_service() called")

        tenant_id = self._get_tenant_id_for_create(context,
                                                   tap_service['tap_service'])

        t_s = tap_service['tap_service']
        port_id = t_s['port_id']

        # Get port details
        port = self._get_port_details(context, port_id)

        # Check if the port is owned by the tenant.
        if port['tenant_id'] != tenant_id:
            raise taas_ex.PortDoesNotBelongToTenant()

        # Extract the host where the port is located
        host = port['binding:host_id']

        if host is not None:
            LOG.debug("Host on which the port is created = %s" % host)
        else:
            LOG.debug("Host could not be found, Port Binding disbaled!")

        # Create tap service in the db model
        ts = super(TaasPlugin, self).create_tap_service(context, tap_service)
        # Get taas id associated with the Tap Service
        tap_id_association = self.get_tap_id_association(
            context,
            tap_service_id=ts['id'])

        taas_vlan_id = (tap_id_association['taas_id'] +
                        cfg.CONF.taas.vlan_range_start)

        if taas_vlan_id > cfg.CONF.taas.vlan_range_end:
            raise taas_ex.TapServiceLimitReached()

        rpc_msg = {'tap_service': ts, 'taas_id': taas_vlan_id, 'port': port}

        self.agent_rpc.create_tap_service(context, rpc_msg, host)

        return ts

    def delete_tap_service(self, context, id):
        LOG.debug("delete_tap_service() called")

        # Get taas id associated with the Tap Service
        tap_id_association = self.get_tap_id_association(
            context,
            tap_service_id=id)

        ts = self.get_tap_service(context, id)

        # Get all the tap Flows that are associated with the Tap service
        # and delete them as well
        t_f_collection = self.get_tap_flows(
            context,
            filters={'tap_service_id': [id]}, fields=['id'])

        for t_f in t_f_collection:
            self.delete_tap_flow(context, t_f['id'])

        # Get the port and the host that it is on
        port_id = ts['port_id']

        port = self._get_port_details(context, port_id)

        host = port['binding:host_id']

        super(TaasPlugin, self).delete_tap_service(context, id)

        taas_vlan_id = (tap_id_association['taas_id'] +
                        cfg.CONF.taas.vlan_range_start)

        rpc_msg = {'tap_service': ts,
                   'taas_id': taas_vlan_id,
                   'port': port}

        self.agent_rpc.delete_tap_service(context, rpc_msg, host)

        return ts

    def create_tap_flow(self, context, tap_flow):
        LOG.debug("create_tap_flow() called")

        tenant_id = self._get_tenant_id_for_create(context,
                                                   tap_flow['tap_flow'])

        t_f = tap_flow['tap_flow']

        # Check if the tenant id of the source port is the same as the
        # tenant_id of the tap service we are attaching it to.

        ts = self.get_tap_service(context, t_f['tap_service_id'])
        ts_tenant_id = ts['tenant_id']

        taas_id = (self.get_tap_id_association(
            context,
            tap_service_id=ts['id'])['taas_id'] +
            cfg.CONF.taas.vlan_range_start)

        if tenant_id != ts_tenant_id:
            raise taas_ex.TapServiceNotBelongToTenant()

        # Extract the host where the source port is located
        port = self._get_port_details(context, t_f['source_port'])
        host = port['binding:host_id']
        port_mac = port['mac_address']

        # create tap flow in the db model
        tf = super(TaasPlugin, self).create_tap_flow(context, tap_flow)

        # Send RPC message to both the source port host and
        # tap service(destination) port host
        rpc_msg = {'tap_flow': tf,
                   'port_mac': port_mac,
                   'taas_id': taas_id,
                   'port': port}

        self.agent_rpc.create_tap_flow(context, rpc_msg, host)

        return tf

    def delete_tap_flow(self, context, id):
        LOG.debug("delete_tap_flow() called")

        tf = self.get_tap_flow(context, id)
        # ts = self.get_tap_service(context, tf['tap_service_id'])

        taas_id = (self.get_tap_id_association(
            context,
            tf['tap_service_id'])['taas_id'] +
            cfg.CONF.taas.vlan_range_start)

        port = self._get_port_details(context, tf['source_port'])
        host = port['binding:host_id']
        port_mac = port['mac_address']

        super(TaasPlugin, self).delete_tap_flow(context, id)

        # Send RPC message to both the source port host and
        # tap service(destination) port host
        rpc_msg = {'tap_flow': tf,
                   'port_mac': port_mac,
                   'taas_id': taas_id,
                   'port': port}

        self.agent_rpc.delete_tap_flow(context, rpc_msg, host)

        return tf
