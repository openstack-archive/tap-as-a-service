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


from neutron.agent.common import config
from neutron_taas.common import topics
from neutron_taas.services.taas.agents import taas_agent_api as api

from oslo_config import cfg
from oslo_log import log as logging
from oslo_utils import importutils

LOG = logging.getLogger(__name__)


class TaasOvsPluginApi(api.TaasPluginApiMixin):
    # Currently there are not any APIs from the the agent towards plugin

    def __init__(self, topic, host):
        super(TaasOvsPluginApi, self).__init__(topic, host)
        return


class TaasOvsAgentRpcCallback(api.TaasAgentRpcCallbackMixin):

    def __init__(self, conf):

        LOG.debug("TaaS OVS Agent initialize called")

        self.conf = conf
        taas_driver_class_path = cfg.CONF.taas.driver
        self.taas_enabled = cfg.CONF.taas.enabled

        self.root_helper = config.get_root_helper(conf)

        try:
            self.taas_driver = importutils.import_object(
                taas_driver_class_path, self.root_helper)
            LOG.debug("TaaS Driver Loaded: '%s'", taas_driver_class_path)
        except ImportError:
            msg = _('Error importing TaaS device driver: %s')
            raise ImportError(msg % taas_driver_class_path)

        # setup RPC to msg taas plugin
        self.taas_plugin_rpc = TaasOvsPluginApi(topics.TAAS_PLUGIN,
                                                conf.host)
        super(TaasOvsAgentRpcCallback, self).__init__()

        return

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
        service_host = tap_flow_msg['service_host']
        if host != self.conf.host and service_host != self.conf.host:
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
        service_host = tap_flow_msg['service_host']
        if host != self.conf.host and service_host != self.conf.host:
            return
        LOG.debug("In RPC Call for Delete Tap Flow: MSG=%s" % tap_flow_msg)

        return self._invoke_driver_for_plugin_api(
            context,
            tap_flow_msg,
            'delete_tap_flow')

    def periodic_tasks(self, argv):
        #
        # Regenerate the flow in br-tun's TAAS_SEND_FLOOD table
        # to ensure all existing tunnel ports are included.
        #
        self.taas_driver.add_update_vlan_submit_flow()
        pass
