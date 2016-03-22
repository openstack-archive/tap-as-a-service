# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import os
import time
import traceback
import uuid

import testtools
import xvfbwrapper

from openstack_dashboard.test.integration_tests import config
from openstack_dashboard.test.integration_tests.pages import loginpage
from openstack_dashboard.test.integration_tests import webdriver


def gen_random_resource_name(resource="", timestamp=True):
    """Generate random resource name using uuid and timestamp.

    Input fields are usually limited to 255 or 80 characters hence their
    provide enough space for quite long resource names, but it might be
    the case that maximum field length is quite restricted, it is then
    necessary to consider using shorter resource argument or avoid using
    timestamp by setting timestamp argument to False.
    """
    fields = ["horizon"]
    if resource:
        fields.append(resource)
    if timestamp:
        tstamp = time.strftime("%d-%m-%H-%M-%S")
        fields.append(tstamp)
    fields.append(str(uuid.uuid4()).replace("-", ""))
    return "_".join(fields)


class BaseTestCase(testtools.TestCase):

    CONFIG = config.get_config()

    def setUp(self):
        if os.environ.get('INTEGRATION_TESTS', False):
            # Start a virtual display server for running the tests headless.
            if os.environ.get('SELENIUM_HEADLESS', False):
                self.vdisplay = xvfbwrapper.Xvfb(width=1280, height=720)
                # workaround for memory leak in Xvfb taken from: http://blog.
                # jeffterrace.com/2012/07/xvfb-memory-leak-workaround.html
                self.vdisplay.xvfb_cmd.append("-noreset")
                # disables X access control
                self.vdisplay.xvfb_cmd.append("-ac")
                self.vdisplay.start()
            # Start the Selenium webdriver and setup configuration.
            self.driver = webdriver.WebDriverWrapper()
            self.driver.maximize_window()
            self.driver.implicitly_wait(self.CONFIG.selenium.implicit_wait)
            self.driver.set_page_load_timeout(
                self.CONFIG.selenium.page_timeout)
            self.addOnException(self._dump_page_html_source)
        else:
            msg = "The INTEGRATION_TESTS env variable is not set."
            raise self.skipException(msg)
        super(BaseTestCase, self).setUp()

    def _dump_page_html_source(self, exc_info):
        content = None
        try:
            pg_source = self._get_page_html_source()
            content = testtools.content.Content(
                testtools.content_type.ContentType('text', 'html'),
                lambda: pg_source)
        except Exception:
            exc_traceback = traceback.format_exc()
            content = testtools.content.text_content(exc_traceback)
        finally:
            self.addDetail("PageHTMLSource.html", content)

    def _get_page_html_source(self):
        """Gets html page source.

        self.driver.page_source is not used on purpose because it does not
        display html code generated/changed by javascript.
        """

        html_elem = self.driver.find_element_by_tag_name("html")
        return html_elem.get_attribute("innerHTML").encode("UTF-8")

    def tearDown(self):
        if os.environ.get('INTEGRATION_TESTS', False):
            self.driver.quit()
        if hasattr(self, 'vdisplay'):
            self.vdisplay.stop()
        super(BaseTestCase, self).tearDown()


class TestCase(BaseTestCase):

    TEST_USER_NAME = BaseTestCase.CONFIG.identity.username
    TEST_PASSWORD = BaseTestCase.CONFIG.identity.password

    def setUp(self):
        super(TestCase, self).setUp()
        self.login_pg = loginpage.LoginPage(self.driver, self.CONFIG)
        self.login_pg.go_to_login_page()
        self.home_pg = self.login_pg.login(self.TEST_USER_NAME,
                                           self.TEST_PASSWORD)

    def tearDown(self):
        try:
            if self.home_pg.is_logged_in:
                self.home_pg.go_to_home_page()
                self.home_pg.log_out()
        finally:
            super(TestCase, self).tearDown()


class AdminTestCase(TestCase):

    TEST_USER_NAME = TestCase.CONFIG.identity.admin_username
    TEST_PASSWORD = TestCase.CONFIG.identity.admin_password
