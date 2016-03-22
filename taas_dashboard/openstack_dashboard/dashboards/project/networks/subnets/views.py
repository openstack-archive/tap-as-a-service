# Copyright 2012 NEC Corporation
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

"""
Views for managing Neutron Subnets.
"""
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import tabs
from horizon.utils import memoized
from horizon import workflows

from openstack_dashboard import api

from openstack_dashboard.dashboards.project.networks.subnets \
    import tables as project_tables
from openstack_dashboard.dashboards.project.networks.subnets \
    import tabs as project_tabs
from openstack_dashboard.dashboards.project.networks.subnets import utils
from openstack_dashboard.dashboards.project.networks.subnets \
    import workflows as project_workflows


class CreateView(workflows.WorkflowView):
    workflow_class = project_workflows.CreateSubnet

    @memoized.memoized_method
    def get_object(self):
        try:
            network_id = self.kwargs["network_id"]
            network = api.neutron.network_get(self.request, network_id)
            return network
        except Exception:
            redirect = reverse('horizon:project:networks:index')
            msg = _("Unable to retrieve network.")
            exceptions.handle(self.request, msg, redirect=redirect)

    def get_initial(self):
        network = self.get_object()
        return {"network_id": self.kwargs['network_id'],
                "network_name": network.name_or_id}


class UpdateView(workflows.WorkflowView):
    workflow_class = project_workflows.UpdateSubnet

    @memoized.memoized_method
    def _get_object(self, *args, **kwargs):
        subnet_id = self.kwargs['subnet_id']
        try:
            return api.neutron.subnet_get(self.request, subnet_id)
        except Exception:
            redirect = reverse("horizon:project:networks:index")
            msg = _('Unable to retrieve subnet details')
            exceptions.handle(self.request, msg, redirect=redirect)

    def get_initial(self):
        initial = super(UpdateView, self).get_initial()

        subnet = self._get_object()

        initial['network_id'] = self.kwargs['network_id']
        initial['subnet_id'] = subnet['id']
        initial['subnet_name'] = subnet['name']

        for key in ('cidr', 'ip_version', 'enable_dhcp'):
            initial[key] = subnet[key]

        initial['gateway_ip'] = subnet['gateway_ip'] or ''
        initial['no_gateway'] = (subnet['gateway_ip'] is None)

        if initial['ip_version'] == 6:
            initial['ipv6_modes'] = utils.get_ipv6_modes_menu_from_attrs(
                subnet['ipv6_ra_mode'], subnet['ipv6_address_mode'])

        initial['dns_nameservers'] = '\n'.join(subnet['dns_nameservers'])
        pools = ['%s,%s' % (p['start'], p['end'])
                 for p in subnet['allocation_pools']]
        initial['allocation_pools'] = '\n'.join(pools)
        routes = ['%s,%s' % (r['destination'], r['nexthop'])
                  for r in subnet['host_routes']]
        initial['host_routes'] = '\n'.join(routes)

        return initial


class DetailView(tabs.TabView):
    tab_group_class = project_tabs.SubnetDetailTabs
    template_name = 'project/networks/subnets/detail.html'
    page_title = _("Subnet Details")

    @memoized.memoized_method
    def get_data(self):
        subnet_id = self.kwargs['subnet_id']
        try:
            subnet = api.neutron.subnet_get(self.request, subnet_id)
        except Exception:
            subnet = []
            msg = _('Unable to retrieve subnet details.')
            exceptions.handle(self.request, msg,
                              redirect=self.get_redirect_url())
        else:
            if subnet.ip_version == 6:
                ipv6_modes = utils.get_ipv6_modes_menu_from_attrs(
                    subnet.ipv6_ra_mode, subnet.ipv6_address_mode)
                subnet.ipv6_modes_desc = utils.IPV6_MODE_MAP.get(ipv6_modes)

        return subnet

    def get_context_data(self, **kwargs):
        context = super(DetailView, self).get_context_data(**kwargs)
        subnet = self.get_data()
        table = project_tables.SubnetsTable(self.request,
                                            network_id=subnet.network_id)
        context["subnet"] = subnet
        context["url"] = self.get_redirect_url()
        context["actions"] = table.render_row_actions(subnet)
        return context

    def get_tabs(self, request, *args, **kwargs):
        subnet = self.get_data()
        return self.tab_group_class(request, subnet=subnet, **kwargs)

    @staticmethod
    def get_redirect_url():
        return reverse('horizon:project:networks:index')
