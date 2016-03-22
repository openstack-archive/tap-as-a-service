# Copyright 2014, Rackspace, US, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import mock

from django.conf import settings

from openstack_dashboard.api.rest import nova
from openstack_dashboard.test import helpers as test


class NovaRestTestCase(test.TestCase):
    #
    # Keypairs
    #
    @mock.patch.object(nova.api, 'nova')
    def test_keypair_get(self, nc):
        request = self.mock_rest_request()
        nc.keypair_list.return_value = [
            mock.Mock(**{'to_dict.return_value': {'id': 'one'}}),
            mock.Mock(**{'to_dict.return_value': {'id': 'two'}}),
        ]
        response = nova.Keypairs().get(request)
        self.assertStatusCode(response, 200)
        self.assertEqual(response.content,
                         '{"items": [{"id": "one"}, {"id": "two"}]}')
        nc.keypair_list.assert_called_once_with(request)

    @mock.patch.object(nova.api, 'nova')
    def test_keypair_create(self, nc):
        request = self.mock_rest_request(body='''{"name": "Ni!"}''')
        new = nc.keypair_create.return_value
        new.to_dict.return_value = {'name': 'Ni!', 'public_key': 'sekrit'}
        new.name = 'Ni!'
        with mock.patch.object(settings, 'DEBUG', True):
            response = nova.Keypairs().post(request)
        self.assertStatusCode(response, 201)
        self.assertEqual(response.content,
                         '{"name": "Ni!", "public_key": "sekrit"}')
        self.assertEqual(response['location'], '/api/nova/keypairs/Ni%21')
        nc.keypair_create.assert_called_once_with(request, 'Ni!')

    @mock.patch.object(nova.api, 'nova')
    def test_keypair_import(self, nc):
        request = self.mock_rest_request(body='''
            {"name": "Ni!", "public_key": "hi"}
        ''')
        new = nc.keypair_import.return_value
        new.to_dict.return_value = {'name': 'Ni!', 'public_key': 'hi'}
        new.name = 'Ni!'
        with mock.patch.object(settings, 'DEBUG', True):
            response = nova.Keypairs().post(request)
        self.assertStatusCode(response, 201)
        self.assertEqual(response.content,
                         '{"name": "Ni!", "public_key": "hi"}')
        self.assertEqual(response['location'], '/api/nova/keypairs/Ni%21')
        nc.keypair_import.assert_called_once_with(request, 'Ni!', 'hi')

    #
    # Availability Zones
    #
    def test_availzone_get_brief(self):
        self._test_availzone_get(False)

    def test_availzone_get_detailed(self):
        self._test_availzone_get(True)

    @mock.patch.object(nova.api, 'nova')
    def _test_availzone_get(self, detail, nc):
        if detail:
            request = self.mock_rest_request(GET={'detailed': 'true'})
        else:
            request = self.mock_rest_request(GET={})
        nc.availability_zone_list.return_value = [
            mock.Mock(**{'to_dict.return_value': {'id': 'one'}}),
            mock.Mock(**{'to_dict.return_value': {'id': 'two'}}),
        ]
        response = nova.AvailabilityZones().get(request)
        self.assertStatusCode(response, 200)
        self.assertEqual(response.content,
                         '{"items": [{"id": "one"}, {"id": "two"}]}')
        nc.availability_zone_list.assert_called_once_with(request, detail)

    #
    # Limits
    #
    def test_limits_get_not_reserved(self):
        self._test_limits_get(False)

    def test_limits_get_reserved(self):
        self._test_limits_get(True)

    @mock.patch.object(nova.api, 'nova')
    def _test_limits_get(self, reserved, nc):
        if reserved:
            request = self.mock_rest_request(GET={'reserved': 'true'})
        else:
            request = self.mock_rest_request(GET={})
        nc.tenant_absolute_limits.return_value = {'id': 'one'}
        response = nova.Limits().get(request)
        self.assertStatusCode(response, 200)
        nc.tenant_absolute_limits.assert_called_once_with(request, reserved)
        self.assertEqual(response.content, '{"id": "one"}')

    #
    # Servers
    #
    @mock.patch.object(nova.api, 'nova')
    def test_server_create_missing(self, nc):
        request = self.mock_rest_request(body='''{"name": "hi"}''')
        response = nova.Servers().post(request)
        self.assertStatusCode(response, 400)
        self.assertEqual(response.content,
                         '"missing required parameter \'source_id\'"')
        nc.server_create.assert_not_called()

    @mock.patch.object(nova.api, 'nova')
    def test_server_create_basic(self, nc):
        request = self.mock_rest_request(body='''{"name": "Ni!",
            "source_id": "image123", "flavor_id": "flavor123",
            "key_name": "sekrit", "user_data": "base64 yes",
            "security_groups": [{"name": "root"}]}
        ''')
        new = nc.server_create.return_value
        new.to_dict.return_value = {'id': 'server123'}
        new.id = 'server123'
        response = nova.Servers().post(request)
        self.assertStatusCode(response, 201)
        self.assertEqual(response.content, '{"id": "server123"}')
        self.assertEqual(response['location'], '/api/nova/servers/server123')
        nc.server_create.assert_called_once_with(
            request, 'Ni!', 'image123', 'flavor123', 'sekrit', 'base64 yes',
            [{'name': 'root'}]
        )

    @mock.patch.object(nova.api, 'nova')
    def test_server_get_single(self, nc):
        request = self.mock_rest_request()
        nc.server_get.return_value.to_dict.return_value = {'name': '1'}

        response = nova.Server().get(request, "1")
        self.assertStatusCode(response, 200)
        nc.server_get.assert_called_once_with(request, "1")

    #
    # Extensions
    #
    @mock.patch.object(nova.api, 'nova')
    @mock.patch.object(settings,
                       'OPENSTACK_NOVA_EXTENSIONS_BLACKLIST', ['baz'])
    def _test_extension_list(self, nc):
        request = self.mock_rest_request()
        nc.list_extensions.return_value = [
            mock.Mock(**{'to_dict.return_value': {'name': 'foo'}}),
            mock.Mock(**{'to_dict.return_value': {'name': 'bar'}}),
            mock.Mock(**{'to_dict.return_value': {'name': 'baz'}}),
        ]
        response = nova.Extensions().get(request)
        self.assertStatusCode(response, 200)
        self.assertEqual(response.content,
                         '{"items": [{"name": "foo"}, {"name": "bar"}]}')
        nc.list_extensions.assert_called_once_with(request)

    #
    # Flavors
    #
    def test_get_extras_no(self):
        self._test_flavor_get_single(get_extras=False)

    def test_get_extras_yes(self):
        self._test_flavor_get_single(get_extras=True)

    def test_get_extras_default(self):
        self._test_flavor_get_single(get_extras=None)

    @mock.patch.object(nova.api, 'nova')
    def _test_flavor_get_single(self, nc, get_extras):
        if get_extras:
            request = self.mock_rest_request(GET={'get_extras': 'tRuE'})
        elif get_extras is None:
            request = self.mock_rest_request()
            get_extras = False
        else:
            request = self.mock_rest_request(GET={'get_extras': 'fAlsE'})
        nc.flavor_get.return_value.to_dict.return_value = {'name': '1'}

        response = nova.Flavor().get(request, "1")
        self.assertStatusCode(response, 200)
        if get_extras:
            self.assertEqual(response.content, '{"extras": {}, "name": "1"}')
        else:
            self.assertEqual(response.content, '{"name": "1"}')
        nc.flavor_get.assert_called_once_with(request, "1",
                                              get_extras=get_extras)

    @mock.patch.object(nova.api, 'nova')
    def _test_flavor_list_public(self, nc, is_public=None):
        if is_public:
            request = self.mock_rest_request(GET={'is_public': 'tRuE'})
        elif is_public is None:
            request = self.mock_rest_request(GET={})
        else:
            request = self.mock_rest_request(GET={'is_public': 'fAlsE'})
        nc.flavor_list.return_value = [
            mock.Mock(**{'to_dict.return_value': {'id': '1'}}),
            mock.Mock(**{'to_dict.return_value': {'id': '2'}}),
        ]
        response = nova.Flavors().get(request)
        self.assertStatusCode(response, 200)
        self.assertEqual(response.content,
                         '{"items": [{"id": "1"}, {"id": "2"}]}')
        nc.flavor_list.assert_called_once_with(request, is_public=is_public,
                                               get_extras=False)

    def test_flavor_list_private(self):
        self._test_flavor_list_public(is_public=False)

    def test_flavor_list_public(self):
        self._test_flavor_list_public(is_public=True)

    def test_flavor_list_public_none(self):
        self._test_flavor_list_public(is_public=None)

    @mock.patch.object(nova.api, 'nova')
    def _test_flavor_list_extras(self, nc, get_extras=None):
        if get_extras:
            request = self.mock_rest_request(GET={'get_extras': 'tRuE'})
        elif get_extras is None:
            request = self.mock_rest_request(GET={})
            get_extras = False
        else:
            request = self.mock_rest_request(GET={'get_extras': 'fAlsE'})
        nc.flavor_list.return_value = [
            mock.Mock(**{'extras': {}, 'to_dict.return_value': {'id': '1'}}),
            mock.Mock(**{'extras': {}, 'to_dict.return_value': {'id': '2'}}),
        ]
        response = nova.Flavors().get(request)
        self.assertStatusCode(response, 200)
        if get_extras:
            self.assertEqual(response.content,
                             '{"items": [{"extras": {}, "id": "1"}, '
                             '{"extras": {}, "id": "2"}]}')
        else:
            self.assertEqual(response.content,
                             '{"items": [{"id": "1"}, {"id": "2"}]}')
        nc.flavor_list.assert_called_once_with(request, is_public=None,
                                               get_extras=get_extras)

    def test_flavor_list_extras_no(self):
        self._test_flavor_list_extras(get_extras=False)

    def test_flavor_list_extras_yes(self):
        self._test_flavor_list_extras(get_extras=True)

    def test_flavor_list_extras_absent(self):
        self._test_flavor_list_extras(get_extras=None)

    @mock.patch.object(nova.api, 'nova')
    def test_flavor_extra_specs(self, nc):
        request = self.mock_rest_request()
        nc.flavor_get_extras.return_value.to_dict.return_value = {'foo': '1'}

        response = nova.FlavorExtraSpecs().get(request, "1")
        self.assertStatusCode(response, 200)
        nc.flavor_get_extras.assert_called_once_with(request, "1", raw=True)
