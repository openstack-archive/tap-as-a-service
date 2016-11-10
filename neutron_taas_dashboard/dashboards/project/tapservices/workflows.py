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

import logging

from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.debug import sensitive_variables

from horizon import exceptions
from horizon import forms
from horizon import workflows

from neutron_taas_dashboard import api
from neutron_taas_dashboard.dashboards.project.tapservices \
    import utils as ts_utils

from openstack_dashboard import api as o_api

LOG = logging.getLogger(__name__)


class CreateTapInfoAction(workflows.Action):
    tap_service_name = forms.CharField(max_length=255,
                                       label=_("Tap Service Name"),
                                       required=False)
    description = forms.CharField(max_length=255, label=_("Description"),
                                  required=False)

    class Meta(object):
        name = _("Tap Service")
        help_text = _("Create a new tap service.")


class CreateTapInfo(workflows.Step):
    action_class = CreateTapInfoAction
    contributes = ("tap_service_name", "description")


class CreateTapDetailAction(workflows.Action):
    port = forms.ChoiceField(label=_("Ports"),
                             help_text=_("Create tap service with"
                                         " this port"),
                             widget=forms.SelectWidget(
                             transform=lambda
                                 x: ("%s (%s) %s" %
                                     (x.name,
                                      x.id,
                                      x["fixed_ips"][0]["ip_address"]))))

    def __init__(self, request, *args, **kwargs):
        super(CreateTapDetailAction, self).__init__(request, *args, **kwargs)
        port_list = self.fields["port"].choices
        if len(port_list) == 1:
            self.fields['port'].initial = [port_list[0][0]]
        if o_api.neutron.is_port_profiles_supported():
            self.fields['profile'].choices = (
                self.get_policy_profile_choices(request))

    class Meta(object):
        name = _("Port")
        permissions = ('openstack.services.network',)
        help_text = _("Select port for your tap service.")

    def populate_port_choices(self, request, context):
        return ts_utils.port_field_data(request)


class CreateTapDetail(workflows.Step):
    action_class = CreateTapDetailAction
    contributes = ("port",)


class CreateTapService(workflows.Workflow):
    slug = "create_tapservice"
    name = _("Create Tap Service")
    finalize_button_name = _("Create")
    success_message = _('Created tap service "%s".')
    failure_message = _('Unable to create tap service "%s".')
    default_steps = (CreateTapInfo,
                     CreateTapDetail)
    wizard = True

    def get_success_url(self):
        return reverse("horizon:project:tapservices:index")

    def get_failure_url(self):
        return reverse("horizon:project:tapservices:index")

    def format_status_message(self, message):
        name = self.context.get('tap_service_name') or \
            self.context.get('tap_service_id', '')
        return message % name

    def _create_tap_service(self, request, data):
        try:
            params = {'name': data['tap_service_name'],
                      'description': data['description']}
            port_id = data['port']
            tap_service = api.taas.create_tap_service(request,
                                                      port_id,
                                                      **params)
            self.context['tap_service_id'] = tap_service.id
            return True
        except Exception:
            exceptions.handle(request)
            return False

    @sensitive_variables('context')
    def handle(self, request, context):
        tap_service = self._create_tap_service(request, context)
        if not tap_service:
            return False
        else:
            return True
