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

from neutron_lib import rpc as n_rpc
from oslo_log import log as logging
import oslo_messaging as messaging

LOG = logging.getLogger(__name__)


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
