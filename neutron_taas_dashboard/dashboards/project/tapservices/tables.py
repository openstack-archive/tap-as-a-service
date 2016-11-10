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


class TapFilterAction(tables.FilterAction):

    def filter(self, table, tap_services, filter_string):
        """Naive case-insensitive search."""
        query = filter_string.lower()
        return [tap_service for tap_service in tap_services
                if query in tap_service.id.lower()]


class CreateTapService(tables.LinkAction):
    name = "create"
    verbose_name = _("Create Tap Service")
    url = "horizon:project:tapservices:create"
    classes = ("ajax-modal",)
    icon = "plus"
    policy_rules = (("network", "create_tap_service"),)

    def allowed(self, request, datum=None):
        return True


class DeleteTapService(tables.DeleteAction):
    @staticmethod
    def action_present(count):
        return ungettext_lazy(
            u"Delete Tap Service",
            u"Delete Tap Services",
            count
        )

    @staticmethod
    def action_past(count):
        return ungettext_lazy(
            u"Deleted Tap Service",
            u"Deleted Tap Services",
            count
        )

    policy_rules = (("network", "delete_tap_service"),)

    def delete(self, request, tap_service_id):
        tap_service_name = tap_service_id
        try:
            api.taas.delete_tap_service(request, tap_service_id)
            LOG.debug('Deleted tap service %s successfully', tap_service_id)
        except Exception:
            msg = _('Failed to delete tap service %s')
            LOG.info(msg, tap_service_id)
            redirect = reverse("horizon:project:tapservices:index")
            exceptions.handle(request,
                              msg % tap_service_name,
                              redirect=redirect)


class CreateTapFlow(tables.LinkAction):
    name = "tapflow"
    verbose_name = _("Create Tap Flow")
    url = "horizon:project:tapservices:createtapflow"
    classes = ("ajax-modal",)
    icon = "plus"
    policy_rules = (("network", "create_tap_flow"),)

    def allowed(self, request, datum=None):
        return True


class TapServicesTable(tables.DataTable):
    name = tables.Column("name_or_id",
                         verbose_name=_("Name"),
                         link="horizon:project:tapservices:detail")
    port_id = tables.Column("port_id",
                            verbose_name=_("Port ID"),)

    def get_object_display(self, obj):
        return obj.id

    class Meta(object):
        name = "tap_service"
        verbose_name = _("Tap Services")
        table_actions = (CreateTapService, DeleteTapService, TapFilterAction)
        row_actions = (CreateTapFlow, DeleteTapService,)
