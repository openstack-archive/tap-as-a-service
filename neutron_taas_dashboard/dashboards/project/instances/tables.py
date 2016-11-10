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

from django.core import urlresolvers
from django.core.urlresolvers import reverse
from django.http import HttpResponse  # noqa
from django.utils.http import urlencode
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import messages
from horizon import tables

from openstack_dashboard import api as o_api
from openstack_dashboard.dashboards.project.instances \
    import tables as i_tables
from openstack_dashboard import policy

from neutron_taas_dashboard import api
from neutron_taas_dashboard.dashboards.project.tapservices.tapflows \
    import workflows

from neutron_taas_dashboard.api import taas


class DeleteInstance(i_tables.DeleteInstance):
    def action(self, request, obj_id):
        # Guard process for when there is a tapservice and tapflow,
        # do not delete the instance
        if not taas.taas_supported(request):
            o_api.nova.server_delete(request, obj_id)
        else:
            try:
                tap_services_pre = taas.list_tap_service(request)
                tap_flows_pre = taas.list_tap_flow(request, [])
                instance_id = obj_id
                tap_services = []
                for tap_service in tap_services_pre:
                    tap_service_port_id = tap_service['port_id']
                    s_port_info = o_api.neutron.port_get(request,
                                                         tap_service_port_id,)
                    if s_port_info.device_id == instance_id:
                        tap_services = tap_services + [tap_service]
                tap_flows = []
                for tap_flow in tap_flows_pre:
                    tap_flow_port_id = tap_flow['source_port']
                    f_port_info = o_api.neutron.port_get(request,
                                                         tap_flow_port_id,)
                    if f_port_info.device_id == instance_id:
                        tap_flows = tap_flows + [tap_flow]
                if len(tap_services) == 0 and len(tap_flows) == 0:
                    o_api.nova.server_delete(request, obj_id)
                else:
                    raise exceptions.NotAvailable()
            except Exception:
                msg = _('There are one or more tap services'
                        ' or tap flows still connected to the instance.')
                messages.error(request, msg)
                redirect = urlresolvers.reverse("horizon:project"
                                                ":instances:index")
                exceptions.handle(request, msg, redirect=redirect)


class CreateVirtualTap(policy.PolicyTargetMixin, tables.LinkAction):
    name = "createtapflow"
    verbose_name = _("Create Tap Flow")
    url = "horizon:project:instances:createtapflow"
    classes = ("ajax-modal",)
    icon = "pencil"
    policy_rules = (("network", "create_tap_flow"),)

    def get_link_url(self, project):
        return self._get_link_url(project, 'instance_info')

    def _get_link_url(self, project, step_slug):
        base_url = reverse(self.url, args=[project.id])
        next_url = self.table.get_full_url()
        params = {"step": step_slug,
                  workflows.CreateTapFlow.redirect_param_name: next_url}
        param = urlencode(params)
        return "?".join([base_url, param])

    def allowed(self, request, instance):
        if not o_api.neutron.is_service_enabled(request,
                                                config_name='enable_taas',
                                                ext_name='taas'):
            return False
        if not api.taas.tap_service_exist(request):
            return False
        if instance.status == "ERROR":
            return False
        instance_id = instance.id
        ports_all = o_api.neutron.port_list(request,)
        ports_instance = []
        for port in ports_all:
            if port.device_id == instance_id:
                ports_instance = ports_instance + [port]
        for port in ports_instance:
            port_id = port.id
            if api.taas.is_tapservice(request, port_id):
                return False
        return not i_tables.is_deleting(instance)


class DeleteVirtualTap(policy.PolicyTargetMixin, tables.LinkAction):
    name = "deletetapflow"
    verbose_name = _("Delete Tap Flow")
    url = "horizon:project:instances:deletetapflow"
    classes = ("btn-danger",)
    policy_rules = (("network", "delete_tap_flow"),)

    def allowed(self, request, instance):
        if not o_api.neutron.is_service_enabled(request,
                                                config_name='enable_taas',
                                                ext_name='taas'):
            return False
        if not api.taas.tap_service_exist(request):
            return False
        instance_id = instance.id
        ports_all = o_api.neutron.port_list(request,)
        ports_instance = []
        for port in ports_all:
            if port.device_id == instance_id:
                ports_instance = ports_instance + [port]
        for port in ports_instance:
            port_id = port.id
            if api.taas.is_tapservice(request, port_id):
                return False
            if api.taas.port_has_tapflow(request, port_id):
                return True
        return False
