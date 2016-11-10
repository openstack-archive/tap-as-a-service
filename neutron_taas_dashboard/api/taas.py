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

from __future__ import absolute_import
from django.conf import settings

from openstack_dashboard.api import neutron

import logging

LOG = logging.getLogger(__name__)

neutronclient = neutron.neutronclient


class TapService(neutron.NeutronAPIDictWrapper):
    """Wrapper for neutron tap services."""

    def __init__(self, apiresource):
        super(TapService, self).__init__(apiresource)


class TapFlow(neutron.NeutronAPIDictWrapper):
    """Wrapper for neutron tap flows."""

    def __init__(self, apiresource):
        super(TapFlow, self).__init__(apiresource)


def add_taas_enable():
    network_config = getattr(settings, 'OPENSTACK_NEUTRON_NETWORK', {})

    if not ('enable_taas' in network_config):
        network_config['enable_taas'] = True


def taas_supported(request):
    network_config = getattr(settings, 'OPENSTACK_NEUTRON_NETWORK', {})
    return network_config.get('enable_taas', True)


def tap_service_exist(request):
    res = neutronclient(request).get('/taas/tap_services')

    tap_services = res['tap_services']
    if tap_services:
        return True
    else:
        return False


def is_tapservice(request, port_id):
    res = neutronclient(request).get('/taas/tap_services')

    tap_service_id = ''
    tap_services = res['tap_services']
    for tap_service in tap_services:
        if port_id == tap_service['port_id']:
            tap_service_id = tap_service['id']
            break
    if not tap_service_id == '':
        return True
    else:
        return False


def port_has_tapflow(request, port_id):
    res = neutronclient(request).get("/taas/tap_flows")

    tap_flow_id = ''
    tap_flows = res['tap_flows']
    for tap_flow in tap_flows:
        if port_id == tap_flow['source_port']:
            tap_flow_id = tap_flow['id']
            break
    if not tap_flow_id == '':
        return True
    else:
        return False


def port_has_tapservice(request, port_id):
    res = neutronclient(request).get("/taas/tap_services")

    tap_service_id = ''
    tap_services = res['tap_services']
    for tap_service in tap_services:
        if port_id == tap_service['port_id']:
            tap_service_id = tap_service['id']
            break
    if not tap_service_id == '':
        return True
    else:
        return False


def list_tap_flow(request, tap_service_id):
    LOG.debug("list_tap_flow()")
    tap_flows = neutronclient(request).get("/taas/tap_flows")
    return [TapFlow(tf) for tf in tap_flows.get('tap_flows')]


def show_tap_flow(request, tap_flow_id):
    LOG.debug("tap_flow_show(): tapflowid=%s" % tap_flow_id)
    tap_flow = neutronclient(request).get("/taas/tap_flows/%s" % tap_flow_id)
    return TapFlow(tap_flow.get('tap_flow'))


def create_tap_flow(request, direction, tap_service_id, port_id, **params):
    req_data = {}
    req_data['tap_flow'] = {
        'name': params['name'],
        'description': params['description'],
        'source_port': port_id,
        'direction': direction,
        'tap_service_id': tap_service_id
    }

    res = neutronclient(request).post("/taas/tap_flows", req_data)
    tap_flow = res.get('tap_flow')
    return TapFlow(tap_flow)


def delete_tap_flow(request, tap_flow_id):
    LOG.debug("tap_flow_delete(): tapflowid=%s" % tap_flow_id)
    neutronclient(request).delete("/taas/tap_flows/%s" % tap_flow_id)


def list_tap_service(request):
    LOG.debug("list_tap_service()")
    tap_services = neutronclient(request).get('/taas/tap_services')
    return [TapService(ts) for ts in tap_services.get('tap_services')]


def show_tap_service(request, tap_service_id):
    LOG.debug("tap_service_show(): tapserviceid=%s" % tap_service_id)
    tap_service = neutronclient(request).get('/taas/tap_services/%s' %
                                             tap_service_id)
    return TapService(tap_service.get('tap_service'))


def create_tap_service(request, port_id, **params):
    req_data = {}
    req_data['tap_service'] = {
        'name': params['name'],
        'description': params['description'],
        'port_id': port_id,
    }

    res = neutronclient(request).post("/taas/tap_services", req_data)
    tap_service = res.get('tap_service')
    return TapService(tap_service)


def delete_tap_service(request, tap_service_id):
    LOG.debug("tap_service_delete(): tapserviceid=%s" % tap_service_id)
    neutronclient(request).delete("/taas/tap_services/%s" %
                                  tap_service_id)
