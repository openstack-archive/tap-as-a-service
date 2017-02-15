# Copyright (c) 2017 NEC Technologies India Ltd.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.


from neutron_lib import context
from oslo_policy import policy as oslo_policy
from oslo_serialization import jsonutils

from neutron import policy
from neutron.tests import base


class DefaultPolicyTest(base.BaseTestCase):

    def setUp(self):
        super(DefaultPolicyTest, self).setUp()
        tmpfilename = self.get_temp_file_path('policy.json')
        self.rules = {
            "default": '',
            "example:exist": '!',
        }
        with open(tmpfilename, "w") as policyfile:
            jsonutils.dump(self.rules, policyfile)
        policy.refresh(policy_file=tmpfilename)

        self.context = context.Context('fake', 'fake')

    def test_policy_called(self):
        self.assertRaises(oslo_policy.PolicyNotAuthorized, policy.enforce,
                          self.context, "example:exist", {})

    def test_not_found_policy_calls_default(self):
        policy.enforce(self.context, "example:noexist", {})
