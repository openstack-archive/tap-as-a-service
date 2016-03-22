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

from django.test.utils import override_settings

from openstack_dashboard import policy
from openstack_dashboard import policy_backend
from openstack_dashboard.test import helpers as test


class PolicyTestCase(test.TestCase):
    @override_settings(POLICY_CHECK_FUNCTION=policy_backend.check)
    def test_policy_check_set(self):
        value = policy.check((("identity", "admin_required"),),
                             request=self.request)
        self.assertFalse(value)

    @override_settings(POLICY_CHECK_FUNCTION=None)
    def test_policy_check_not_set(self):
        value = policy.check((("identity", "admin_required"),),
                             request=self.request)
        self.assertTrue(value)


class PolicyBackendTestCaseAdmin(test.BaseAdminViewTests):
    @override_settings(POLICY_CHECK_FUNCTION=policy_backend.check)
    def test_policy_check_set_admin(self):
        value = policy.check((("identity", "admin_required"),),
                             request=self.request)
        self.assertTrue(value)
