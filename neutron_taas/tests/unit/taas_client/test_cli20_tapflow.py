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
import sys

from neutron_taas.taas_client import tapflow
from neutronclient import shell
from neutronclient.tests.unit import test_cli20


class CLITestV20TapFlowJSON(test_cli20.CLITestV20Base):
    resource = 'tap_flow'
    resource_plural = '%ss' % resource

    def setUp(self):
        self._mock_extension_loading()
        super(CLITestV20TapFlowJSON, self).setUp()
        self.resources = self.resource_plural
        self.register_non_admin_status_resource(self.resource)

    def _create_patch(self, name, func=None):
        patcher = mock.patch(name)
        thing = patcher.start()
        return thing

    def _mock_extension_loading(self):
        ext_pkg = 'neutronclient.common.extension'
        contrib = self._create_patch(ext_pkg + '._discover_via_entry_points')
        contrib.return_value = [("_tap_flow", tapflow)]
        return contrib

    def test_ext_cmd_loaded(self):
        neutron_shell = shell.NeutronShell('2.0')
        extension_cmd = {'tap-flow-create': tapflow.CreateTapFlow,
                         'tap-flow-delete': tapflow.DeleteTapFlow,
                         'tap-flow-show': tapflow.ShowTapFlow,
                         'tap-flow-list': tapflow.ListTapFlow}
        for cmd_name, cmd_class in extension_cmd.items():
            found = neutron_shell.command_manager.find_command([cmd_name])
            self.assertEqual(cmd_class, found[0])

    def _test_create_tap_flow(self, port_id="random_port",
                              service_id="random_service",
                              direction="BOTH", arg_attr=None,
                              name_attr=None, val_attr=None,
                              name=''):
        # Common definition for creating Tap flow
        arg_attr = arg_attr or []
        name_attr = name_attr or []
        val_attr = val_attr or []
        cmd = tapflow.CreateTapFlow(test_cli20.MyApp(sys.stdout), None)
        tenant_id = 'my-tenant'
        my_id = 'my-id'
        args = ['--tenant-id', tenant_id,
                '--port', port_id,
                '--tap-service', service_id,
                '--direction', direction] + arg_attr
        pos_names = ['source_port', 'tap_service_id', 'direction'] + name_attr
        pos_values = [port_id, service_id, direction] + val_attr
        self._test_create_resource(self.resource, cmd, name, my_id, args,
                                   pos_names, pos_values,
                                   tenant_id=tenant_id)

    def test_create_tap_flow_mandatory_params(self):
        self._test_create_tap_flow()

    def test_create_tap_flow_all_params(self):
        name = 'dummyTapFlow'
        description = 'Create a dummy tap flow'
        self._test_create_tap_flow(name=name,
                                   arg_attr=[
                                       '--name', name,
                                       '--description', description],
                                   name_attr=['name', 'description'],
                                   val_attr=[name, description])

    def test_delete_tap_flow(self):
        # Delete tap_flow: myid.
        cmd = tapflow.DeleteTapFlow(test_cli20.MyApp(sys.stdout), None)
        myid = 'myid'
        args = [myid]
        self._test_delete_resource(self.resource, cmd, myid, args)

    def test_update_tap_flow(self):
        # Update tap_flow: myid --name myname.
        cmd = tapflow.UpdateTapFlow(test_cli20.MyApp(sys.stdout), None)
        self._test_update_resource(self.resource, cmd, 'myid',
                                   ['myid', '--name', 'myname'],
                                   {'name': 'myname'})

    def test_list_tap_flows(self):
        # List tap_flows.
        cmd = tapflow.ListTapFlow(test_cli20.MyApp(sys.stdout), None)
        self._test_list_resources(self.resources, cmd, True)

    def test_show_tap_flow(self):
        # Show tap_flow: --fields id --fields name myid.
        cmd = tapflow.ShowTapFlow(test_cli20.MyApp(sys.stdout), None)
        args = ['--fields', 'id', '--fields', 'name', self.test_id]
        self._test_show_resource(self.resource, cmd, self.test_id,
                                 args, ['id', 'name'])
