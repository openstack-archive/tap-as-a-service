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
    def resource_setup(cls):
        super(TaaSExtensionTestJSON, cls).resource_setup()
        if not utils.is_extension_enabled('taas', 'network'):
            msg = "TaaS Extension not enabled."
            raise cls.skipException(msg)

    @decorators.idempotent_id('b993c14e-797a-4c91-b4da-8cb1a450aa2f')
    def test_create_tap_service_and_flow(self):
        network = self.create_network()
        port = self.create_port(network)
        tap_service = self.create_tap_service(port_id=port['id'])
        self.create_tap_flow(tap_service_id=tap_service['id'],
                             direction='BOTH', source_port=port['id'])

    @decorators.idempotent_id('d7a2115d-16b4-41cf-95a6-dcebc3682b24')
    def test_delete_tap_service_after_delete_port(self):
        network = self.create_network()
        port = self.create_port(network)
        tap_service = self.create_tap_service(port_id=port['id'])
        # delete port; it shall also delete the associated tap-service
        self.ports_client.delete_port(port['id'])
        # Attempt tap-service deletion; it should throw not found exception.
        self.assertRaises(lib_exc.NotFound,
                          self.tap_services_client.delete_tap_service,
                          tap_service['id'])

    @decorators.idempotent_id('5568590a-0d34-415d-83f8-517a7f64cd12')
    def test_delete_tap_flow_after_delete_port(self):
        network = self.create_network()
        port = self.create_port(network)
        tap_service = self.create_tap_service(port_id=port['id'])
        tap_flow = self.create_tap_flow(tap_service_id=tap_service['id'],
                                        direction='BOTH',
                                        source_port=port['id'])
        # delete port; it shall also delete the associated tap-service
        self.ports_client.delete_port(port['id'])
        # Attempt tap-flow deletion; it should throw not found exception.
        self.assertRaises(lib_exc.NotFound,
                          self.tap_flows_client.delete_tap_flow,
                          tap_flow['id'])

    @decorators.idempotent_id('687089b8-b045-496d-86bf-030b380039d1')
    def test_update_tap_service(self):
        network = self.create_network()
        port = self.create_port(network)
        tap_service = self.create_tap_service(port_id=port['id'])
        # Update description of the tap service
        self.update_tap_service(
            tap_service['id'],
            description='Tap Service Description Updated')

    @decorators.idempotent_id('bb4d5482-37fc-46b5-85a5-5867e9adbfae')
    def test_update_tap_flow(self):
        network = self.create_network()
        port = self.create_port(network)
        tap_service = self.create_tap_service(port_id=port['id'])
        tap_flow = self.create_tap_flow(
            tap_service_id=tap_service['id'],
            direction='BOTH', source_port=port['id'])
        # Update description of the tap flow
        self.update_tap_flow(
            tap_flow['id'],
            description='Tap Flow Description Updated')
