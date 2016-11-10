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

from neutron_taas_dashboard.tests.integration_tests.pages.project.network \
    import tapservicedetailpage
from openstack_dashboard.test.integration_tests.pages import basepage
from openstack_dashboard.test.integration_tests.regions import forms
from openstack_dashboard.test.integration_tests.regions import tables
from selenium.webdriver.common import by


class TapservicesPage(basepage.BaseNavigationPage):
    PORT_TAB_INDEX = 1

    def __init__(self, driver, conf):
        super(TapservicesPage, self).__init__(driver, conf)
        self._page_title = "Tap Services"

    def _get_tap_rows(self):
        return self.tapservices_table.rows()

    def create_tapservice(self, service_name, desc_name, port_id):

        create_form = self.tapservices_table.create_tapservice()
        create_form.tap_service_name.text = service_name
        create_form.description.text = desc_name

        create_form.switch_to(self.PORT_TAB_INDEX)
        create_form.port.value = port_id
        create_form.submit()

    def delete_tapservice(self, name):
        row = self.get_row(name)
        row.mark()
        form = self.tapservices_table.delete_tapservice()
        confirm_delete_tapservice_form = form
        confirm_delete_tapservice_form.submit()

    def create_tapflow(self, service_name, flow_name,
                       desc_name, direction, port_id):

        row = self.get_row(service_name)
        create_form = self.tapservices_table.create_tapflow(row)
        create_form.tap_flow_name.text = flow_name
        create_form.description.text = desc_name
        create_form.direction.value = direction
        create_form.switch_to(self.PORT_TAB_INDEX)
        create_form.port.value = port_id
        create_form.submit()

    def get_row(self, name):
        names = self.tapservices_table.get_name()
        rowss = self._get_tap_rows()
        row = None
        for i, row_name in enumerate(names):
            if name == row_name:
                row = rowss[i]
        return row

    def go_to_overview_page(self, name):
        return tapservicedetailpage.TapserviceDetailPage(self.driver,
                                                         self.conf, name)

    @property
    def tapservices_table(self):
        return TapservicesTable(self.driver, self.conf)


class TapservicesTable(tables.TableRegion):
    name = "tap_service"
    CREATE_TAPSERVICE_FORM_FIELDS = (("tap_service_name",
                                      "description"),
                                     ("port", "port"))
    CREATE_TAPFLOW_FORM_FIELDS = (("tap_flow_name",
                                   "description", "direction"),
                                  ("port", "port"))
    _name_locator = (by.By.CSS_SELECTOR, 'tbody > tr > td > a')

    @tables.bind_table_action('create')
    def create_tapservice(self, create_button):
        create_button.click()
        return forms.TabbedFormRegion(self.driver, self.conf,
                                      self.CREATE_TAPSERVICE_FORM_FIELDS)

    @tables.bind_table_action('delete')
    def delete_tapservice(self, delete_button):
        delete_button.click()
        return forms.BaseFormRegion(self.driver, self.conf)

    @tables.bind_row_action('tapflow')
    def create_tapflow(self, create_button, row):
        create_button.click()
        return forms.TabbedFormRegion(self.driver, self.conf,
                                      self.CREATE_TAPFLOW_FORM_FIELDS)

    def get_name(self):
        tap_names = []
        for elem in self._get_elements(*self._name_locator):
            tap_names.append(elem.text)
        return tap_names

    def rows(self):
        if self._is_element_present(*self._empty_table_locator):
            return []
        else:
            return self._get_rows()
