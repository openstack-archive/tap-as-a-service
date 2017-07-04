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
from neutron import manager

from neutron_taas.common import topics
from neutron_taas.services.taas.agents import taas_agent_api as api

from oslo_config import cfg
from oslo_log import log as logging
from oslo_service import service

LOG = logging.getLogger(__name__)


class TaasOvsPluginApi(api.TaasPluginApiMixin):
    # Currently there are not any APIs from the the agent towards plugin

    def __init__(self, topic, host):
        super(TaasOvsPluginApi, self).__init__(topic, host)
        return


class TaasOvsAgentRpcCallback(api.TaasAgentRpcCallbackMixin):

    def __init__(self, conf, driver_type):
        LOG.debug("TaaS OVS Agent initialize called")

        self.conf = conf
        self.driver_type = driver_type

        super(TaasOvsAgentRpcCallback, self).__init__()

    def initialize(self):
        self.taas_driver = manager.NeutronManager.load_class_for_provider(
            'neutron_taas.taas.agent_drivers', self.driver_type)()
        self.taas_driver.consume_api(self.agent_api)
        self.taas_driver.initialize()

        self._taas_rpc_setup()
        TaasOvsAgentService(self).start()

    def consume_api(self, agent_api):
        self.agent_api = agent_api

    def _invoke_driver_for_plugin_api(self, context, args, func_name):
        LOG.debug("Invoking Driver for %(func_name)s from agent",
                  {'func_name': func_name})

        try:
            self.taas_driver.__getattribute__(func_name)(args)
        except Exception:
            LOG.debug("Failed to invoke the driver")

        return

    def create_tap_service(self, context, tap_service, host):
        """Handle Rpc from plugin to create a firewall."""
        if host != self.conf.host:
            return
        LOG.debug("In RPC Call for Create Tap Service: MSG=%s" % tap_service)

        return self._invoke_driver_for_plugin_api(
            context,
            tap_service,
            'create_tap_service')

    def create_tap_flow(self, context, tap_flow_msg, host):
        if host != self.conf.host:
            return
        LOG.debug("In RPC Call for Create Tap Flow: MSG=%s" % tap_flow_msg)

        return self._invoke_driver_for_plugin_api(
            context,
            tap_flow_msg,
            'create_tap_flow')

    def delete_tap_service(self, context, tap_service, host):
        #
        # Cleanup operations must be performed by all hosts
        # where the source and/or destination ports associated
        # with this tap service were residing.
        #
        LOG.debug("In RPC Call for Delete Tap Service: MSG=%s" % tap_service)

        return self._invoke_driver_for_plugin_api(
            context,
            tap_service,
            'delete_tap_service')

    def delete_tap_flow(self, context, tap_flow_msg, host):
        if host != self.conf.host:
            return
        LOG.debug("In RPC Call for Delete Tap Flow: MSG=%s" % tap_flow_msg)

        return self._invoke_driver_for_plugin_api(
            context,
            tap_flow_msg,
            'delete_tap_flow')

    def _taas_rpc_setup(self):
        # setup RPC to msg taas plugin
        self.taas_plugin_rpc = TaasOvsPluginApi(
            topics.TAAS_PLUGIN, self.conf.host)

        endpoints = [self]
        conn = n_rpc.create_connection()
        conn.create_consumer(topics.TAAS_AGENT, endpoints, fanout=False)
        conn.consume_in_threads()

    def periodic_tasks(self):
        #
        # Regenerate the flow in br-tun's TAAS_SEND_FLOOD table
        # to ensure all existing tunnel ports are included.
        #
        self.taas_driver.update_tunnel_flood_flow()


class TaasOvsAgentService(service.Service):
    def __init__(self, driver):
        super(TaasOvsAgentService, self).__init__()
        self.driver = driver

    def start(self):
        super(TaasOvsAgentService, self).start()
        self.tg.add_timer(
            int(cfg.CONF.taas_agent_periodic_interval),
            self.driver.periodic_tasks,
            None
        )
