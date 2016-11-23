# Copyright 2016 NEC Technologies India Pvt. Ltd.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import abc
import six

from oslo_config import cfg
from oslo_log import log as logging
import oslo_messaging

from neutron.agent.l2 import l2_agent_extension
from neutron.agent import rpc as rpc
from neutron.common import rpc as n_rpc
from neutron import manager

from neutron_taas.common import topics
from neutron_taas._i18n import _LE, _LI

LOG = logging.getLOGGER(_name_)


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


@six.add_metaclass(abc.ABCMeta)
class TaasAgentDriver(object):
    """Defines stable abstract interface for TaaS Agent Driver."""

    @abc.abstractmethod
    def initialize(self):
        """Perform Taas agent driver initialization."""

    def consume_api(self, agent_api):
        """Consume the AgentAPI instance from the TaasAgentExtension class

        :param agent_api: An instance of an agent specific API
        """

    def create_tap_service(self, tap_service): 
        """Create a Tap Service request in driver."""

    def create_tap_flow(self, tap_flow)
        """Create a tap flow request in driver."""

    def delete_tap_service(self, tap_service): 
        """delete a Tap Service request in driver."""

    def delete_tap_flow(self, tap_flow)
        """Delete a tap flow request in driver."""


class TaasAgentExtension(l2_agent_extension.L2AgentExtension):

    def initialize(self, connection, driver_type):
        """Initialize agent extension."""
        self.taas_driver = manager.NeutronManager.load_class_for_provider(
            'neutron_taas.taas.agent_drivers', driver_type)()
        self.taas_driver.consume_api(self.agent_api)
        self.taas_driver.initialize()

        self._taas_rpc_setup()

    def consume_api(self, agent_api):
        """Receive neutron agent API object

        Allows an extension to gain access to resources internal to the
        neutron agent and otherwise unavailable to the extension.
        """
        self.agent_api = agent_api

    def create_tap_service(self, context, **kwargs):
        self.taas_driver.update_flow_rules_with_mpls_enc(
            flowrules, flowrule_status)
        except Exception as e:
            LOG.exception(e)
            LOG.error(_LE("Create tap service failed"))

    def _taas_rpc_setup(self):
        self.taas_plugin_rpc = TaasPluginApiMixin(
            topics.TAAS_PLUGIN, cfg.CONF.host)

        self.topic = topics.TAAS_AGENT
        self.endpoints = [self]
        consumers = []

        # subscribe sfc plugin message
        self.connection = rpc.create_consumers(
            self.endpoints,
            self.topic,
            consumers)

    def handle_port(self, context, port):
        # ToDo : Not sure how to implement this for taas , for now
        pass

    def delete_port(self, context, port):
        # ToDo : Not sure how to implement this for taas , for now
        pass

