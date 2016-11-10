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

from openstack_dashboard.test.integration_tests.pages import basepage
from openstack_dashboard.test.integration_tests.regions import forms
from openstack_dashboard.test.integration_tests.regions import tables
from selenium.webdriver.common import by


class TapserviceDetailPage(basepage.BaseNavigationPage):
    PORT_TAB_INDEX = 1
    _breadcrumb_routers_locator = (by.By.CSS_SELECTOR,
                                   'ol.breadcrumb>li>' +
                                   'a[href*="/dashboard/project/tapservices"]')

    def __init__(self, driver, conf, name):
        super(TapserviceDetailPage, self).__init__(driver, conf)
        self._page_title = "Tap Service Details:" + name

    def _get_tap_rows(self):
        return self.tapflows_table.rows()

    def delete_tapflow(self, name):
        row = self.get_row(name)
        row.mark()
        confirm_delete_tapflow_form = self.tapflows_table.delete_tapflow()
        confirm_delete_tapflow_form.submit()

    def get_row(self, name):
        names = self.tapflows_table.get_name()
        rowss = self._get_tap_rows()
        row = None
        for i, row_name in enumerate(names):
            if name == row_name:
                row = rowss[i]
        return row

    def switch_to_tapservice_page(self):
        self._get_element(*self._breadcrumb_routers_locator).click()

    @property
    def tapflows_table(self):
        return TapflowsTable(self.driver, self.conf)


class TapflowsTable(tables.TableRegion):
    name = "tapflows"
    _name_locator = (by.By.CSS_SELECTOR, 'tbody > tr > td > a')

    @tables.bind_table_action('delete')
    def delete_tapflow(self, delete_button):
        delete_button.click()
        return forms.BaseFormRegion(self.driver, self.conf)

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
