# Copyright (C) 2018 AT&T
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

import copy

import mock
from neutron_taas.common import constants as taas_consts
from neutron_taas.extensions import taas as taas_ext
from neutron_taas.extensions import vlan_filter as vlan_filter_ext
from neutron_taas.tests.unit.extensions import test_taas as test_taas_ext
from oslo_utils import uuidutils
from webob import exc

from neutron.tests.unit.api.v2 import test_base as test_api_v2
import webtest


_uuid = uuidutils.generate_uuid
_get_path = test_api_v2._get_path


class VlanFilterExtensionTestCase(test_taas_ext.TaasExtensionTestCase):
    def setUp(self):
        super(test_taas_ext.TaasExtensionTestCase, self).setUp()

        attr_map = taas_ext.RESOURCE_ATTRIBUTE_MAP
        attr_map['tap_flows'].update(
            vlan_filter_ext.EXTENDED_ATTRIBUTES_2_0['tap_flows'])
        self.setup_extension(
            'neutron_taas.extensions.taas.TaasPluginBase',
            'TAAS',
            taas_ext.Taas,
            'taas',
            plural_mappings={}
        )

    def _get_expected_tap_flow(self, data):
        ret = super(VlanFilterExtensionTestCase,
                    self)._get_expected_tap_flow(data)
        ret['tap_flow'].update(
            vlan_filter=data['tap_flow'].get('vlan_filter', None))
        return ret

    def test_create_tap_flow_with_vlan_filter(self):
        tenant_id = _uuid()
        tap_flow_data = {
            'tenant_id': tenant_id,
            'name': 'MyTapFlow',
            'description': 'This is my tap flow',
            'direction': 'BOTH',
            'tap_service_id': _uuid(),
            'source_port': _uuid(),
            'project_id': tenant_id,
            'vlan_filter': taas_consts.VLAN_RANGE,
        }
        data = {'tap_flow': tap_flow_data}
        expected_data = self._get_expected_tap_flow(data)
        expected_ret_val = copy.copy(expected_data['tap_flow'])
        expected_ret_val.update({'id': _uuid()})
        instance = self.plugin.return_value
        instance.create_tap_flow.return_value = expected_ret_val

        res = self.api.post(
            _get_path(test_taas_ext.TAP_FLOW_PATH, fmt=self.fmt),
            self.serialize(data),
            content_type='application/%s' % self.fmt)
        instance.create_tap_flow.assert_called_with(
            mock.ANY,
            tap_flow=expected_data)
        self.assertEqual(exc.HTTPCreated.code, res.status_int)
        res = self.deserialize(res)
        self.assertIn('tap_flow', res)
        self.assertEqual(expected_ret_val, res['tap_flow'])

    def test_create_tap_flow_invalid_vlan_filter_value(self):
        tenant_id = _uuid()
        tap_flow_data = {
            'tenant_id': tenant_id,
            'name': 'MyTapFlow',
            'description': 'This is my tap flow',
            'direction': 'BOTH',
            'tap_service_id': _uuid(),
            'source_port': _uuid(),
            'project_id': tenant_id,
            'vlan_filter': '10-25,',
        }
        data = {'tap_flow': tap_flow_data}
        self.assertRaises(
            webtest.app.AppError,
            self.api.post,
            _get_path(test_taas_ext.TAP_FLOW_PATH, fmt=self.fmt),
            self.serialize(data),
            content_type='application/%s' % self.fmt)
