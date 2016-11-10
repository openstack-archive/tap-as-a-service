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

from horizon import exceptions
from horizon import tables
from horizon.utils import memoized
from horizon import workflows

from neutron_taas_dashboard import api
from neutron_taas_dashboard.dashboards.project.tapservices \
    import tables as ts_tables
from neutron_taas_dashboard.dashboards.project.tapservices.tapflows \
    import tables as tf_tables
from neutron_taas_dashboard.dashboards.project.tapservices \
    import workflows as ts_workflows

import logging
LOG = logging.getLogger(__name__)


class IndexView(tables.DataTableView):
    table_class = ts_tables.TapServicesTable
    template_name = 'project/tapservices/index.html'
    page_title = _("Tap Services")

    @memoized.memoized_method
    def get_data(self):

        try:
            tap_service = api.taas.list_tap_service(self.request)
        except Exception:
            tap_service = []
            msg = _('Tap service list can not be retrieved.')
            exceptions.handle(self.request, msg)

        return tap_service


class CreateView(workflows.WorkflowView):
    workflow_class = ts_workflows.CreateTapService
    ajax_template_name = 'project/tapservices/create.html'


class DetailView(tables.DataTableView):
    table_class = tf_tables.TapFlowsTable
    template_name = 'project/tapservices/detail.html'
    page_title = _("Tap Service Details: {{ tap_service.name }}")

    def get_data(self):
        try:
            tap_service = self._get_data()
            tap_service_id = tap_service.id
            tap_flows_pre = api.taas.list_tap_flow(self.request,
                                                   tap_service_id)
            tap_flows = []
            for tap_flow in tap_flows_pre:
                tap_flow_tap_service_id = tap_flow['tap_service_id']
                if tap_flow_tap_service_id == tap_service_id:
                    tap_flows = tap_flows + [tap_flow]
        except Exception:
            tap_flows = []
            msg = _('Tap flow list can not be retrieved.')
            exceptions.handle(self.request, msg)
        LOG.debug("GET_TAPFLOWS_DATA")

        return tap_flows

    @memoized.memoized_method
    def _get_data(self):
        try:
            tap_service_id = self.kwargs['tap_service_id']
            tap_service = api.taas.show_tap_service(self.request,
                                                    tap_service_id)
        except Exception:
            msg = _('Unable to retrieve details for tap service "%s".') \
                % (tap_service_id)
            exceptions.handle(self.request, msg,
                              redirect=self.get_redirect_url())
        return tap_service

    def get_context_data(self, **kwargs):
        context = super(DetailView, self).get_context_data(**kwargs)
        tap_service = self._get_data()
        context["tap_service"] = tap_service
        table = ts_tables.TapServicesTable(self.request)
        context["url"] = self.get_redirect_url()
        context["actions"] = table.render_row_actions(tap_service)
        LOG.debug("GET_CONTEXT_DATA")
        return context

    @staticmethod
    def get_redirect_url():
        return reverse('horizon:project:tapservices:index')
