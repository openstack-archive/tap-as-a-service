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


class TestTapflows(helpers.AdminTestCase):
    SERVICE_NAME = 'test'
    FLOW_NAME = helpers.gen_random_resource_name("flow")
    DESC_NAME = helpers.gen_random_resource_name("desc")
    PG_NAME = 'demo'
    PORT_ID = '29a79636-17c9-4e92-908a-bdc27c5d071f'
    DIRECTION = 'BOTH'

    @decorators.services_required("neutron")
    def test_tapflows(self):
        tapservice_page = self.home_pg.go_to_network_tapservicespage()

        tapservice_page.change_project(self.PG_NAME)

        tapservice_page.create_tapflow(self.SERVICE_NAME,
                                       self.FLOW_NAME, self.DESC_NAME,
                                       self.DIRECTION, self.PORT_ID)
        self.assertTrue(
            tapservice_page.find_message_and_dismiss(messages.SUCCESS))
        self.assertFalse(
            tapservice_page.find_message_and_dismiss(messages.ERROR))

        tapflow_page = tapservice_page.go_to_overview_page(self.SERVICE_NAME)
        tapflow_page.delete_tapflow(self.FLOW_NAME)

        self.assertTrue(
            tapflow_page.find_message_and_dismiss(messages.SUCCESS))
        self.assertFalse(
            tapflow_page.find_message_and_dismiss(messages.ERROR))
