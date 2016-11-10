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

from horizon import exceptions
from horizon import tables
from horizon.utils import memoized
from horizon import workflows

from neutron_taas_dashboard.api import taas
from neutron_taas_dashboard.dashboards.project.instances \
    import tabs as tap_tabs
from neutron_taas_dashboard.dashboards.project.instances.tapflows \
    import tables as tf_tables
from neutron_taas_dashboard.dashboards.project.instances \
    import workflows as project_workflows

from openstack_dashboard import api
from openstack_dashboard.dashboards.project.instances \
    import views as project_view

import logging
LOG = logging.getLogger(__name__)


class DetailView(project_view.DetailView):
    tab_group_class = tap_tabs.InstanceDetailTabs


class CreateTapFlowView(workflows.WorkflowView):
    workflow_class = project_workflows.CreateTapFlow
    ajax_template_name = 'project/instances/tapflows/create.html'

    def get_workflow(self):
        extra_context = self.kwargs
        entry_point = self.request.GET.get("step", None)
        workflow = self.workflow_class(self.request,
                                       context_seed=extra_context,
                                       entry_point=entry_point,)
        return workflow


class DeleteTapFlowView(tables.DataTableView):
    table_class = tf_tables.DeleteTapFlowTable
    template_name = 'project/instances/tapflows/detail.html'
    page_title = _("Delete Tap Flows")

    @memoized.memoized_method
    def get_data(self):

        try:
            instance_id = self.kwargs['instance_id']
            tap_service_id = []
            tap_flows_pre = taas.list_tap_flow(self.request, tap_service_id)
            tap_flows = []
            for tap_flow in tap_flows_pre:
                tap_flow_port_id = tap_flow['source_port']
                tap_flow_port_info = api.neutron.port_get(self.request,
                                                          tap_flow_port_id,)
                if tap_flow_port_info.device_id == instance_id:
                    tap_flows = tap_flows + [tap_flow]
        except Exception:
            tap_flows = []
            msg = _('Unable to retrieve subnet details.')
            exceptions.handle(self.request, msg)

        return tap_flows
