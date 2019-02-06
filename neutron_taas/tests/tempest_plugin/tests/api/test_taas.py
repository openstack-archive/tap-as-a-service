# Copyright (c) 2018 AT&T Intellectual Property. All other rights reserved.
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

from tempest.common import utils
from tempest import config
from tempest.lib import decorators
from tempest.lib import exceptions as lib_exc

from neutron_taas.tests.tempest_plugin.tests.api import base

CONF = config.CONF


class TaaSExtensionTestJSON(base.BaseTaaSTest):

    @classmethod
    @utils.requires_ext(extension='taas', service='network')
    def skip_checks(cls):
        super(TaaSExtensionTestJSON, cls).skip_checks()

    @classmethod
    def resource_setup(cls):
        super(TaaSExtensionTestJSON, cls).resource_setup()
        cls.network = cls.create_network()
        cls.ts_port = cls.create_port(cls.network)
        cls.tf_port = cls.create_port(cls.network)
        cls.tf2_port = cls.create_port(cls.network)

    @decorators.idempotent_id('b993c14e-797a-4c91-b4da-8cb1a450aa2f')
    def test_create_tap_service_and_flow(self):
        """create tap service adn tap flow

        Test create tap service and flow.
        """
        tap_service = self.create_tap_service(port_id=self.ts_port['id'])
        self.create_tap_flow(tap_service_id=tap_service['id'],
                             direction='BOTH', source_port=self.tf_port['id'])

    @decorators.idempotent_id('d7a2115d-16b4-41cf-95a6-dcebc3682b24')
    def test_delete_tap_resources_after_ts_port_delete(self):
        """delete tap resources after ts port delete

        Test delete tap resources after deletion of ts port.
        """
        tap_service = self.create_tap_service(port_id=self.ts_port['id'])
        tap_flow = self.create_tap_flow(tap_service_id=tap_service['id'],
                                        direction='BOTH',
                                        source_port=self.tf2_port['id'])
        # delete ts_port; it shall also delete the associated tap-service and
        # subsequently the tap-flow as well
        self.ports_client.delete_port(self.ts_port['id'])
        # Attempt tap-service deletion; it should throw not found exception.
        self.assertRaises(lib_exc.NotFound,
                          self.tap_services_client.delete_tap_service,
                          tap_service['id'])
        # Attempt tap-flow deletion; it should throw not found exception.
        self.assertRaises(lib_exc.NotFound,
                          self.tap_flows_client.delete_tap_flow,
                          tap_flow['id'])

    @decorators.idempotent_id('9ba4edfd-4002-4c44-b02b-6c4f71b40a92')
    def test_delete_tap_resources_after_tf_port_delete(self):
        """delete tap resources after tf port delete

        Test delete tap service after deletion of tf port.
        """
        tap_service = self.create_tap_service(port_id=self.ts_port['id'])
        tap_flow = self.create_tap_flow(tap_service_id=tap_service['id'],
                                        direction='BOTH',
                                        source_port=self.tf_port['id'])
        # delete tf port; it shall also delete the associated tap-flow
        self.ports_client.delete_port(self.tf_port['id'])
        # Attempt tap-flow deletion; it should throw not found exception.
        self.assertRaises(lib_exc.NotFound,
                          self.tap_flows_client.delete_tap_flow,
                          tap_flow['id'])
        # delete tap service; it shall go fine
        self.tap_services_client.delete_tap_service(tap_service['id'])

    @decorators.idempotent_id('687089b8-b045-496d-86bf-030b380039d1')
    def test_create_and_update_tap_service(self):
        """create and update tap service

        Test update tap service - update description.
        """
        tap_service = self.create_tap_service(port_id=self.ts_port['id'])

        # Update description of the tap service
        self.update_tap_service(
            tap_service['id'],
            description='Tap Service Description Updated')

    @decorators.idempotent_id('bb4d5482-37fc-46b5-85a5-5867e9adbfae')
    def test_create_and_update_tap_flow(self):
        """create and update tap flow

        Test update tap flow - update description.
        """
        tap_service = self.create_tap_service(port_id=self.ts_port['id'])
        tap_flow = self.create_tap_flow(
            tap_service_id=tap_service['id'],
            direction='BOTH', source_port=self.tf_port['id'])
        # Update description of the tap flow
        self.update_tap_flow(
            tap_flow['id'],
            description='Tap Flow Description Updated')
