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
from horizon import tabs

from neutron_taas_dashboard.api import taas
from neutron_taas_dashboard.dashboards.project.instances.tapflows \
    import tables as tapf_tables

from openstack_dashboard import api
from openstack_dashboard.dashboards.project.instances \
    import tabs as i_tabs

import logging
LOG = logging.getLogger(__name__)


class OverviewTab(tabs.TableTab):
    table_classes = (tapf_tables.TapFlowsTable,)
    name = _("Overview")
    slug = "overview"
    template_name = ("project/instances/"
                     "_taas_detail_overview.html")

    def get_context_data(self, request):
        context = super(OverviewTab, self).get_context_data(request)
        if taas.taas_supported(request):
            context["tap_flow"] = self._get_tapflow_data()
            context["tapflows_table"] = self._get_tapflow_data()
            context["instance"] = self.tab_group.kwargs['instance']
            context["is_superuser"] = request.user.is_superuser
            context["is_taas"] = True
        else:
            context["instance"] = self.tab_group.kwargs['instance']
            context["is_superuser"] = request.user.is_superuser
            context["is_taas"] = False
        return context

    def get_tapflows_data(self):
        tap_flow = self._get_tapflow_data()
        return tap_flow

    def _get_tapflow_data(self):
        try:
            instance = self.tab_group.kwargs['instance']
            instance_id = instance.id
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
            msg = _('Tap flow list can not be retrieved.')
            exceptions.handle(self.request, msg)
        return tap_flows


class InstanceDetailTabs(i_tabs.InstanceDetailTabs):
    tabs = (OverviewTab, i_tabs.LogTab, i_tabs.ConsoleTab, i_tabs.AuditTab)
