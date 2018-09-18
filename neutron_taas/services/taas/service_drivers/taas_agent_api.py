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

from neutron_lib import constants
from neutron_lib import rpc as n_rpc
from neutron_taas.services.taas.service_drivers import (service_driver_context
                                                        as sd_context)
from oslo_log import log as logging
from oslo_utils import excutils
import oslo_messaging as messaging

LOG = logging.getLogger(__name__)


class TaasCallbacks(object):
    """Currently there are no callbacks to the Taas Plugin."""

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
                continue;

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
