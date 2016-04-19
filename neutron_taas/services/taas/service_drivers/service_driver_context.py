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
