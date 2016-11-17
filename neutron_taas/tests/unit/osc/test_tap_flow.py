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
from neutron_taas.osc.taas import tapflow
from neutron_taas.tests.unit.osc import fakes


def _get_id(client, id_or_name, resource):
    return id_or_name


class TestListTapFlow(fakes.TestNeutronClientOSCV2):
    _tapflow = fakes.FakeTapFlow.create_tap_flows(count=1)
    columns = ('ID', 'NAME', 'SOURCE PORT', 'TAP SERVICE', 'STATUS')
    data = []
    _tap_flow = _tapflow['tap_flows'][0]
    data.append((
        _tap_flow['id'],
        _tap_flow['name'],
        _tap_flow['source_port'],
        _tap_flow['tap_service_id']))
    _tap_flow1 = {'tap_flows': _tap_flow}
    _tap_flow_id = _tap_flow['id']

    def setUp(self):
        super(TestListTapFlow, self).setUp()

        self.neutronclient.list_ext = mock.Mock(
            return_value=self._tap_flow1
        )
        # Get the command object to test
        self.cmd = tapflow.ListTapFlow(self.app, self.namespace)

    def test_tap_flow_list(self):
        client = self.app.client_manager.neutronclient
        mock_tap_flow_list = client.list_ext
        parsed_args = self.check_parser(self.cmd, [], [])
        columns = self.cmd.take_action(parsed_args)
        data = mock_tap_flow_list.assert_called_once_with(
            collection='tap_flows', path='/taas/tap_flows',
            retrieve_all=True)
        self.assertEqual(self.columns, columns[0])
        self.assertIsNone(data)


class TestCreateTapFlow(fakes.TestNeutronClientOSCV2):
    # The new tap_flow created
    _tap_flow = fakes.FakeTapFlow.create_tap_flow()

    columns = (
        'id',
        'name',
        'description',
        'source_port',
        'tap_service_id',
    )

    def get_data(self):
        return (
            self._tap_flow['id'],
            self._tap_flow['name'],
            self._tap_flow['description'],
            self._tap_flow['source_port'],
            self._tap_flow['tap_service_id'],
        )

    def setUp(self):
        super(TestCreateTapFlow, self).setUp()
        mock.patch('neutron_taas.osc.common.find_taas_resource',
                   new=_get_id).start()
        common.create_taas_resource = mock.Mock(
            return_value={'tap_flows': self._tap_flow})
        self.data = self.get_data()

        # Get the command object to test
        self.cmd = tapflow.CreateTapFlow(self.app,
                                         self.namespace)

    def test_create_tap_flow_exception(self):
        arglist = []
        verifylist = []

        self.assertRaises(tests_utils.ParserException, self.check_parser,
                          self.cmd, arglist, verifylist)


class TestDeleteTapFlow(fakes.TestNeutronClientOSCV2):

    def setUp(self):
        super(TestDeleteTapFlow, self).setUp()
        _tap_flow = fakes.FakeTapFlow.create_tap_flows()
        self._tap_flow = _tap_flow['tap_flows'][0]
        _tap_flow_id = self._tap_flow['id']
        common.delete_taas_resource = mock.Mock(return_value=None)
        common.find_taas_resource = mock.Mock(return_value=_tap_flow_id)
        self.cmd = tapflow.DeleteTapFlow(self.app,
                                         self.namespace)

    def test_delete_tap_flow(self):
        client = self.app.client_manager.neutronclient
        tf_id = self._tap_flow['id']
        mock_tap_flow_delete = common.delete_taas_resource
        arglist = [
            self._tap_flow['id'],
        ]
        verifylist = [
            ('tap_flow', [self._tap_flow['id']]),
        ]
        parsed_args = self.check_parser(self.cmd, arglist, verifylist)
        result = self.cmd.take_action(parsed_args)
        mock_tap_flow_delete.assert_called_once_with(self.cmd, client,
                                                     'tap_flow',
                                                     tf_id)
        self.assertIsNone(result)


class TestShowTapFlow(fakes.TestNeutronClientOSCV2):

    _tf = fakes.FakeTapFlow.create_tap_flow()
    data = (
        _tf['description'],
        _tf['id'],
        _tf['name'],
        _tf['source_port'],
        _tf['status'],
        _tf['tap_service_id'],
        _tf['tenant_id'])
    _tap_flow = {'tap_flow': _tf}
    _tap_flow_id = _tf['id']
    columns = (
        'description',
        'id',
        'name',
        'source_port',
        'status',
        'tap_service_id',
        'tenant_id')

    def setUp(self):
        super(TestShowTapFlow, self).setUp()
        common.find_taas_resource = mock.Mock(
            return_value=self._tap_flow_id)
        common.show_taas_resource = mock.Mock(
            return_value=self._tap_flow
        )
        # Get the command object to test
        self.cmd = tapflow.ShowTapFlow(self.app, self.namespace)

    def test_tap_flow_show(self):
        client = self.app.client_manager.neutronclient
        mock_tap_flow_show = common.show_taas_resource
        arglist = [
            self._tap_flow_id,
        ]
        verifylist = [
            ('tap_flow', self._tap_flow_id),
        ]
        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        data = self.cmd.take_action(parsed_args)
        tf_id = self._tap_flow_id
        mock_tap_flow_show.assert_called_once_with(self.cmd, client,
                                                   'tap_flow',
                                                   tf_id)
        self.assertEqual(self.columns, data[0])
        self.assertEqual(self.data, data[1])


class TestUpdateTapFlow(fakes.TestNeutronClientOSCV2):
    _tap_flow = fakes.FakeTapFlow.create_tap_flow()
    _tap_flow_name = _tap_flow['name']
    _tap_flow_id = _tap_flow['id']
    port_id = _tap_flow_id

    def setUp(self):
        super(TestUpdateTapFlow, self).setUp()
        common.update_taas_resource = mock.Mock(return_value=None)
        common.find_taas_resource = mock.Mock(
            return_value=self._tap_flow_id)

        self.cmd = tapflow.UpdateTapFlow(self.app,
                                         self.namespace)

    def test_update_tap_flow(self):
        client = self.app.client_manager.neutronclient
        mock_tap_flow_update = common.update_taas_resource
        arglist = [
            self._tap_flow_name,
            '--name', 'name_updated',
            '--description', 'desc_updated',
        ]
        verifylist = [
            ('tap_flow', self._tap_flow_name),
            ('name', 'name_updated'),
            ('description', 'desc_updated'),
        ]

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)
        result = self.cmd.take_action(parsed_args)

        attrs = {
            'name': 'name_updated',
            'description': 'desc_updated', }
        tf_id = self._tap_flow_id
        mock_tap_flow_update.assert_called_once_with(self.cmd, client,
                                                     'tap_flow',
                                                     attrs, tf_id)
        self.assertIsNone(result)
