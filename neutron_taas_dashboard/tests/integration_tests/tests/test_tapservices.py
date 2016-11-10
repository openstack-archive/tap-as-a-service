#    Copyright 2016, FUJITSU LABORATORIES LTD.
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

from openstack_dashboard.test.integration_tests import decorators
from openstack_dashboard.test.integration_tests import helpers
from openstack_dashboard.test.integration_tests.regions import messages


class TestTapservices(helpers.AdminTestCase):
    SERVICE_NAME = helpers.gen_random_resource_name("service")
    DESC_NAME = helpers.gen_random_resource_name("desc")
    PG_NAME = 'demo'
    PORT_ID = 'c1c625e0-edfa-4550-9423-ad8d0dde801c'

    @decorators.services_required("neutron")
    def test_tapservices(self):
        tapservice_page = self.home_pg.go_to_network_tapservicespage()

        tapservice_page.change_project(self.PG_NAME)

        tapservice_page.create_tapservice(self.SERVICE_NAME,
                                          self.DESC_NAME, self.PORT_ID)
        self.assertTrue(
            tapservice_page.find_message_and_dismiss(messages.SUCCESS))
        self.assertFalse(
            tapservice_page.find_message_and_dismiss(messages.ERROR))

        tapservice_page.delete_tapservice(self.SERVICE_NAME)
        self.assertTrue(
            tapservice_page.find_message_and_dismiss(messages.SUCCESS))
        self.assertFalse(
            tapservice_page.find_message_and_dismiss(messages.ERROR))
