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

from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ungettext_lazy

from horizon import exceptions
from horizon import tables

from neutron_taas_dashboard import api

import logging

LOG = logging.getLogger(__name__)


class CreateTapFlow(tables.LinkAction):
    name = "create"
    verbose_name = _("Create Tap Flow")
    url = "horizon:project:tapservices:createtapflow"
    classes = ("ajax-modal",)
    icon = "plus"
    policy_rules = (("network", "create_tap_flow"),)

    def get_link_url(self, datum=None):
        tap_service_id = self.table.kwargs['tap_service_id']
        return reverse(self.url, args=(tap_service_id,))

    def allowed(self, request, datum=None):
        return True


class DeleteTapFlow(tables.DeleteAction):
    @staticmethod
    def action_present(count):
        return ungettext_lazy(
            u"Delete Tap Flow",
            u"Delete Tap Flows",
            count
        )

    @staticmethod
    def action_past(count):
        return ungettext_lazy(
            u"Deleted Tap Flow",
            u"Deleted Tap Flows",
            count
        )

    policy_rules = (("network", "delete_tap_flow"),)

    def delete(self, request, tap_flow_id):
        tap_service_id = self.table.kwargs['tap_service_id']
        tap_flow_name = tap_flow_id
        LOG.error("DELETE_TAP_FLOW: DELETE: %s", tap_flow_id)
        try:
            api.taas.delete_tap_flow(request, tap_flow_id)
            LOG.debug('Deleted tap flow %s successfully', tap_flow_id)
        except Exception:
            msg = _('Failed to delete tap flow %s')
            LOG.info(msg, tap_flow_id)
            redirect = reverse("horizon:project:tapservices:detail",
                               args=[tap_service_id])
            exceptions.handle(request, msg % tap_flow_name, redirect=redirect)


class TapFlowsTable(tables.DataTable):
    name = tables.Column("name_or_id",
                         verbose_name=_("Name"),
                         link="horizon:project:tapservices:tapflows:detail")
    port_id = tables.Column("source_port",
                            verbose_name=_("Port ID"))
    tap_service_id = tables.Column("tap_service_id",
                                   verbose_name=_("Tap Service ID"))

    def get_object_display(self, obj):
        return obj.id

    class Meta(object):
        name = "tapflows"
        verbose_name = _("Tap Flows")
        table_actions = (CreateTapFlow, DeleteTapFlow,)
        row_actions = (DeleteTapFlow,)
        hidden_title = False
