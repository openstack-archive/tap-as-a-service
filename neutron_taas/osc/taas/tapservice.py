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
from osc_lib import utils

from neutron_taas._i18n import _
from neutron_taas.osc import common

LOG = logging.getLogger(__name__)

resource = common.TAP_SERVICE_RESOURCE


def _add_updatable_args(parser):
    parser.add_argument(
        '--name',
        help=_('Name of this Tap service.'))
    parser.add_argument(
        '--description',
        help=_('Description for this Tap service.'))


def _get_columns(item):
    return tuple(sorted(list(item.keys())))


def _update_common_attrs(parsed_args, attrs):
    if parsed_args.name:
        attrs['name'] = parsed_args.name
    if parsed_args.description:
        attrs['description'] = parsed_args.description


class CreateTapService(command.ShowOne):
    """Create a tap service."""

    def get_parser(self, prog_name):
        parser = super(CreateTapService, self).get_parser(prog_name)
        _add_updatable_args(parser)
        parser.add_argument(
            'port',
            metavar="PORT",
            help=_('Port to which the Tap service is connected.'))
        return parser

    def take_action(self, parsed_args):
        client = common.get_client(self)
        port_id = common.get_id(
            client,
            'port',
            parsed_args.port)
        attrs = {'port': port_id}
        _update_common_attrs(parsed_args, attrs)
        obj = common.create_taas_resource(self, client, resource, attrs)
        columns = _get_columns(obj[resource])
        data = utils.get_dict_properties(obj[resource], columns)
        return columns, data


class DeleteTapService(command.Command):
    """Delete a tap service."""

    def get_parser(self, prog_name):
        parser = super(DeleteTapService, self).get_parser(prog_name)
        parser.add_argument(
            'tap_service',
            metavar="TAP_SERVICE",
            help=_("ID or name of the Tap Service to be deleted")
        )
        return parser

    def take_action(self, parsed_args):
        client = common.get_client(self)
        id = common.find_taas_resource(self, client, resource,
                                       parsed_args.tap_service)
        common.delete_taas_resource(self, client, resource, id)


class ShowTapService(command.ShowOne):
    """Show information for a tap service."""

    def get_parser(self, prog_name):
        parser = super(ShowTapService, self).get_parser(prog_name)
        parser.add_argument(
            'tap_service',
            metavar="TAP_SERVICE",
            help=_("ID or name of the Tap Service to display")
        )
        return parser

    def take_action(self, parsed_args):
        client = common.get_client(self)
        id = common.find_taas_resource(self, client, resource,
                                       parsed_args.tap_service)
        obj = common.show_taas_resource(self, client, resource, id)
        columns = _get_columns(obj[resource])
        data = utils.get_dict_properties(obj[resource], columns)
        return columns, data


class UpdateTapService(command.Command):
    """Update a tap service."""

    def get_parser(self, prog_name):
        parser = super(UpdateTapService, self).get_parser(prog_name)
        _add_updatable_args(parser)
        parser.add_argument(
            'tap_service',
            metavar="TAP_SERVICE",
            help=_("ID or name of the Tap Service to be updated")
        )
        return parser

    def take_action(self, parsed_args):
        attrs = {}
        client = common.get_client(self)
        id = common.find_taas_resource(self, client, resource,
                                       parsed_args.tap_service)
        _update_common_attrs(parsed_args, attrs)
        common.update_taas_resource(self, client, resource, attrs, id)


class ListTapService(command.Lister):
    """List tap services."""

    def take_action(self, parsed_args):
        data = common.get_client(self).list_ext(
            collection='tap_services', path=common.get_object_path(resource),
            retrieve_all=True)
        list_columns = ['id', 'name', 'port_id', 'status']
        headers = ('ID', 'NAME', 'PORT', 'STATUS')
        return (headers, (utils.get_dict_properties(
                          s, list_columns, ) for s in data['tap_services']))
