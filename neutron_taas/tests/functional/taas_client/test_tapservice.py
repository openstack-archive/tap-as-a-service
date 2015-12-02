# Copyright 2015 NEC Corporation Limited
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.
from neutronclient.tests.functional import base

# ToDo(reedip) : Add more Functional Test cases for other
# TAP  related tests


class TapServiceCreateNeutronClientCLITest(base.ClientTestBase):

    def test_create_tap_service_create(self):
        self.neutron('net-create Net')
        self.addCleanup(self.neutron, 'net-delete Net')
        self.neutron('port-create Net', params='--name Port')
        self.addCleanup(self.neutron, 'port-delete Port')
        parameters = ('--name TapService --port-id '
                      'Port --network-id Net')
        self.neutron('tap-service-create ',
                     params='--name TapService --port-id Port --network-id Net'
                     )
        self.addCleanup(self.neutron, 'tap-service-delete TapService')
        firewall_rule_list = self.parser.listing(self.neutron(
            'tap-service-list'))
        found = False
        for row in firewall_rule_list:
            if row.get('name') == 'TapService':
                found = True
                break
        if not found:
            self.fail('Created TapService not found in list')
