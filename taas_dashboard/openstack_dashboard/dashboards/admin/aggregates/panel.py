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

import logging

from django.utils.translation import ugettext_lazy as _

import horizon

from openstack_dashboard.api import nova
from openstack_dashboard.dashboards.admin import dashboard

LOG = logging.getLogger(__name__)


class Aggregates(horizon.Panel):
    name = _("Host Aggregates")
    slug = 'aggregates'
    permissions = ('openstack.services.compute',)

    def allowed(self, context):
        # extend basic permission-based check with a check to see whether
        # the Aggregates extension is even enabled in nova
        try:
            if not nova.extension_supported('Aggregates', context['request']):
                return False
        except Exception:
            LOG.error("Call to list supported extensions failed. This is "
                      "likely due to a problem communicating with the Nova "
                      "endpoint. Host Aggregates panel will not be displayed.")
            return False
        return super(Aggregates, self).allowed(context)


dashboard.Admin.register(Aggregates)
