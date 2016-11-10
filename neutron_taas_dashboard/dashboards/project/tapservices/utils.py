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

from django.utils.translation import ugettext_lazy as _
import six

from horizon import exceptions

from neutron_taas_dashboard import api

from openstack_dashboard import api as o_api

LOG = logging.getLogger(__name__)


def port_field_data(request, instance_id=None, include_empty_option=False):
    """Returns a list of tuples of all ports.

    Generates a list of ports available to the user (request). And returns
    a list of (id, name) tuples.

    :param request: django http request object
    :param include_empty_option: flag to include a empty tuple in the front of
    the list
    :return: list of (id, name) tuples
    """
    ports = []
    try:
        ports_pre = o_api.neutron.port_list(request,)
        for port in ports_pre:
            if not instance_id or port.device_id == instance_id:
                ports = ports + [port]
        ports = [(n.id, n) for n in ports]
        ports.sort(key=lambda obj: obj[1].name_or_id)
    except Exception as e:
        msg = _('Failed to get port list {0}').format(six.text_type(e))
        exceptions.handle(request, msg)

    if not ports:
        if include_empty_option:
            return [("", _("No ports available")), ]
        return []

    if include_empty_option:
        return [("", _("Select Port")), ] + ports
    return ports


def tap_service_field_data(request, include_empty_option=False):
    tap_services = []
    try:
        tap_services = api.taas.list_tap_service(request)
        tap_services = [(n.id, n) for n in tap_services]
        tap_services.sort(key=lambda obj: obj[1])
    except Exception as e:
        msg = _('Failed to get tap service list {0}').format(six.text_type(e))
        exceptions.handle(request, msg)

    if not tap_services:
        if include_empty_option:
            return [("", _("No tap services available")), ]
        return []

    if include_empty_option:
        return [("", _("Select Tap Service")), ] + tap_services
    return tap_services
