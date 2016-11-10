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

from django.utils.translation import ugettext_lazy as _

from neutron_taas_dashboard.dashboards.project.tapservices import tables


class DeleteTapService(tables.DeleteTapService):
    failure_url = 'horizon:project:network_topology'


class TapServicesTable(tables.TapServicesTable):

    class Meta(object):
        name = "tap_service"
        verbose_name = _("Tap Services")
        row_actions = (DeleteTapService, )
