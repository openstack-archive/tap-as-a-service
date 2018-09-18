# Copyright (C) 2018 AT&T
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
from neutronclient.common import utils
from neutronclient.neutron import v2_0 as neutronv20


def _add_updatable_args(parser):
    parser.add_argument(
        '--name',
        help=_('Name of this Tap flow.'))
    parser.add_argument(
        '--description',
        help=_('Description for this Tap flow.'))


def _updatable_args2body(parsed_args, body):
    neutronv20.update_dict(parsed_args, body, ['name', 'description'])


class TapFlow(extension.NeutronClientExtension):
    # Define required variables for resource operations.

    resource = 'tap_flow'
    resource_plural = '%ss' % resource
    object_path = '/taas/%s' % resource_plural
    resource_path = '/taas/%s/%%s' % resource_plural
    versions = ['2.0']


class ListTapFlow(extension.ClientExtensionList, TapFlow):
    """List tap flows."""

    shell_command = 'tap-flow-list'
    list_columns = ['id', 'name', 'source_port', 'tap_service_id', 'status',
                    'vlan_filter']
    pagination_support = True
    sorting_support = True


class CreateTapFlow(extension.ClientExtensionCreate, TapFlow):
    """Create a tap flow."""

    shell_command = 'tap-flow-create'
    list_columns = ['id', 'name', 'direction', 'source_port']

    def add_known_arguments(self, parser):
        _add_updatable_args(parser)
        parser.add_argument(
            '--port',
            required=True,
            metavar="SOURCE_PORT",
            help=_('Source port to which the Tap Flow is connected.'))
        parser.add_argument(
            '--tap-service',
            required=True,
            metavar="TAP_SERVICE",
            help=_('Tap Service to which the Tap Flow belongs.'))
        parser.add_argument(
            '--direction',
            required=True,
            metavar="DIRECTION",
            choices=['IN', 'OUT', 'BOTH'],
            type=utils.convert_to_uppercase,
            help=_('Direction of the Tap flow.'))
        parser.add_argument(
            '--vlan-filter',
            required=False,
            metavar="VLAN_FILTER",
            help=_('VLAN Ids to be mirrored in the form of range string.'))

    def args2body(self, parsed_args):
        client = self.get_client()
        source_port = neutronv20.find_resourceid_by_name_or_id(
            client, 'port',
            parsed_args.port)
        tap_service_id = neutronv20.find_resourceid_by_name_or_id(
            client, 'tap_service',
            parsed_args.tap_service)
        body = {'source_port': source_port,
                'tap_service_id': tap_service_id}
        neutronv20.update_dict(parsed_args, body, ['tenant_id', 'direction',
                                                   'vlan_filter'])
        _updatable_args2body(parsed_args, body)
        return {self.resource: body}


class DeleteTapFlow(extension.ClientExtensionDelete, TapFlow):
    """Delete a tap flow."""

    shell_command = 'tap-flow-delete'


class ShowTapFlow(extension.ClientExtensionShow, TapFlow):
    """Show a tap flow."""

    shell_command = 'tap-flow-show'


class UpdateTapFlow(extension.ClientExtensionUpdate, TapFlow):
    """Update a tap flow."""

    shell_command = 'tap-flow-update'
    list_columns = ['id', 'name']

    def add_known_arguments(self, parser):
        _add_updatable_args(parser)

    def args2body(self, parsed_args):
        body = {}
        _updatable_args2body(parsed_args, body)
        return {self.resource: body}
