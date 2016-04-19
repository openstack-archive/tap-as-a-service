# Copyright (C) 2016 Midokura SARL.
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

from neutron_taas.extensions import taas

from oslo_log import log

LOG = log.getLogger(__name__)


class ServiceDriverContext(object):
    """ServiceDriverContext context base class"""
    def __init__(self, service_plugin, plugin_context):
        self._plugin = service_plugin
        self._plugin_context = plugin_context


class TapServiceContext(ServiceDriverContext):

    def __init__(self, service_plugin, plugin_context, tap_service):
        super(TapServiceContext, self).__init__(service_plugin, plugin_context)
        self._tap_service = tap_service
        self._tap_id_association = None
        self._setup_tap_id_association(tap_service['id'])

    def _setup_tap_id_association(self, tap_service_id):
        try:
            self._tap_id_association = self._plugin.get_tap_id_association(
                self._plugin_context, tap_service_id)
        except taas.TapServiceNotFound:
            LOG.debug("Not found tap_ip_association for tap_service: %s",
                      tap_service_id)

    @property
    def tap_service(self):
        return self._tap_service

    @property
    def tap_id_association(self):
        return self._tap_id_association

    @tap_id_association.setter
    def tap_id_association(self, tap_id_association):
        """Set tap_id_association in context"""
        self._tap_id_association = tap_id_association


class TapFlowContext(ServiceDriverContext):

    def __init__(self, service_plugin, plugin_context, tap_flow):
        super(TapFlowContext, self).__init__(service_plugin, plugin_context)
        self._tap_flow = tap_flow

    @property
    def tap_flow(self):
        return self._tap_flow
