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
from django.views.decorators.debug import sensitive_variables

from horizon import exceptions
from horizon import forms
from horizon import workflows

from neutron_taas_dashboard import api

from neutron_taas_dashboard.dashboards.project.tapservices \
    import utils as ts_utils


class CreateTapFlowInfoAction(workflows.Action):
    tap_flow_name = forms.CharField(max_length=255,
                                    label=_("Tap Flow Name"),
                                    required=False)
    description = forms.CharField(max_length=255,
                                  label=_("Description"),
                                  required=False)
    direction = forms.ChoiceField(choices=[('BOTH', _('Both')),
                                           ('IN', _('Ingress')),
                                           ('OUT', _('Egress'))],
                                  label=_("Direction"),
                                  help_text=_("Whether to mirror the traffic"
                                              " leaving or ariving"
                                              " at the source port."))

    class Meta(object):
        name = _("Information")
        slug = 'instance_info'
        help_text = _("Create a new tap flow.")


class CreateTapFlowInfo(workflows.Step):
    action_class = CreateTapFlowInfoAction
    contributes = ("tap_flow_name", "description", "direction")


class SelectTapServiceAction(workflows.Action):
    tap_service = forms.ChoiceField(label=_("Tap Service"),
                                    help_text=_("Create tap flow with"
                                                " this tap service"),
                                    widget=forms.SelectWidget(
                                    transform=lambda x: ("%s (%s)" % (x.name,
                                                                      x.id))))

    def __init__(self, request, *args, **kwargs):
        super(SelectTapServiceAction, self).__init__(request, *args, **kwargs)
        tap_service_list = self.fields["tap_service"].choices
        if len(tap_service_list) == 1:
            self.fields['tap_service'].initial = [tap_service_list[0][0]]

    class Meta(object):
        name = _("Tap Service")
        permissions = ('openstack.services.network',)
        help_text = _("Select tap service for your tap flow.")

    def populate_tap_service_choices(self, request, context):
        return ts_utils.tap_service_field_data(request)


class SelectTapService(workflows.Step):
    action_class = SelectTapServiceAction
    contributes = ("tap_service",)


class SelectPortAction(workflows.Action):
    port = forms.ChoiceField(label=_("Port"),
                             help_text=_("Create tap flow with"
                                         " this port"),
                             widget=forms.SelectWidget(
                                 transform=lambda
                                 x: ("%s (%s) %s" %
                                     (x.name,
                                      x.id,
                                      x["fixed_ips"][0]["ip_address"]))))

    def __init__(self, request, *args, **kwargs):
        super(SelectPortAction, self).__init__(request, *args, **kwargs)
        port_list = self.fields["port"].choices
        if len(port_list) == 1:
            self.fields['port'].initial = [port_list[0][0]]

    class Meta(object):
        name = _("Port")
        permissions = ('openstack.services.network',)
        help_text = _("Select port for your tap flow.")

    def populate_port_choices(self, request, context):
        instance_id = context['instance_id']
        return ts_utils.port_field_data(request, instance_id)


class SelectPort(workflows.Step):
    action_class = SelectPortAction
    depends_on = ("instance_id",)
    contributes = ("port",)


class CreateTapFlow(workflows.Workflow):
    slug = "create_tapflow"
    name = _("Create Tap Flow")
    finalize_button_name = _("Create")
    success_message = _('Created tap flow "%s".')
    failure_message = _('Unable to create tap flow "%s".')
    default_steps = (CreateTapFlowInfo,
                     SelectTapService,
                     SelectPort,)
    wizard = True

    def get_success_url(self):
        return reverse("horizon:project:network_topology:index")

    def get_failure_url(self):
        return reverse("horizon:project:network_topology:index")

    def format_status_message(self, message):
        name = self.context.get('tap_flow_name') or \
            self.context.get('tap_flow_id', '')
        return message % name

    def _create_tap_flow(self, request, data):
        try:
            params = {'name': data['tap_flow_name'],
                      'description': data['description']}
            direction = data['direction']
            tap_service_id = data['tap_service']
            port_id = data['port']
            tap_flow = api.taas.create_tap_flow(request,
                                                direction,
                                                tap_service_id,
                                                port_id,
                                                **params)
            self.context['tap_flow_id'] = tap_flow.id
            return True
        except Exception:
            exceptions.handle(request)
            return False

    @sensitive_variables('context')
    def handle(self, request, context):
        tap_flow = self._create_tap_flow(request, context)
        if not tap_flow:
            return False
        else:
            return True
