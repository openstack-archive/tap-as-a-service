# Copyright (c) 2016 NEC Technologies India Pvt.Limited.
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
#
from neutronclient.common import exceptions
from neutronclient.i18n import _
from neutronclient.neutron import v2_0 as neutronV20
from neutron_taas.taas_client.tap_flow import TapFlow
from neutron_taas.taas_client.tap_service import TapService

TAP_FLOW_RESOURCE = 'tap_flow'
TAP_SERVICE_RESOURCE = 'tap_service'
TAAS_COMMON_PREFIX = "/taas"


def _resolve_resource_path(self, resource):
    """Resolves and returns resource path."""

    if resource == TAP_FLOW_RESOURCE:
        return TapFlow.resource_path
    elif resource == TAP_SERVICE_RESOURCE:
        return TapService.resource_path


def get_object_path(self, resource):
    """Resolves the object path"""

    if resource == TAP_FLOW_RESOURCE:
        return TAAS_COMMON_PREFIX + "/" + TAP_FLOW_RESOURCE + "s"
    elif resource == TAP_SERVICE_RESOURCE:
        return TAAS_COMMON_PREFIX + "/" + TAP_SERVICE_RESOURCE + "s"


def create_taas_resource(self, client, resource, props):
    """Returns created taas resource record."""
    path = _resolve_resource_path(self, resource)
    record = client.create_ext(path, {resource: props})
    return record


def update_taas_resource(self, client, resource, prop_diff, resource_id):
    """Returns updated taas resource record."""

    path = _resolve_resource_path(self, resource)
    return client.update_ext(path + '/%s', resource_id,
                                    {resource: prop_diff})


def delete_taas_resource(self, client, resource, resource_id):
    """Deletes taas resource record and returns status."""

    path = _resolve_resource_path(self, resource)
    return client.delete_ext(path + '/%s', resource_id)


def show_taas_resource(self, client, resource, resource_id):
    """Returns specific taas resource record."""

    path = _resolve_resource_path(self, resource)
    return client.show_ext(path + '/%s', resource_id)


def find_taas_resource(self, client, resource, name_or_id):
    """Returns the id and validate taas resource."""

    path = _resolve_resource_path(self, resource)

    try:
        record = client.show_ext(path + '/%s', name_or_id)
        return record.get(resource).get('id')
    except exceptions.NotFound:
        res_plural = resource + 's'
        record = client.list_ext(collection=res_plural,
                                 path=path, retrieve_all=True)
        record1 = record.get(res_plural)
        rec_chk = []
        for i in range(len(record1)):
            if (record1[i].get('name') == name_or_id):
                rec_chk.append(record1[i].get('id'))
        if len(rec_chk) > 1:
            raise exceptions.NeutronClientNoUniqueMatch(resource=resource,
                                                        name=name_or_id)
        elif len(rec_chk) == 0:
            not_found_message = (_("Unable to find %(resource)s with name "
                                   "or id '%(name_or_id)s'") %
                                 {'resource': resource,
                                  'name_or_id': name_or_id})
            raise exceptions.NotFound(message=not_found_message)
        else:
            return rec_chk[0]


def get_id(client, id_or_name, resource):
    return neutronV20.find_resourceid_by_name_or_id(
        client, resource, str(id_or_name))


def get_client(obj):
    return obj.app.client_manager.neutronclient


def convert_to_uppercase(string):
    return string.upper()


def convert_to_lowercase(string):
    return string.lower()
