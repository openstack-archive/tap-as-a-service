# Copyright 2017 FUJITSU LABORATORIES LTD.
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

from neutron_lib.agent import l2_extension

from neutron_taas.services.taas.agents.common import taas_agent

from oslo_config import cfg
from oslo_log import log as logging

LOG = logging.getLogger(__name__)

OPTS = [
    cfg.IntOpt(
        'taas_agent_periodic_interval',
        default=5,
        help=_('Seconds between periodic task runs')
    )
]
cfg.CONF.register_opts(OPTS)


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

    @abc.abstractmethod
    def create_tap_service(self, tap_service):
        """Create a Tap Service request in driver."""

    @abc.abstractmethod
    def create_tap_flow(self, tap_flow):
        """Create a tap flow request in driver."""

    @abc.abstractmethod
    def delete_tap_service(self, tap_service):
        """delete a Tap Service request in driver."""

    @abc.abstractmethod
    def delete_tap_flow(self, tap_flow):
        """Delete a tap flow request in driver."""


class TaasAgentExtension(l2_extension.L2AgentExtension):

    def initialize(self, connection, driver_type):
        """Initialize agent extension."""
        self.taas_agent = taas_agent.TaasAgentRpcCallback(
            cfg.CONF, driver_type)
        self.taas_agent.consume_api(self.agent_api)
        self.taas_agent.initialize()

    def consume_api(self, agent_api):
        """Receive neutron agent API object

        Allows an extension to gain access to resources internal to the
        neutron agent and otherwise unavailable to the extension.
        """
        self.agent_api = agent_api

    def handle_port(self, context, port):
        pass

    def delete_port(self, context, port):
        pass
