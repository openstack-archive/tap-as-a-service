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

import json

from django.core.urlresolvers import reverse
from django.http import HttpResponse  # noqa
from django.utils.translation import ugettext_lazy as _

from horizon.utils.lazy_encoder import LazyTranslationEncoder

from neutron_taas_dashboard import api
from neutron_taas_dashboard.dashboards.project.network_topology.tapflows \
    import tables as tf_tables
from neutron_taas_dashboard.dashboards.project.network_topology.tapservices \
    import tables as ts_tables
from neutron_taas_dashboard.dashboards.project.network_topology \
    import utils
from neutron_taas_dashboard.dashboards.project.tapservices \
    import views as ts_views
from neutron_taas_dashboard.dashboards.project.tapservices \
    import workflows as ts_workflows

from openstack_dashboard import api as o_api
from openstack_dashboard.dashboards.project.network_topology \
    import tabs as topology_tabs
from openstack_dashboard.dashboards.project.network_topology \
    import views as nt_views


class NTCreateTapService(ts_workflows.CreateTapService):
    def get_success_url(self):
        return reverse("horizon:project:network_topology:index")

    def get_failure_url(self):
        return reverse("horizon:project:network_topology:index")


class NTCreateTapServiceView(ts_views.CreateView):
    workflow_class = NTCreateTapService


class TapServiceView(ts_views.IndexView):
    table_class = ts_tables.TapServicesTable
    template_name = 'project/network_topology/iframe.html'

    def get_tap_service_data(self):
        pass


class TapFlowView(ts_views.DetailView):
    table_class = tf_tables.TapFlowsTable
    template_name = 'project/network_topology/iframe.html'


class MyNetworkTopologyView(nt_views.NetworkTopologyView):
    tab_group_class = topology_tabs.TopologyTabs
    template_name = 'project/network_topology/index.html'
    page_title = _("Network Topology")

    def get_context_data(self, **kwargs):
        context = super(MyNetworkTopologyView, self).get_context_data(**kwargs)

        return utils.get_context(self.request, context)


class MyJSONView(nt_views.JSONView):
    def _get_servers(self, request):
        old_data = super(MyJSONView, self)._get_servers(request)
        data = []
        try:
            neutron_ports = o_api.neutron.port_list(request)
        except Exception:
            neutron_ports = []

        for server_data_ in old_data:
            port_ids = []
            for port in neutron_ports:
                if port.device_id == server_data_['id']:
                    port_ids.append(port.id)
            tapservice = 'false'
            tapflow = 'false'
            if len(port_ids) > 0:
                for port_id in port_ids:
                    if api.taas.port_has_tapservice(request, port_id):
                        tapservice = 'true'
                    elif api.taas.port_has_tapflow(request, port_id):
                        tapflow = 'true'

            server_data = {'name': server_data_['name'],
                           'status': server_data_['status'],
                           'original_status': server_data_['original_status'],
                           'task': server_data_['task'],
                           'id': server_data_['id'],
                           'tapservice': tapservice,
                           'tapflow': tapflow}

            if server_data_.get('console', None):
                server_data['console'] = server_data_['console']
            data.append(server_data)

        self.add_resource_url('horizon:project:instances:detail', data)
        return data

    def _get_networks(self, request):
        networks = super(MyJSONView, self)._get_networks(request)

        def net_cmp(x, y):
            ext = cmp(x.get('router:external'), y.get('router:external'))
            if ext == 0:
                return cmp(y['name'], x['name'])
            else:
                return ext
        return sorted(networks, cmp=net_cmp, reverse=True)

    def _get_tapservices(self, request):
        try:
            neutron_tapservices = api.taas.list_tap_service(request)
        except Exception:
            neutron_tapservices = []

        tapservices = [{'id': tapservice.id,
                        'name': tapservice.name_or_id,
                        'port_id': tapservice.port_id, }
                       for tapservice in neutron_tapservices]
        self.add_resource_url('horizon:project:tapservices:detail',
                              tapservices)
        return tapservices

    def _get_tapflows(self, request):
        try:
            tap_service_id = []
            neutron_tapflows = api.taas.list_tap_flow(request, tap_service_id)
        except Exception:
            neutron_tapflows = []

        tapflows = [{'id': tapflow.id,
                     'name': tapflow.name_or_id,
                     'port_id': tapflow.source_port,
                     'tap_service_id': tapflow.tap_service_id, }
                    for tapflow in neutron_tapflows]
        self.add_resource_url('horizon:project:tapservices:tapflows:detail',
                              tapflows)
        return tapflows

    def get(self, request, *args, **kwargs):
        networks = self._get_networks(request)
        data = {'servers': self._get_servers(request),
                'tapservices': self._get_tapservices(request),
                'tapflows': self._get_tapflows(request),
                'networks': networks,
                'ports': self._get_ports(request, networks),
                'routers': self._get_routers(request)}
        self._prepare_gateway_ports(data['routers'], data['ports'])
        json_string = json.dumps(data, cls=LazyTranslationEncoder,
                                 ensure_ascii=False)
        return HttpResponse(json_string, content_type='text/json')
