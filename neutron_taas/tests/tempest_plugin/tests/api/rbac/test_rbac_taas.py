"""Taas API RBAC tests"""
# Copyright (c) 2018 AT&T Corporation
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

from neutron_taas.tests.tempest_plugin.tests.api import base

from patrole_tempest_plugin import rbac_rule_validation
from patrole_tempest_plugin.tests.api.network import rbac_base

from tempest.common import utils
from tempest.lib import decorators

from tempest.lib.common.utils import test_utils


# pylint: disable=too-many-ancestors
class TaasRbacTest(base.BaseTaaSTest, rbac_base.BaseNetworkRbacTest):
    """TaasRbacTest Class"""

    @classmethod
    @utils.requires_ext(extension='taas', service='network')
    def skip_checks(cls):
        super(TaasRbacTest, cls).skip_checks()

    @classmethod
    def resource_setup(cls):
        super(TaasRbacTest, cls).resource_setup()
        # Create a network, subnet
        cls.network = cls.create_network()
        cls.subnet = cls.create_subnet(cls.network)
        cls.port = cls.create_port(cls.network)
        cls.source_port = cls.create_port(cls.network)

    def _create_taas_service_resource(self):
        """Creates a taas service resource"""

        ts_id = self.tap_services_client.create_tap_service(
            port_id=self.port['id'])
        self.addCleanup(test_utils.call_and_ignore_notfound_exc,
                        self.tap_services_client.delete_tap_service,
                        ts_id['tap_service']['id'])
        return ts_id

    def _create_taas_flow_resource(self, ts_id):
        """Creates a taas flow resource"""

        tf_id = self.tap_flows_client.create_tap_flow(
            tap_service_id=ts_id['tap_service']['id'],
            direction='BOTH', source_port=self.source_port['id'])
        self.addCleanup(test_utils.call_and_ignore_notfound_exc,
                        self.tap_flows_client.delete_tap_flow,
                        tf_id['tap_flow']['id'])
        return tf_id

    @rbac_rule_validation.action(service="neutron_taas",
                                 rules=["get_tap_service",
                                        "delete_tap_service"],
                                 expected_error_codes=[404, 403])
    @decorators.idempotent_id('79c13e03-fb14-4b2a-a0a1-c0061b9ee9f3')
    def test_delete_tap_service(self):
        """Delete tap service api test"""

        ts_id = self._create_taas_service_resource()
        with self.rbac_utils.override_role(self):
            self.tap_services_client.delete_tap_service(
                ts_id['tap_service']['id'])

    @rbac_rule_validation.action(service="neutron_taas",
                                 rules=["create_tap_service"])
    @decorators.idempotent_id('2c06a62d-b03e-48d8-b0f2-d042ec797298')
    def test_create_tap_service(self):
        """create tap service api test"""

        with self.rbac_utils.override_role(self):
            ts_id = self.tap_services_client.create_tap_service(
                port_id=self.port['id'])
        self.addCleanup(test_utils.call_and_ignore_notfound_exc,
                        self.tap_services_client.delete_tap_service,
                        ts_id['tap_service']['id'])

    @rbac_rule_validation.action(service="neutron_taas",
                                 rules=["get_tap_service",
                                        "update_tap_service"],
                                 expected_error_codes=[404, 403])
    @decorators.idempotent_id('c6b42938-1818-40a2-944a-275d30d1ece2')
    def test_update_tap_service(self):
        """Update tap service api test"""

        ts_id = self._create_taas_service_resource()
        ts_id['tap_service']['description'] = "TAP_SERVICE"
        with self.rbac_utils.override_role(self):
            self.tap_services_client.update_tap_service(
                ts_id['tap_service']['id'],
                description='TAP_SERVICE')

    @rbac_rule_validation.action(service="neutron_taas",
                                 rules=["get_tap_service"],
                                 expected_error_codes=[404])
    @decorators.idempotent_id('a0a476f0-dfc4-497e-a8fc-0acce7917c24')
    def test_get_tap_service(self):
        """Show tap service api test"""

        ts_id = self._create_taas_service_resource()
        with self.rbac_utils.override_role(self):
            self.tap_services_client.show_tap_service(
                ts_id['tap_service']['id'])

    @rbac_rule_validation.action(service="neutron_taas",
                                 rules=["get_tap_service"])
    @decorators.idempotent_id('ec69523e-fdc6-4d7d-927e-595e6fb3281a')
    def test_list_tap_services(self):
        """List tap services test"""

        response_object = self._create_taas_service_resource()
        with (self.rbac_utils.override_role_and_validate_list(
                self,
                admin_resource_id=response_object['tap_service']['id']
                )) as ctx:
            ctx.resources = self.tap_services_client.list_tap_services(
                id=response_object['tap_service']['id'])["tap_services"]

    @rbac_rule_validation.action(service="neutron_taas",
                                 rules=["create_tap_flow"])
    @decorators.idempotent_id('51e0cdc8-ba88-4e3e-b056-c291ad1f8be9')
    def test_create_tap_flow(self):
        """Create tap flow api test"""

        ts_id = self._create_taas_service_resource()
        with self.rbac_utils.override_role(self):
            tf_id = self.tap_flows_client.create_tap_flow(
                tap_service_id=ts_id['tap_service']['id'],
                direction='BOTH', source_port=self.source_port['id'])
        self.addCleanup(test_utils.call_and_ignore_notfound_exc,
                        self.tap_flows_client.delete_tap_flow,
                        tf_id['tap_flow']['id'])

    @rbac_rule_validation.action(service="neutron_taas",
                                 rules=["get_tap_flow",
                                        "delete_tap_flow"],
                                 expected_error_codes=[404, 403])
    @decorators.idempotent_id('744b7d22-33c2-4bbc-8c06-3b27c244efc4')
    def test_delete_tap_flow(self):
        """Delete tap flow api test"""

        ts_id = self._create_taas_service_resource()
        tf_id = self._create_taas_flow_resource(ts_id)
        with self.rbac_utils.override_role(self):
            self.tap_flows_client.delete_tap_flow(
                tf_id['tap_flow']['id'])

    @rbac_rule_validation.action(service="neutron_taas",
                                 rules=["get_tap_flow",
                                        "update_tap_flow"],
                                 expected_error_codes=[404, 403])
    @decorators.idempotent_id('10e0ab6c-ff66-48cd-bed4-536f797cc371')
    def test_update_tap_flow(self):
        """Update tap flow api test"""

        ts_id = self._create_taas_service_resource()
        tf_id = self._create_taas_flow_resource(ts_id)
        with self.rbac_utils.override_role(self):
            self.tap_flows_client.update_tap_flow(
                tf_id['tap_flow']['id'],
                description='TAP_FLOW')

    @rbac_rule_validation.action(service="neutron_taas",
                                 rules=["get_tap_flow"],
                                 expected_error_codes=[404])
    @decorators.idempotent_id('fad0b667-2b96-4c57-8654-79efb44cc381')
    def test_get_tap_flow(self):
        """Show tap flow api test"""

        ts_id = self._create_taas_service_resource()
        tf_id = self._create_taas_flow_resource(ts_id)
        with self.rbac_utils.override_role(self):
            self.tap_flows_client.show_tap_flow(
                tf_id['tap_flow']['id'])

    @rbac_rule_validation.action(service="neutron_taas",
                                 rules=["get_tap_flow"])
    @decorators.idempotent_id('c07cf0f9-57fa-41b4-a2fc-396a6087fdce')
    def test_list_tap_flows(self):
        """List tap flows api test"""

        ts_object = self._create_taas_service_resource()
        tf_object = self.tap_flows_client.create_tap_flow(
            tap_service_id=ts_object['tap_service']['id'],
            direction='BOTH', source_port=self.source_port['id'])
        with (self.rbac_utils.override_role_and_validate_list(
                self, admin_resource_id=tf_object['tap_flow']['id']
                )) as ctx:
            ctx.resources = self.tap_flows_client.list_tap_flows(
                id=tf_object['tap_flow']['id'])["tap_flows"]
