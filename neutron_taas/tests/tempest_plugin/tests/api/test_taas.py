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

import testtools

from tempest_lib import exceptions as lib_exc

from tempest import config
from tempest import test

from neutron_taas.tests.tempest_plugin.tests.api import base

CONF = config.CONF


class TaaSExtensionTestJSON(base.BaseTaaSTest):

    @classmethod
    def resource_setup(cls):
        super(TaaSExtensionTestJSON, cls).resource_setup()
        if not test.is_extension_enabled('taas', 'network'):
            msg = "TaaS Extension not enabled."
            raise cls.skipException(msg)

    @test.idempotent_id('b993c14e-797a-4c91-b4da-8cb1a450aa2f')
    def test_create_tap_service_and_flow(self):
        network = self.create_network()
        port = self.create_port(network)
        tap_service = self.create_tap_service(network_id=network['id'],
                                              port_id=port['id'])
        self.create_tap_flow(tap_service_id=tap_service['id'],
                             direction='BOTH', source_port=port['id'])

    @test.attr(type=['negative'])
    @test.idempotent_id('2d5024f5-bc80-4a31-a4a5-5bf5b14a8f3e')
    def test_create_tap_service_with_wrong_network(self):
        with testtools.ExpectedException(lib_exc.BadRequest):
            self.create_tap_service(network_id='nonexistent')
