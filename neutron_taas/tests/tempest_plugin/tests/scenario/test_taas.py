# Copyright (c) 2015 Midokura SARL
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

from tempest.common import utils
from tempest import config
from tempest.lib import decorators

from neutron_taas.tests.tempest_plugin.tests.scenario import base

CONF = config.CONF


class TestTaaS(base.TaaSScenarioTest):

    @classmethod
    def resource_setup(cls):
        super(TestTaaS, cls).resource_setup()
        for ext in ['taas']:
            if not utils.is_extension_enabled(ext, 'network'):
                msg = "%s Extension not enabled." % ext
                raise cls.skipException(msg)

    @decorators.idempotent_id('40903cbd-0e3c-464d-b311-dc77d3894e65')
    def test_dummy(self):
        pass
