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


def convert_to_upper_case(srcstr):
    return srcstr.upper()

def _add_updatable_args(parser):
    parser.add_argument(
        '--name',
        help=_('Name of this Tap flow.'))
    parser.add_argument(
        '--description',
        help=_('Description for this Tap flow.'))
    parser.add_argument(
        '--source_port',
        required=True,
        metavar="SOURCE-PORT",
        help=_('ID of the source port to which the Tap Flow is connected.'))
    parser.add_argument(
        '--service_id',
        required=True,
        metavar="SERVICE",
        help=_('Tap Service to which the flow belogs.'))
    parser.add_argument(
        '--direction',
        required=True,
        metavar="DIRECTION",
        choices=['IN', 'OUT', 'BOTH'],
        type=convert_to_upper_case,
        help=_('Direction of the Tap flow .'))


def _updatable_args2body(parsed_args, body, client):
    source_port = neutronv20.find_resourceid_by_name_or_id(
                client, 'port',
                parsed_args.source_port)
    service_id = neutronv20.find_resourceid_by_name_or_id(
                client, 'tap-service',
                parsed_args.service_id)
    neutronv20.update_dict(parsed_args, body, ['tenant_id', 'name',
                           'description','direction'])
    body['source_port'] = source_port
    body['tap_service_id'] = service_id



class TapFlow(extension.NeutronClientExtension):
    """Define required variables for resource operations."""

    resource = 'tap-flow'
    resource_plural = '%ss' % resource
    object_path = '/taas/%s' % resource_plural
    resource_path = '/taas/%s/%%s' % resource_plural
    versions = ['2.0']


class ListTapFlow(extension.ClientExtensionList, TapFlow):
    """List tap flows."""

    shell_command = 'tap-flow-list'
    list_columns = ['id', 'name','source_port', 'tap_service_id']
    pagination_support = True
    sorting_support = True


class CreateTapFlow(extension.ClientExtensionCreate, TapFlow):
    """Create a tap flow."""

    shell_command = 'tap-flow-create'
    list_columns = ['id', 'name', 'direction', 'source_port']

    def add_known_arguments(self, parser):
        _add_updatable_args(parser)

    def args2body(self, parsed_args):
        body = {}
        client = self.get_client()
        _updatable_args2body(parsed_args, body, client)
        return {'tap_flow': body}


class DeleteTapFlow(extension.ClientExtensionDelete, TapFlow):
    """Delete a tap flow."""

    shell_command = 'tap-flow-delete'


class ShowTapFlow(extension.ClientExtensionShow, TapFlow):
    """Show a tap flow."""

    shell_command = 'tap-flow-show'


'''
If in future, it is required, then simply use this code
class TapFlowUpdate(extension.ClientExtensionUpdate, TapFlow):
    """Update a tap flow."""

    shell_command = 'tap-flow-update'
    list_columns = ['id', 'name']

    def add_known_arguments(self, parser):
        # _add_updatable_args(parser)
        parser.add_argument(
            '--name',
            help=_('Name of this tap flow.'))

    def args2body(self, parsed_args):
        body = {'name': parsed_args.name}
        return {'tap_flow': body}
'''

