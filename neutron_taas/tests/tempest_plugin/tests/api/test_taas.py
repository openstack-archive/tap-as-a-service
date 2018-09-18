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
    def test_create_tap_service_and_flow_vlan_filter(self):
        """create tap service with vlan_filter

        Test create tap service with additional vlan_filter argument.
        """
        tap_service = self.create_tap_service(port_id=self.port['id'])
        self.create_tap_flow(tap_service_id=tap_service['id'],
                             direction='BOTH', source_port=self.port['id'],
                             vlan_filter='189,279,999-1008')

    @decorators.idempotent_id('d7a2115d-16b4-41cf-95a6-dcebc3682b24')
    def test_delete_tap_service_after_delete_port(self):
        """delete tap service

        Test delete tap service after deletion of port.
        """
        tap_service = self.create_tap_service(port_id=self.port['id'])
        # delete port
        self.ports_client.delete_port(self.port['id'])
        self.tap_services_client.delete_tap_service(tap_service['id'])
