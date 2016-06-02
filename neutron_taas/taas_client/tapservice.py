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

from neutron_taas._i18n import _
from neutronclient.common import extension
from neutronclient.neutron import v2_0 as neutronv20


def _add_updatable_args(parser):
    parser.add_argument(
        '--name',
        help=_('Name of this Tap service.'))
    parser.add_argument(
        '--description',
        help=_('Description for this Tap service.'))


def _updatable_args2body(parsed_args, body):
    neutronv20.update_dict(parsed_args, body, ['name', 'description'])


class TapService(extension.NeutronClientExtension):
    # Define required variables for resource operations.

    resource = 'tap_service'
    resource_plural = '%ss' % resource
    object_path = '/taas/%s' % resource_plural
    resource_path = '/taas/%s/%%s' % resource_plural
    versions = ['2.0']


class ListTapService(extension.ClientExtensionList, TapService):
    """List tap services."""

    shell_command = 'tap-service-list'
    list_columns = ['id', 'name', 'port', 'status']
    pagination_support = True
    sorting_support = True


class CreateTapService(extension.ClientExtensionCreate, TapService):
    """Create a tap service."""

    shell_command = 'tap-service-create'
    list_columns = ['id', 'name', 'port']

    def add_known_arguments(self, parser):
        _add_updatable_args(parser)
        parser.add_argument(
            '--port',
            dest='port_id',
            required=True,
            metavar="PORT",
            help=_('Port to which the Tap service is connected.'))

    def args2body(self, parsed_args):
        client = self.get_client()
        port_id = neutronv20.find_resourceid_by_name_or_id(
            client, 'port',
            parsed_args.port_id)
        body = {'port_id': port_id}
        if parsed_args.tenant_id:
            body['tenant_id'] = parsed_args.tenant_id
        _updatable_args2body(parsed_args, body)
        return {self.resource: body}


class DeleteTapService(extension.ClientExtensionDelete, TapService):
    """Delete a tap service."""

    shell_command = 'tap-service-delete'


class ShowTapService(extension.ClientExtensionShow, TapService):
    """Show a tap service."""

    shell_command = 'tap-service-show'


class UpdateTapService(extension.ClientExtensionUpdate, TapService):
    """Update a tap service."""

    shell_command = 'tap-service-update'
    list_columns = ['id', 'name']

    def add_known_arguments(self, parser):
        _add_updatable_args(parser)

    def args2body(self, parsed_args):
        body = {}
        _updatable_args2body(parsed_args, body)
        return {self.resource: body}
