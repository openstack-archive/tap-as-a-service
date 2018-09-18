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
        cls.port = cls.create_port(cls.network)

    @decorators.idempotent_id('b993c14e-797a-4c91-b4da-8cb1a450aa2f')
    def test_create_tap_service_and_flow(self):
        """create tap service

        Test create tap service without additional vlan_filter argument.
        """
        tap_service = self.create_tap_service(port_id=self.port['id'])
        self.create_tap_flow(tap_service_id=tap_service['id'],
                             direction='BOTH', source_port=self.port['id'])

    @decorators.idempotent_id('897a0aaf-1b55-4ea8-9d9f-1bc0fd09cb60')
    @utils.requires_ext(extension='taas-vlan-filter', service='network')
    def test_create_tap_service_and_flow_vlan_filter(self):
        """create tap service with vlan_filter

        Test create tap service with additional vlan_filter argument.
        """
        tap_service = self.create_tap_service(port_id=self.port['id'])
        self.create_tap_flow(tap_service_id=tap_service['id'],
                             direction='BOTH', source_port=self.port['id'],
                             vlan_filter='189,279,999-1008')

    @decorators.idempotent_id('d7a2115d-16b4-41cf-95a6-dcebc3682b24')
    def test_delete_tap_service_and_flow_after_delete_port(self):
        """delete tap service

        Test delete tap service after deletion of port.
        """
        tap_service = self.create_tap_service(port_id=self.port['id'])
        tap_flow = self.create_tap_flow(tap_service_id=tap_service['id'],
                                        direction='BOTH',
                                        source_port=self.port['id'])
        # delete port; it shall also delete the associated tap-service
        self.ports_client.delete_port(self.port['id'])
        # Attempt tap-service deletion; it should throw not found exception.
        self.assertRaises(lib_exc.NotFound,
                          self.tap_services_client.delete_tap_service,
                          tap_service['id'])
        # Attempt tap-flow deletion; it should throw not found exception.
        self.assertRaises(lib_exc.NotFound,
                          self.tap_flows_client.delete_tap_flow,
                          tap_flow['id'])

    @decorators.idempotent_id('687089b8-b045-496d-86bf-030b380039d1')
    def test_create_and_update_tap_service(self):
        """create and update tap service

        Test update tap service - update description.
        """
        tap_service = self.create_tap_service(port_id=self.port['id'])

        # Update description of the tap service
        self.update_tap_service(
            tap_service['id'],
            description='Tap Service Description Updated')

    @decorators.idempotent_id('bb4d5482-37fc-46b5-85a5-5867e9adbfae')
    def test_create_and_update_tap_flow(self):
        """create and update tap flow

        Test update tap flow - update description.
        """
        tap_service = self.create_tap_service(port_id=self.port['id'])
        tap_flow = self.create_tap_flow(
            tap_service_id=tap_service['id'],
            direction='BOTH', source_port=self.port['id'])
        # Update description of the tap flow
        self.update_tap_flow(
            tap_flow['id'],
            description='Tap Flow Description Updated')
