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
    FLOW_NAME = helpers.gen_random_resource_name("flow")
    DESC_NAME = helpers.gen_random_resource_name("desc")
    DIRECTION = 'BOTH'
    PG_NAME = 'demo'
    PORT_ID = '29a79636-17c9-4e92-908a-bdc27c5d071f'

    @decorators.services_required("neutron")
    def test_create_tapservices_tapflows(self):
        tapservice_page = self.home_pg.go_to_network_tapservicespage()
        tapservice_page.change_project(self.PG_NAME)

        self._create_tapservice(tapservice_page)
        self._create_tapflow(tapservice_page)

        tapflow_page = tapservice_page.go_to_overview_page(self.SERVICE_NAME)
        self._delete_tapflow(tapflow_page)

        tapflow_page.switch_to_tapservice_page()
        self._delete_tapservice(tapservice_page)

    def _create_tapservice(self, tapservice_page):
        tapservice_page.create_tapservice(self.SERVICE_NAME,
                                          self.DESC_NAME, self.PORT_ID)
        self.assertTrue(
            tapservice_page.find_message_and_dismiss(messages.SUCCESS))
        self.assertFalse(
            tapservice_page.find_message_and_dismiss(messages.ERROR))

    def _create_tapflow(self, tapservice_page):
        tapservice_page.create_tapflow(self.SERVICE_NAME,
                                       self.FLOW_NAME, self.DESC_NAME,
                                       self.DIRECTION, self.PORT_ID)
        self.assertTrue(
            tapservice_page.find_message_and_dismiss(messages.SUCCESS))
        self.assertFalse(
            tapservice_page.find_message_and_dismiss(messages.ERROR))

    def _delete_tapflow(self, tapflow_page):
        tapflow_page.delete_tapflow(self.FLOW_NAME)

        self.assertTrue(
            tapflow_page.find_message_and_dismiss(messages.SUCCESS))
        self.assertFalse(
            tapflow_page.find_message_and_dismiss(messages.ERROR))

    def _delete_tapservice(self, tapservice_page):
        tapservice_page.delete_tapservice(self.SERVICE_NAME)
        self.assertTrue(
            tapservice_page.find_message_and_dismiss(messages.SUCCESS))
        self.assertFalse(
            tapservice_page.find_message_and_dismiss(messages.ERROR))
