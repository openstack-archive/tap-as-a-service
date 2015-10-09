# Copyright (C) 2015 Midokura SARL.
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

import contextlib

import mock
import testtools

from oslo_config import cfg
from oslo_utils import uuidutils

import neutron.common.rpc as n_rpc
import neutron.common.utils as n_utils
from neutron import context
from neutron.tests.unit import testlib_api

import neutron_taas.db.taas_db  # noqa
import neutron_taas.extensions.taas as taas_ext
from neutron_taas.services.taas import taas_plugin


class TestTaasPlugin(testlib_api.SqlTestCaseLight):
    def setUp(self):
        super(TestTaasPlugin, self).setUp()
        mock.patch.object(n_rpc, 'create_connection', auto_spec=True).start()
        mock.patch.object(taas_plugin, 'TaasCallbacks', auto_spec=True).start()
        mock.patch.object(taas_plugin, 'TaasAgentApi', auto_spec=True).start()
        self._plugin = taas_plugin.TaasPlugin()
        self._context = context.get_admin_context()

        self._tenant_id = 'tenant-X'
        self._network_id = uuidutils.generate_uuid()
        self._host_id = 'host-A'
        self._port_id = uuidutils.generate_uuid()
        self._port_details = {
            'tenant_id': self._tenant_id,
            'binding:host_id': self._host_id,
            'mac_address': n_utils.get_random_mac(
                'fa:16:3e:00:00:00'.split(':')),
        }
        self._tap_service = {
            'tenant_id': self._tenant_id,
            'name': 'MyTap',
            'description': 'This is my tap service',
            'port_id': self._port_id,
            'network_id': self._network_id,
        }
        self._tap_flow = {
            'description': 'This is my tap flow',
            'direction': 'BOTH',
            'name': 'MyTapFlow',
            'source_port': self._port_id,
            'tenant_id': self._tenant_id,
        }

    @contextlib.contextmanager
    def tap_service(self):
        req = {
            'tap_service': self._tap_service,
        }
        with mock.patch.object(self._plugin, '_get_port_details',
                               return_value=self._port_details):
            yield self._plugin.create_tap_service(self._context, req)
        self._tap_service['id'] = mock.ANY
        expected_msg = {
            'tap_service': self._tap_service,
            'taas_id': mock.ANY,
            'port': self._port_details,
        }
        self._plugin.agent_rpc.assert_has_calls([
            mock.call.create_tap_service(self._context, expected_msg,
                                         self._host_id),
        ])

    @contextlib.contextmanager
    def tap_flow(self, tap_service, tenant_id=None):
        self._tap_flow['tap_service_id'] = tap_service
        if tenant_id is not None:
            self._tap_flow['tenant_id'] = tenant_id
        req = {
            'tap_flow': self._tap_flow,
        }
        with mock.patch.object(self._plugin, '_get_port_details',
                               return_value=self._port_details):
            yield self._plugin.create_tap_flow(self._context, req)
        self._tap_flow['id'] = mock.ANY
        self._tap_service['id'] = mock.ANY
        expected_msg = {
            'tap_flow': self._tap_flow,
            'port_mac': self._port_details['mac_address'],
            'taas_id': mock.ANY,
            'port': self._port_details,
        }
        self._plugin.agent_rpc.assert_has_calls([
            mock.call.create_tap_flow(self._context, expected_msg,
                                      self._host_id),
        ])

    def test_create_tap_service(self):
        with self.tap_service():
            pass

    def test_create_tap_service_wrong_tenant_id(self):
        self._port_details['tenant_id'] = 'other-tenant'
        with testtools.ExpectedException(taas_ext.PortDoesNotBelongToTenant), \
            self.tap_service():
            pass
        self.assertEqual([], self._plugin.agent_rpc.mock_calls)

    def test_create_tap_service_reach_limit(self):
        cfg.CONF.set_override('vlan_range_end', 3900, 'taas')  # same as start
        with testtools.ExpectedException(taas_ext.TapServiceLimitReached), \
            self.tap_service():
            pass
        self.assertEqual([], self._plugin.agent_rpc.mock_calls)

    def test_delete_tap_service(self):
        with self.tap_service() as ts:
            self._plugin.delete_tap_service(self._context, ts['id'])
        expected_msg = {
            'tap_service': self._tap_service,
            'taas_id': mock.ANY,
            'port': self._port_details,
        }
        self._plugin.agent_rpc.assert_has_calls([
            mock.call.delete_tap_service(self._context, expected_msg,
                                         self._host_id),
        ])

    def test_delete_tap_service_with_flow(self):
        with self.tap_service() as ts, \
            self.tap_flow(tap_service=ts['id']) as tf:
            self._plugin.delete_tap_service(self._context, ts['id'])
        expected_msg = {
            'tap_service': self._tap_service,
            'taas_id': mock.ANY,
            'port': self._port_details,
        }
        self._plugin.agent_rpc.assert_has_calls([
            mock.call.delete_tap_service(self._context, expected_msg,
                                         self._host_id),
        ])
        self._tap_flow['id'] = tf['id']
        expected_msg = {
            'tap_flow': self._tap_flow,
            'taas_id': mock.ANY,
            'port_mac': self._port_details['mac_address'],
            'port': self._port_details,
        }
        self._plugin.agent_rpc.assert_has_calls([
            mock.call.delete_tap_flow(self._context, expected_msg,
                                      self._host_id),
        ])

    def test_delete_tap_service_non_existent(self):
        with testtools.ExpectedException(taas_ext.TapServiceNotFound):
            self._plugin.delete_tap_service(self._context, 'non-existent')

    def test_create_tap_flow(self):
        with self.tap_service() as ts, self.tap_flow(tap_service=ts['id']):
            pass

    def test_create_tap_flow_wrong_tenant_id(self):
        with self.tap_service() as ts, \
            testtools.ExpectedException(taas_ext.TapServiceNotBelongToTenant), \
            self.tap_flow(tap_service=ts['id'], tenant_id='other-tenant'):
            pass

    def test_delete_tap_flow(self):
        with self.tap_service() as ts, \
            self.tap_flow(tap_service=ts['id']) as tf:
            self._plugin.delete_tap_flow(self._context, tf['id'])
        self._tap_flow['id'] = tf['id']
        expected_msg = {
            'tap_flow': self._tap_flow,
            'taas_id': mock.ANY,
            'port_mac': self._port_details['mac_address'],
            'port': self._port_details,
        }
        self._plugin.agent_rpc.assert_has_calls([
            mock.call.delete_tap_flow(self._context, expected_msg,
                                      self._host_id),
        ])
