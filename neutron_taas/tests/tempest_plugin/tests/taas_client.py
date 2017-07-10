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

from tempest import config
from tempest.lib.common.utils import data_utils
from tempest.lib.common.utils import test_utils

from neutron_taas.tests.tempest_plugin.services import client

CONF = config.CONF


class TaaSClientMixin(object):

    @classmethod
    def resource_setup(cls):
        super(TaaSClientMixin, cls).resource_setup()
        os_primary = cls.os_primary
        cls.tap_services_client = client.TapServicesClient(
            os_primary.auth_provider,
            CONF.network.catalog_type,
            CONF.network.region or CONF.identity.region,
            endpoint_type=CONF.network.endpoint_type,
            build_interval=CONF.network.build_interval,
            build_timeout=CONF.network.build_timeout,
            **os_primary.default_params)
        cls.tap_flows_client = client.TapFlowsClient(
            os_primary.auth_provider,
            CONF.network.catalog_type,
            CONF.network.region or CONF.identity.region,
            endpoint_type=CONF.network.endpoint_type,
            build_interval=CONF.network.build_interval,
            build_timeout=CONF.network.build_timeout,
            **os_primary.default_params)

    def create_tap_service(self, **kwargs):
        body = self.tap_services_client.create_tap_service(
            name=data_utils.rand_name("tap_service"),
            **kwargs)
        tap_service = body['tap_service']
        self.addCleanup(test_utils.call_and_ignore_notfound_exc,
                        self.tap_services_client.delete_tap_service,
                        tap_service['id'])
        return tap_service

    def create_tap_flow(self, **kwargs):
        body = self.tap_flows_client.create_tap_flow(
            name=data_utils.rand_name("tap_service"),
            **kwargs)
        tap_flow = body['tap_flow']
        self.addCleanup(test_utils.call_and_ignore_notfound_exc,
                        self.tap_flows_client.delete_tap_flow,
                        tap_flow['id'])
        return tap_flow
