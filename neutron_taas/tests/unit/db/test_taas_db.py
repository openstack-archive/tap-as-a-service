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

from neutron import context
from neutron.tests.unit import testlib_api

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

    def _get_tap_service_data(self, name=None, port_id=None):
        name = name or 'ts-1'
        port_id = port_id or _uuid()
        return {"tap_service": {"name": name,
                                "tenant_id": self.tenant_id,
                                "description": "test tap service",
                                "port_id": port_id}}

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
