# Copyright 2012 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
#
# Copyright 2012 Nebula, Inc.
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
from django.core.urlresolvers import reverse_lazy
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import forms
from horizon import tables
from horizon.utils import memoized
from horizon import workflows

from openstack_dashboard import api

from openstack_dashboard.dashboards.admin.flavors \
    import forms as project_forms
from openstack_dashboard.dashboards.admin.flavors \
    import tables as project_tables
from openstack_dashboard.dashboards.admin.flavors \
    import workflows as flavor_workflows


INDEX_URL = "horizon:admin:flavors:index"


class IndexView(tables.DataTableView):
    table_class = project_tables.FlavorsTable
    template_name = 'admin/flavors/index.html'
    page_title = _("Flavors")

    def get_data(self):
        request = self.request
        flavors = []
        try:
            # "is_public=None" will return all flavors.
            flavors = api.nova.flavor_list(request, None)
        except Exception:
            exceptions.handle(request,
                              _('Unable to retrieve flavor list.'))
        # Sort flavors by size
        flavors.sort(key=lambda f: (f.vcpus, f.ram, f.disk))
        return flavors


class CreateView(workflows.WorkflowView):
    workflow_class = flavor_workflows.CreateFlavor
    template_name = 'admin/flavors/create.html'
    page_title = _("Create Flavor")


class UpdateView(workflows.WorkflowView):
    workflow_class = flavor_workflows.UpdateFlavor
    template_name = 'admin/flavors/update.html'
    page_title = _("Edit Flavor")

    def get_initial(self):
        flavor_id = self.kwargs['id']

        try:
            # Get initial flavor information
            flavor = api.nova.flavor_get(self.request, flavor_id)
        except Exception:
            exceptions.handle(self.request,
                              _('Unable to retrieve flavor details.'),
                              redirect=reverse_lazy(INDEX_URL))
        return {'flavor_id': flavor.id,
                'name': flavor.name,
                'vcpus': flavor.vcpus,
                'memory_mb': flavor.ram,
                'disk_gb': flavor.disk,
                'swap_mb': flavor.swap or 0,
                'eph_gb': getattr(flavor, 'OS-FLV-EXT-DATA:ephemeral', None)}


class UpdateMetadataView(forms.ModalFormView):
    template_name = "admin/flavors/update_metadata.html"
    form_class = project_forms.UpdateMetadataForm
    success_url = reverse_lazy('horizon:admin:flavors:index')
    page_title = _("Update Flavor Metadata")

    def get_initial(self):
        extra_specs_dict = self.get_object()
        return {'id': self.kwargs["id"], 'metadata': extra_specs_dict}

    def get_context_data(self, **kwargs):
        context = super(UpdateMetadataView, self).get_context_data(**kwargs)

        extra_specs_dict = self.get_object()

        context['existing_metadata'] = json.dumps(extra_specs_dict)

        resource_type = 'OS::Nova::Flavor'

        namespaces = []
        try:
            # metadefs_namespace_list() returns a tuple with list as 1st elem
            namespaces = [
                api.glance.metadefs_namespace_get(self.request, x.namespace,
                                                  resource_type)
                for x in api.glance.metadefs_namespace_list(
                    self.request,
                    filters={'resource_types': [resource_type]}
                )[0]
            ]

        except Exception:
            msg = _('Unable to retrieve available metadata for flavors.')
            exceptions.handle(self.request, msg)

        context['available_metadata'] = json.dumps({'namespaces': namespaces})
        context['id'] = self.kwargs['id']
        return context

    @memoized.memoized_method
    def get_object(self):
        flavor_id = self.kwargs['id']
        try:
            extra_specs = api.nova.flavor_get_extras(self.request, flavor_id)
            return dict((i.key, i.value) for i in extra_specs)
        except Exception:
            msg = _('Unable to retrieve the flavor metadata.')
            exceptions.handle(self.request, msg,
                              redirect=reverse(INDEX_URL))
