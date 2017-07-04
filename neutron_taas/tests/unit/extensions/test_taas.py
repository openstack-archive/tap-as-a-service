# Copyright 2017 FUJITSU LABORATORIES LTD.

#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at

#         http://www.apache.org/licenses/LICENSE-2.0

#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import copy
import mock
from webob import exc

from oslo_utils import uuidutils

from neutron.tests.unit.api.v2 import test_base as test_api_v2
from neutron.tests.unit.extensions import base as test_api_v2_extension

from neutron_taas.extensions import taas as taas_ext

_uuid = uuidutils.generate_uuid
_get_path = test_api_v2._get_path

TAP_SERVICE_PATH = 'taas/tap_services'
TAP_FLOW_PATH = 'taas/tap_flows'


class TaasExtensionTestCase(test_api_v2_extension.ExtensionTestCase):
    fmt = 'json'

    def setUp(self):
        super(TaasExtensionTestCase, self).setUp()
        self._setUpExtension(
            'neutron_taas.extensions.taas.TaasPluginBase',
            'TAAS',
            taas_ext.RESOURCE_ATTRIBUTE_MAP,
            taas_ext.Taas,
            'taas',
            plural_mappings={}
        )

    def test_create_tap_service(self):
        tenant_id = _uuid()
        tap_service_data = {
            'tenant_id': tenant_id,
            'name': 'MyTap',
            'description': 'This is my tap service',
            'port_id': _uuid(),
            'project_id': tenant_id,
        }
        data = {'tap_service': tap_service_data}
        expected_ret_val = copy.copy(data['tap_service'])
        expected_ret_val.update({'id': _uuid()})
        instance = self.plugin.return_value
        instance.create_tap_service.return_value = expected_ret_val

        res = self.api.post(_get_path(TAP_SERVICE_PATH, fmt=self.fmt),
                            self.serialize(data),
                            content_type='application/%s' % self.fmt)
        instance.create_tap_service.assert_called_with(
            mock.ANY,
            tap_service=data)
        self.assertEqual(exc.HTTPCreated.code, res.status_int)
        res = self.deserialize(res)
        self.assertIn('tap_service', res)
        self.assertEqual(expected_ret_val, res['tap_service'])

    def test_delete_tap_service(self):
        self._test_entity_delete('tap_service')

    def test_create_tap_flow(self):
        tenant_id = _uuid()
        tap_flow_data = {
            'tenant_id': tenant_id,
            'name': 'MyTapFlow',
            'description': 'This is my tap flow',
            'direction': 'BOTH',
            'tap_service_id': _uuid(),
            'source_port': _uuid(),
            'project_id': tenant_id,
        }
        data = {'tap_flow': tap_flow_data}
        expected_ret_val = copy.copy(data['tap_flow'])
        expected_ret_val.update({'id': _uuid()})
        instance = self.plugin.return_value
        instance.create_tap_flow.return_value = expected_ret_val

        res = self.api.post(_get_path(TAP_FLOW_PATH, fmt=self.fmt),
                            self.serialize(data),
                            content_type='application/%s' % self.fmt)
        instance.create_tap_flow.assert_called_with(
            mock.ANY,
            tap_flow=data)
        self.assertEqual(exc.HTTPCreated.code, res.status_int)
        res = self.deserialize(res)
        self.assertIn('tap_flow', res)
        self.assertEqual(expected_ret_val, res['tap_flow'])

    def test_delete_tap_flow(self):
        self._test_entity_delete('tap_flow')
