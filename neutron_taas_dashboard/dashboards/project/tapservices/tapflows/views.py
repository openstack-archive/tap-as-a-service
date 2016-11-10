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
from neutron_taas_dashboard.dashboards.project.tapservices.tapflows \
    import tables as tf_tables
from neutron_taas_dashboard.dashboards.project.tapservices.tapflows \
    import workflows as tf_workflows


class CreateView(workflows.WorkflowView):
    workflow_class = tf_workflows.CreateTapFlow
    ajax_template_name = 'project/tapservices/tapflows/create.html'

    @memoized.memoized_method
    def get_object(self):
        try:
            tap_service_id = self.kwargs["tap_service_id"]
            tap_service = api.taas.show_tap_service(self.request,
                                                    tap_service_id)
            return tap_service
        except Exception:
            redirect = reverse('horizon:project:tapservices:index')
            msg = _('Unable to retrieve details for tap service "%s".') \
                % (tap_service_id)
            exceptions.handle(self.request, msg, redirect=redirect)

    def get_initial(self):
        return {"tap_service_id": self.kwargs['tap_service_id']}


class DetailView(tables.DataTableView):
    table_class = tf_tables.TapFlowsTable
    template_name = 'project/tapservices/tapflows/detail.html'
    page_title = _("Tap Flow Details: {{ tap_flow.name }}")

    @memoized.memoized_method
    def get_data(self):
        tap_flow_id = self.kwargs['tap_flow_id']

        try:
            tap_flow = api.taas.show_tap_flow(self.request, tap_flow_id)
        except Exception:
            tap_flow = []
            redirect = self.get_redirect_url()
            msg = _('Unable to retrieve details for tap flow \"%s\".') \
                % (tap_flow_id)
            exceptions.handle(self.request, msg, redirect=redirect)

        return tap_flow

    def get_context_data(self, **kwargs):
        context = super(DetailView, self).get_context_data(**kwargs)
        tap_flow = self.get_data()
        context["tap_flow"] = tap_flow
        context["url"] = self.get_redirect_url()
        return context

    def get_tabs(self, request, *args, **kwargs):
        tap_flow = self.get_data()
        return self.tab_group_class(request, tap_flow=tap_flow, **kwargs)

    @staticmethod
    def get_redirect_url():
        return reverse('horizon:project:tapservices:index')
