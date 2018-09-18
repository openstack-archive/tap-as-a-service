# Copyright 2016 VMware, Inc.
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

from neutron.tests.unit import testlib_api

from neutron_lib import context
from oslo_utils import importutils
from oslo_utils import uuidutils

from neutron_taas.db import taas_db
from neutron_taas.extensions import taas


DB_PLUGIN_KLAAS = 'neutron.db.db_base_plugin_v2.NeutronDbPluginV2'
_uuid = uuidutils.generate_uuid


class TaaSDbTestCase(testlib_api.SqlTestCase):

    """Unit test for TaaS DB support."""

    def setUp(self):
        super(TaaSDbTestCase, self).setUp()
        self.ctx = context.get_admin_context()
        self.mixin = taas_db.Taas_db_Mixin()
        self.plugin = importutils.import_object(DB_PLUGIN_KLAAS)
        self.tenant_id = 'fake-tenant-id'

    def _get_tap_service_data(self, name='ts-1', port_id=None):
        port_id = port_id or _uuid()
        return {"tap_service": {"name": name,
                                "tenant_id": self.tenant_id,
                                "description": "test tap service",
                                "port_id": port_id}}

    def _get_tap_flow_data(self, tap_service_id, name='tf-1',
                           direction='BOTH', source_port=None,
                           vlan_filter=None):
        source_port = source_port or _uuid()
        return {"tap_flow": {"name": name,
                             "tenant_id": self.tenant_id,
                             "description": "test tap flow",
                             "tap_service_id": tap_service_id,
                             "source_port": source_port,
                             "direction": direction,
                             "vlan_filter": vlan_filter}}

    def _get_tap_service(self, tap_service_id):
        """Helper method to retrieve tap service."""
        with self.ctx.session.begin(subtransactions=True):
            return self.mixin.get_tap_service(self.ctx, tap_service_id)

    def _get_tap_services(self):
        """Helper method to retrieve all tap services."""
        with self.ctx.session.begin(subtransactions=True):
            return self.mixin.get_tap_services(self.ctx)

    def _create_tap_service(self, tap_service):
        """Helper method to create tap service."""
        with self.ctx.session.begin(subtransactions=True):
            return self.mixin.create_tap_service(self.ctx, tap_service)

    def _update_tap_service(self, tap_service_id, tap_service):
        """Helper method to update tap service."""
        with self.ctx.session.begin(subtransactions=True):
            return self.mixin.update_tap_service(self.ctx,
                                                 tap_service_id,
                                                 tap_service)

    def _delete_tap_service(self, tap_service_id):
        """Helper method to delete tap service."""
        with self.ctx.session.begin(subtransactions=True):
            return self.mixin.delete_tap_service(self.ctx, tap_service_id)

    def _get_tap_flow(self, tap_flow_id):
        """Helper method to retrieve tap flow."""
        with self.ctx.session.begin(subtransactions=True):
            return self.mixin.get_tap_flow(self.ctx, tap_flow_id)

    def _get_tap_flows(self):
        """Helper method to retrieve all tap flows."""
        with self.ctx.session.begin(subtransactions=True):
            return self.mixin.get_tap_flows(self.ctx)

    def _create_tap_flow(self, tap_flow):
        """Helper method to create tap flow."""
        with self.ctx.session.begin(subtransactions=True):
            return self.mixin.create_tap_flow(self.ctx, tap_flow)

    def _update_tap_flow(self, tap_flow_id, tap_flow):
        """Helper method to update tap flow."""
        with self.ctx.session.begin(subtransactions=True):
            return self.mixin.update_tap_flow(self.ctx, tap_flow_id, tap_flow)

    def _delete_tap_flow(self, tap_flow_id):
        """Helper method to delete tap flow."""
        with self.ctx.session.begin(subtransactions=True):
            return self.mixin.delete_tap_flow(self.ctx, tap_flow_id)

    def test_tap_service_get(self):
        """Test to retrieve a tap service from the database."""
        name = 'test-tap-service'
        data = self._get_tap_service_data(name=name)
        result = self._create_tap_service(data)
        get_result = self._get_tap_service(result['id'])
        self.assertEqual(name, get_result['name'])

    def test_tap_service_create(self):
        """Test to create a tap service in the database."""
        name = 'test-tap-service'
        port_id = _uuid()
        data = self._get_tap_service_data(name=name, port_id=port_id)
        result = self._create_tap_service(data)
        self.assertEqual(name, result['name'])
        self.assertEqual(port_id, result['port_id'])

    def test_tap_service_list(self):
        """Test to retrieve all tap services from the database."""
        name_1 = "ts-1"
        data_1 = self._get_tap_service_data(name=name_1)
        name_2 = "ts-2"
        data_2 = self._get_tap_service_data(name=name_2)
        self._create_tap_service(data_1)
        self._create_tap_service(data_2)
        tap_services = self._get_tap_services()
        self.assertEqual(2, len(tap_services))

    def test_tap_service_update(self):
        """Test to update a tap service in the database."""
        original_name = "ts-1"
        updated_name = "ts-1-got-updated"
        data = self._get_tap_service_data(name=original_name)
        ts = self._create_tap_service(data)
        updated_data = self._get_tap_service_data(name=updated_name)
        ts_updated = self._update_tap_service(ts['id'], updated_data)
        self.assertEqual(updated_name, ts_updated['name'])

    def test_tap_service_delete(self):
        """Test to delete a tap service from the database."""
        data = self._get_tap_service_data()
        result = self._create_tap_service(data)
        self._delete_tap_service(result['id'])
        self.assertRaises(taas.TapServiceNotFound,
                          self._get_tap_service, result['id'])

    def test_tap_flow_get(self):
        """Test to retrieve a tap flow from the database."""
        ts_data = self._get_tap_service_data()
        ts = self._create_tap_service(ts_data)
        tf_name = 'test-tap-flow'
        tf_data = self._get_tap_flow_data(tap_service_id=ts['id'],
                                          name=tf_name)
        tf = self._create_tap_flow(tf_data)
        get_tf = self._get_tap_flow(tf['id'])
        self.assertEqual(tf_name, get_tf['name'])

    def test_tap_flow_create(self):
        """Test to create a tap flow in the database."""
        ts_data = self._get_tap_service_data()
        ts = self._create_tap_service(ts_data)
        tf_name = 'test-tap-flow'
        tf_direction = 'IN'
        tf_source_port = _uuid()
        tf_data = self._get_tap_flow_data(tap_service_id=ts['id'],
                                          name=tf_name,
                                          source_port=tf_source_port,
                                          direction=tf_direction)
        tf = self._create_tap_flow(tf_data)
        self.assertEqual(tf_name, tf['name'])
        self.assertEqual(tf_direction, tf['direction'])
        self.assertEqual(tf_source_port, tf['source_port'])

    def test_tap_flow_create_with_vlan_filter(self):
        """Test to create a tap flow (with vlan_filter) in the database."""
        ts_data = self._get_tap_service_data()
        ts = self._create_tap_service(ts_data)
        tf_name = 'test-tap-flow'
        tf_direction = 'IN'
        tf_source_port = _uuid()
        tf_vlan_filter = '9-18,27,36-45'
        tf_data = self._get_tap_flow_data(tap_service_id=ts['id'],
                                          name=tf_name,
                                          source_port=tf_source_port,
                                          direction=tf_direction,
                                          vlan_filter=tf_vlan_filter)
        tf = self._create_tap_flow(tf_data)
        self.assertEqual(tf_name, tf['name'])
        self.assertEqual(tf_direction, tf['direction'])
        self.assertEqual(tf_source_port, tf['source_port'])
        self.assertEqual(tf_vlan_filter, tf['vlan_filter'])

    def test_tap_flow_list(self):
        """Test to retrieve all tap flows from the database."""
        ts_data = self._get_tap_service_data()
        ts = self._create_tap_service(ts_data)
        tf_1_name = "tf-1"
        tf_1_data = self._get_tap_flow_data(tap_service_id=ts['id'],
                                            name=tf_1_name)
        tf_2_name = "tf-2"
        tf_2_data = self._get_tap_flow_data(tap_service_id=ts['id'],
                                            name=tf_2_name)
        self._create_tap_flow(tf_1_data)
        self._create_tap_flow(tf_2_data)
        tap_flows = self._get_tap_flows()
        self.assertEqual(2, len(tap_flows))

    def test_tap_flow_delete(self):
        """Test to delete a tap flow from the database."""
        ts_data = self._get_tap_service_data()
        ts = self._create_tap_service(ts_data)
        tf_name = "test-tap-flow"
        tf_data = self._get_tap_flow_data(tap_service_id=ts['id'],
                                          name=tf_name)
        tf = self._create_tap_flow(tf_data)
        self._delete_tap_flow(tf['id'])
        self.assertRaises(taas.TapFlowNotFound,
                          self._get_tap_flow, tf['id'])
