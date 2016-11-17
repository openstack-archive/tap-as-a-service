# Copyright (c) 2016 Huawei Technologies India Pvt.Limited.
# All Rights Reserved.
#
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

import mock

from osc_lib.tests import utils as tests_utils

from neutron_taas.osc import common
from neutron_taas.osc.taas import tap_service
from neutron_taas.tests.unit.osc import fakes


def _get_id(client, id_or_name, resource):
    return id_or_name


class TestListTapServiceGroup(fakes.TestNeutronClientOSCV2):
    _tapservice = fakes.FakeTapServiceGroup.create_tap_services(count=1)
    columns = ('ID', 'Name', 'Tap Service')
    data = []
    _tap_service = _tapservice['tap_services'][0]
    data.append((
        _tap_service['id'],
        _tap_service['name'],
        _tap_service['port_id'],))
    _tap_service1 = {'tap_services': _tap_service}
    _tap_service_id = _tap_service['id']

    def setUp(self):
        super(TestListTapServiceGroup, self).setUp()

        self.neutronclient.list_ext = mock.Mock(
            return_value=self._tap_service1
        )
        # Get the command object to test
        self.cmd = tap_service.ListTapServiceGroup(self.app, self.namespace)

    def test_tap_service_list(self):
        client = self.app.client_manager.neutronclient
        mock_tap_service_list = client.list_ext
        parsed_args = self.check_parser(self.cmd, [], [])
        columns = self.cmd.take_action(parsed_args)
        data = mock_tap_service_list.assert_called_once_with(
            collection='tap_services', path='/taas/tap_services',
            retrieve_all=True)
        self.assertEqual(self.columns, columns[0])
        self.assertIsNone(data)


class TestCreateTapServiceGroup(fakes.TestNeutronClientOSCV2):
    # The new port_pair created
    _tap_service = fakes.FakeTapServiceGroup.create_tap_service()

    columns = (
        'id',
        'name',
        'description',
        'port_id',
    )

    def get_data(self):
        return (
            self._tap_service['id'],
            self._tap_service['name'],
            self._tap_service['description'],
            self._tap_service['port_id'],
        )

    def setUp(self):
        super(TestCreateTapServiceGroup, self).setUp()
        mock.patch('neutron_taas.osc.common.find_taas_resource',
                   new=_get_id).start()
        common.create_taas_resource = mock.Mock(
            return_value={'tap_services': self._tap_service})
        self.data = self.get_data()

        # Get the command object to test
        self.cmd = tap_service.CreateTapServiceGroup(self.app,
                                                     self.namespace)

    def test_create_tap_service(self):
        arglist = []
        verifylist = []

        self.assertRaises(tests_utils.ParserException, self.check_parser,
                          self.cmd, arglist, verifylist)


class TestDeleteTapServiceGroup(fakes.TestNeutronClientOSCV2):

    def setUp(self):
        super(TestDeleteTapServiceGroup, self).setUp()
        _tap_service = fakes.FakeTapServiceGroup.create_tap_services()
        self._tap_service = _tap_service['tap_services'][0]
        _tap_service_id = self._tap_service['id']
        common.delete_taas_resource = mock.Mock(return_value=None)
        common.find_taas_resource = mock.Mock(return_value=_tap_service_id)
        self.cmd = tap_service.DeleteTapServiceGroup(self.app,
                                                     self.namespace)

    def test_delete_tap_service(self):
        client = self.app.client_manager.neutronclient
        tf_id = self._tap_service['id']
        mock_tap_service_delete = common.delete_taas_resource
        arglist = [
            self._tap_service['id'],
        ]
        verifylist = [
            ('tap_service', self._tap_service['id']),
        ]
        parsed_args = self.check_parser(self.cmd, arglist, verifylist)
        result = self.cmd.take_action(parsed_args)
        mock_tap_service_delete.assert_called_once_with(self.cmd, client,
                                                        'tap_service',
                                                        tf_id)
        self.assertIsNone(result)


class TestShowTapServiceGroup(fakes.TestNeutronClientOSCV2):

    _tf = fakes.FakeTapServiceGroup.create_tap_service()
    data = (
        _tf['description'],
        _tf['group_id'],
        _tf['id'],
        _tf['name'],
        _tf['port_id'],
        _tf['tenant_id'])
    _tap_service = {'tap_service': _tf}
    _tap_service_id = _tf['id']
    columns = (
        'description',
        'group_id',
        'id',
        'name',
        'port_id',
        'tenant_id')

    def setUp(self):
        super(TestShowTapServiceGroup, self).setUp()
        common.find_taas_resource = mock.Mock(
            return_value=self._tap_service_id)
        common.show_taas_resource = mock.Mock(
            return_value=self._tap_service
        )
        # Get the command object to test
        self.cmd = tap_service.ShowTapServiceGroup(self.app, self.namespace)

    def test_tap_service_show(self):
        client = self.app.client_manager.neutronclient
        mock_tap_service_show = common.show_taas_resource
        arglist = [
            self._tap_service_id,
        ]
        verifylist = [
            ('tap_service', self._tap_service_id),
        ]
        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        data = self.cmd.take_action(parsed_args)
        tf_id = self._tap_service_id
        mock_tap_service_show.assert_called_once_with(self.cmd, client,
                                                      'tap_service',
                                                      tf_id)
        self.assertEqual(self.columns, data[0])
        self.assertEqual(self.data, data[1])


class TestUpdateTapServiceGroup(fakes.TestNeutronClientOSCV2):
    _tap_service = fakes.FakeTapServiceGroup.create_tap_service()
    _tap_service_name = _tap_service['name']
    _tap_service_id = _tap_service['id']
    port_id = _tap_service_id

    def setUp(self):
        super(TestUpdateTapServiceGroup, self).setUp()
        common.update_taas_resource = mock.Mock(return_value=None)
        common.find_taas_resource = mock.Mock(
            return_value=self._tap_service_id)

        self.cmd = tap_service.UpdateTapServiceGroup(self.app,
                                                     self.namespace)

    def test_update_tap_service(self):
        client = self.app.client_manager.neutronclient
        mock_tap_service_update = common.update_taas_resource
        arglist = [
            self._tap_service_name,
            '--name', 'name_updated',
            '--description', 'desc_updated',
            '--port', self.port_id,
        ]
        verifylist = [
            ('tap_service', self._tap_service_name),
            ('name', 'name_updated'),
            ('description', 'desc_updated'),
            ('port_id', [self.port_id]),
        ]

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)
        result = self.cmd.take_action(parsed_args)

        attrs = {
            'name': 'name_updated',
            'description': 'desc_updated',
            'port_id': [self.port_id]}
        tf_id = self._tap_service_id
        mock_tap_service_update.assert_called_once_with(self.cmd, client,
                                                        'tap_service',
                                                        attrs, tf_id)
        self.assertIsNone(result)
