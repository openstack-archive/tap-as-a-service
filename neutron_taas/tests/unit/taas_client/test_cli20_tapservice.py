# Copyright 2015 NEC Corporation
# All Rights Reserved
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
#
import mock

from neutron_taas.taas_client import tapservice
from neutronclient import shell
from neutronclient.tests.unit import test_cli20


class CLITestV20TapServiceJSON(test_cli20.CLITestV20Base,
                               tapservice.TapService):

    def setUp(self):
        # need to mock before super because extensions loaded on instantiation
        self._mock_extension_loading()
        super(CLITestV20TapServiceJSON, self).setUp()

    def _create_patch(self, name, func=None):
        patcher = mock.patch(name)
        thing = patcher.start()
        self.addCleanup(patcher.stop)
        return thing

    def _mock_extension_loading(self):
        ext_pkg = 'neutronclient.common.extension'
        contrib = self._create_patch(ext_pkg + '._discover_via_entry_points')
        contrib.return_value = [("_tap_service", tapservice)]
        return contrib

    def test_ext_cmd_loaded(self):
        shell.NeutronShell('2.0')
        extension_cmd = {'tap-service-create': tapservice.CreateTapService,
                         'tap-service-delete': tapservice.DeleteTapService,
                         'tap-service-show': tapservice.ShowTapService,
                         'tap-service-list': tapservice.ListTapService}
        self.assertDictContainsSubset(extension_cmd, shell.COMMANDS['2.0'])
'''
    import sys

    from neutronclient.common import extension

    def test_create_tap_service_mandatory_params(self,port_id="random_port",
                                                 network_id="random_net"):
        cmd = tapservice.CreateTapService(test_cli20.MyApp(sys.stdout), None)
        name = ''
        tenant_id = 'my-tenant'
        my_id = 'my-id'
        args = ['--tenant-id', tenant_id,
                '--port-id', port_id,
                '--network-id', network_id ]
        position_names = []
        position_values = [port_id, network_id ]
        self._test_create_resource(self.resource, cmd, name, my_id, args,
                                   position_names, position_values,
                                   tenant_id=tenant_id)


'''
