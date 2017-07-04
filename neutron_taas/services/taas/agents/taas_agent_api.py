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

from neutron_taas._i18n import _
from oslo_config import cfg
import oslo_messaging as messaging

from neutron.common import rpc as n_rpc

TaasOpts = [
    cfg.StrOpt(
        'driver',
        default='',
        help=_("Name of the TaaS Driver")),
    cfg.BoolOpt(
        'enabled',
        default=False,
        help=_("Enable TaaS")),
]
cfg.CONF.register_opts(TaasOpts, 'taas')


class TaasPluginApiMixin(object):

    # Currently there are no Calls the Agent makes towards the Plugin.

    def __init__(self, topic, host):
        self.host = host
        target = messaging.Target(topic=topic, version='1.0')
        self.client = n_rpc.get_client(target)
        super(TaasPluginApiMixin, self).__init__()
        return


class TaasAgentRpcCallbackMixin(object):
    """Mixin for Taas agent Implementations."""

    def __init__(self):
        super(TaasAgentRpcCallbackMixin, self).__init__()

    def consume_api(self, agent_api):
        """Receive neutron agent API object

        Allows an extension to gain access to resources internal to the
        neutron agent and otherwise unavailable to the extension.
        """
        self.agent_api = agent_api

    def create_tap_service(self, context, tap_service, host):
        """Handle RPC cast from plugin to create a tap service."""
        pass

    def delete_tap_service(self, context, tap_service, host):
        """Handle RPC cast from plugin to delete a tap service."""
        pass

    def create_tap_flow(self, context, tap_flow_msg, host):
        """Handle RPC cast from plugin to create a tap flow"""
        pass

    def delete_tap_flow(self, context, tap_flow_msg, host):
        """Handle RPC cast from plugin to delete a tap flow"""
        pass
