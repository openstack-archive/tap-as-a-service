# Copyright (c) 2015 Midokura SARL
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from tempest.lib.services.network import base


class TapServicesClient(base.BaseNetworkClient):

    def create_tap_service(self, **kwargs):
        uri = '/taas/tap_services'
        post_data = {'tap_service': kwargs}
        return self.create_resource(uri, post_data)

    def update_tap_service(self, tap_service_id, **kwargs):
        uri = '/taas/tap_services'
        post_data = {'tap_service': kwargs}
        return self.update_resource(uri, post_data)

    def show_tap_service(self, tap_service_id, **fields):
        uri = '/taas/tap_services/%s' % tap_service_id
        return self.show_resource(uri, **fields)

    def delete_tap_service(self, tap_service_id):
        uri = '/taas/tap_services/%s' % tap_service_id
        return self.delete_resource(uri)

    def list_tap_services(self, **filters):
        uri = '/taas/tap_services'
        return self.list_resources(uri, **filters)


class TapFlowsClient(base.BaseNetworkClient):

    def create_tap_flow(self, **kwargs):
        uri = '/taas/tap_flows'
        post_data = {'tap_flow': kwargs}
        return self.create_resource(uri, post_data)

    def update_tap_flow(self, tap_flow_id, **kwargs):
        uri = '/taas/tap_flows'
        post_data = {'tap_flow': kwargs}
        return self.update_resource(uri, post_data)

    def show_tap_flow(self, tap_flow_id, **fields):
        uri = '/taas/tap_flows/%s' % tap_flow_id
        return self.show_resource(uri, **fields)

    def delete_tap_flow(self, tap_flow_id):
        uri = '/taas/tap_flows/%s' % tap_flow_id
        return self.delete_resource(uri)

    def list_tap_flows(self, **filters):
        uri = '/taas/tap_flows'
        return self.list_resources(uri, **filters)
