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

import sys

import eventlet
eventlet.monkey_patch()

from oslo_config import cfg
from oslo_service import service

from neutron.agent.common import config
from neutron.common import config as common_config
from neutron.common import rpc as n_rpc

from neutron_taas._i18n import _
from neutron_taas.common import topics
from neutron_taas.services.taas.agents.common import taas_agent


OPTS = [
    cfg.IntOpt(
        'taas_agent_periodic_interval',
        default=5,
        help=_('Seconds between periodic task runs')
    )
]


class TaaSAgentService(n_rpc.Service):
    def start(self):
        super(TaaSAgentService, self).start()
        if 'OvsTaasDriver' in cfg.CONF.taas.driver:
            self.tg.add_timer(
                cfg.CONF.taas_agent_periodic_interval,
                self.manager.periodic_tasks,
                None,
                None
            )


def main():
    # Load the configuration parameters.
    cfg.CONF.register_opts(OPTS)
    config.register_root_helper(cfg.CONF)
    common_config.init(sys.argv[1:])
    config.setup_logging()

    # Set up RPC
    mgr = taas_agent.TaasAgentRpcCallback(cfg.CONF)
    endpoints = [mgr]
    conn = n_rpc.create_connection()
    conn.create_consumer(topics.TAAS_AGENT, endpoints, fanout=False)
    conn.consume_in_threads()

    svc = TaaSAgentService(
        host=cfg.CONF.host,
        topic=topics.TAAS_PLUGIN,
        manager=mgr
        )
    service.launch(cfg.CONF, svc).wait()

if __name__ == '__main__':
    main()
