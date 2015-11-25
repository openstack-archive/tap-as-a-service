# Copyright 2015 NEC Corporation
# All Rights Reserved
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

from neutronclient.common import extension
from neutronclient.i18n import _
from neutronclient.neutron import v2_0 as neutronv20



def _add_updatable_args(parser):
    parser.add_argument(
        '--name',
        help=_('Name of this Tap service.'))
    parser.add_argument(
        '--description',
        help=_('Description for this Tap service.'))
    parser.add_argument(
        'port_id',
        metavar="PORT",
        help=_('ID of the port to which the Tap service is connected.'))
    parser.add_argument(
        'network_id',
        metavar="NETWORK",
        help=_('Network to which the Tap service is connected.'))


def _updatable_args2body(parsed_args, body, client):
    port_id = neutronv20.find_resourceid_by_name_or_id(
                client, 'port',
                parsed_args.port_id)
    network_id = neutronv20.find_resourceid_by_name_or_id(
                client, 'network',
                parsed_args.network_id)
    neutronv20.update_dict(parsed_args, body, ['tenant_id', 'name',
                           'description'])
    body['port_id'] = port_id
    body['network_id'] = network_id



class TapService(extension.NeutronClientExtension):
    """Define required variables for resource operations."""

    resource = 'tap_service'
    resource_plural = '%ss' % resource
    object_path = '/%s' % resource_plural
    resource_path = '/%s/%%s' % resource_plural
    versions = ['2.0']


class TapServiceList(extension.ClientExtensionList, TapService):
    """List tap services."""

    shell_command = 'tap-service-list'
    list_columns = ['id', 'name', 'port_id']
    pagination_support = True
    sorting_support = True


class TapServiceCreate(extension.ClientExtensionCreate, TapService):
    """Create a tap service."""

    shell_command = 'tap-service-create'
    list_columns = ['id', 'name', 'port_id', 'network_id']

    def add_known_arguments(self, parser):
        _add_updatable_args(parser)

    def args2body(self, parsed_args):
        body = {}
        client = self.get_client()
        _updatable_args2body(parsed_args, body, client)
        return {'tap_service': body}


class TapServiceDelete(extension.ClientExtensionDelete, TapService):
    """Delete a tap service."""

    shell_command = 'tap-service-delete'


class TapServiceShow(extension.ClientExtensionShow, TapService):
    """Show a tap service."""

    shell_command = 'tap-service-show'


'''
If in future, it is required, then simply use this code
class TapServiceUpdate(extension.ClientExtensionUpdate, TapService):
    """Update a tap service."""

    shell_command = 'tap-service-update'
    list_columns = ['id', 'name']

    def add_known_arguments(self, parser):
        # _add_updatable_args(parser)
        parser.add_argument(
            '--name',
            help=_('Name of this tap service.'))

    def args2body(self, parsed_args):
        body = {'name': parsed_args.name}
        return {'tap_service': body}
'''

