# Copyright (c) 2016 NEC Technologies India Pvt.Limited.
# All Rights Reserved.
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

from osc_lib.command import command
from osc_lib import exceptions
from osc_lib import utils

from neutron_taas._i18n import _
from neutron_taas.osc import common

LOG = logging.getLogger(__name__)

resource = common.TAP_FLOW_RESOURCE


def _add_updatable_args(parser):
    parser.add_argument(
        '--name',
        help=_('Name of the Tap flow.'))
    parser.add_argument(
        '--description',
        help=_('Description for the Tap flow.'))


def _get_columns(item):
    return tuple(sorted(list(item.keys())))


def _update_common_attrs(parsed_args, attrs):
    if parsed_args.name:
        attrs['name'] = parsed_args.name
    if parsed_args.description:
        attrs['description'] = parsed_args.description


class CreateTapFlow(command.ShowOne):
    """Create a new tap flow"""

    def get_parser(self, prog_name):
        parser = super(CreateTapFlow, self).get_parser(prog_name)
        _add_updatable_args(parser)
        parser.add_argument(
            'port',
            help=_('Source port to which the Tap Flow is connected '
                   '(name or ID)'))
        parser.add_argument(
            'tap-service',
            help=_('Tap Service with which the tapflow is associated '
                   '(name or ID)'))
        parser.add_argument(
            '--direction',
            required=True,
            choices=['IN', 'OUT', 'BOTH'],
            type=common.convert_to_uppercase,
            help=_('Direction of the packet flow which needs to be mirrored '
                   'by the tapflow'))
        return parser

    def take_action(self, parsed_args):
        client = common.get_client(self)
        source_port = common.get_id(
            client,
            'port',
            parsed_args.port)
        tap_service_id = common.find_taas_resource(
            client, 'tap_service',
            parsed_args.tap_service)
        attrs = {'source_port': source_port,
                 'tap_service_id': tap_service_id}
        _update_common_attrs(parsed_args, attrs)
        if parsed_args.direction:
            attrs['direction'] = parsed_args.direction
        obj = common.create_taas_resource(self, client, resource, attrs)
        columns = _get_columns(obj[resource])
        data = utils.get_dict_properties(obj[resource], columns)
        return columns, data


class DeleteTapFlow(command.Command):
    """Delete tap flow(s)"""

    def get_parser(self, prog_name):
        parser = super(DeleteTapFlow, self).get_parser(prog_name)
        parser.add_argument(
            'tap_flow',
            nargs='+',
            help=_("Tap Flow to delete (name or ID)")
        )
        return parser

    def take_action(self, parsed_args):
        result = 0
        client = common.get_client(self)
        for tap_flow in parsed_args.tap_flow:
            try:
                id = common.find_taas_resource(self, client, resource,
                                               tap_flow)
                common.delete_taas_resource(self, client, resource, id)
            except Exception as e:
                result += 1
                LOG.error(_("Failed to delete tap flow with "
                            "name or ID '%(flow)s': %(e)s"),
                          {'flow': tap_flow, 'e': e})

        if result > 0:
            total = len(parsed_args.tap_flow)
            msg = (_("%(result)s of %(total)s tap flows were failed "
                   "to be deleted.") % {'result': result, 'total': total})
            raise exceptions.CommandError(msg)


class ShowTapFlow(command.ShowOne):
    """Display tap flow details"""

    def get_parser(self, prog_name):
        parser = super(ShowTapFlow, self).get_parser(prog_name)
        parser.add_argument(
            'tap_flow',
            help=_("ID or name of the Tap Flow to display")
        )
        return parser

    def take_action(self, parsed_args):
        client = common.get_client(self)
        id = common.find_taas_resource(self, client, resource,
                                       parsed_args.tap_flow)
        obj = common.show_taas_resource(self, client, resource, id)
        columns = _get_columns(obj[resource])
        data = utils.get_dict_properties(obj[resource], columns)
        return columns, data


class SetTapFlow(command.Command):
    """Set tap flow properties"""

    def get_parser(self, prog_name):
        parser = super(SetTapFlow, self).get_parser(prog_name)
        _add_updatable_args(parser)
        parser.add_argument(
            'tap_flow',
            help=_("Tap Flow to modify (name or ID)")
        )
        return parser

    def take_action(self, parsed_args):
        attrs = {}
        client = common.get_client(self)
        id = common.find_taas_resource(self, client, resource,
                                       parsed_args.tap_flow)
        _update_common_attrs(parsed_args, attrs)
        common.update_taas_resource(self, client, resource, attrs, id)


class ListTapFlow(command.Lister):
    """List tap flows"""

    def take_action(self, parsed_args):
        path = common.get_object_path(resource)
        data = common.get_client(self).list_ext(
            collection='tap_flows', path=path,
            retrieve_all=True)
        columns = ['id', 'name', 'source_port', 'status', 'tap_service_id']
        headers = ('ID', 'NAME', 'SOURCE PORT', 'STATUS', 'TAP SERVICE')
        return (headers, (utils.get_dict_properties(
                          s, columns, ) for s in data['tap_flows']))
