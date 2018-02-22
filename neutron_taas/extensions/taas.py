# Copyright (C) 2015 Ericsson AB
# Copyright (c) 2015 Gigamon
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import abc

from neutron_lib.api import extensions
from neutron_lib import exceptions as qexception
from neutron_lib.services import base as service_base

from neutron.api.v2 import resource_helper

from neutron_taas._i18n import _
from neutron_taas.common import constants

from oslo_config import cfg

import six

# TaaS exception handling classes


class TapServiceNotFound(qexception.NotFound):
    message = _("Tap Service  %(tap_id)s does not exist")


class TapFlowNotFound(qexception.NotFound):
    message = _("Tap Flow  %(flow_id)s does not exist")


class InvalidDestinationPort(qexception.NotFound):
    message = _("Destination Port %(port)s does not exist")


class InvalidSourcePort(qexception.NotFound):
    message = _("Source Port  %(port)s does not exist")


class PortDoesNotBelongToTenant(qexception.NotAuthorized):
    message = _("The specified port does not belong to the tenant")


class TapServiceNotBelongToTenant(qexception.NotAuthorized):
    message = _("Specified Tap Service does not belong to the tenant")


class TapServiceLimitReached(qexception.OverQuota):
    message = _("Reached the maximum quota for Tap Services")


direction_enum = ['IN', 'OUT', 'BOTH']


'''
Resource Attribute Map:

Note:

'tap_services' data model refers to the Tap Service created.
port_id specifies destination port to which the mirrored data is sent.
'''

RESOURCE_ATTRIBUTE_MAP = {
    'tap_services': {
        'id': {'allow_post': False, 'allow_put': False,
               'validate': {'type:uuid': None}, 'is_visible': True,
               'primary_key': True},
        'tenant_id': {'allow_post': True, 'allow_put': False,
                      'validate': {'type:string': None},
                      'required_by_policy': True, 'is_visible': True},
        'name': {'allow_post': True, 'allow_put': True,
                 'validate': {'type:string': None},
                 'is_visible': True, 'default': ''},
        'description': {'allow_post': True, 'allow_put': True,
                        'validate': {'type:string': None},
                        'is_visible': True, 'default': ''},
        'port_id': {'allow_post': True, 'allow_put': False,
                    'validate': {'type:uuid': None},
                    'is_visible': True},
        'status': {'allow_post': False, 'allow_put': False,
                   'is_visible': True}
    },
    'tap_flows': {
        'id': {'allow_post': False, 'allow_put': False,
               'validate': {'type:uuid': None}, 'is_visible': True,
               'primary_key': True},
        'tenant_id': {'allow_post': True, 'allow_put': False,
                      'validate': {'type:string': None},
                      'required_by_policy': True, 'is_visible': True},
        'name': {'allow_post': True, 'allow_put': True,
                 'validate': {'type:string': None},
                 'is_visible': True, 'default': ''},
        'description': {'allow_post': True, 'allow_put': True,
                        'validate': {'type:string': None},
                        'is_visible': True, 'default': ''},
        'tap_service_id': {'allow_post': True, 'allow_put': False,
                           'validate': {'type:uuid': None},
                           'required_by_policy': True, 'is_visible': True},
        'source_port': {'allow_post': True, 'allow_put': False,
                        'validate': {'type:uuid': None},
                        'required_by_policy': True, 'is_visible': True},
        'direction': {'allow_post': True, 'allow_put': False,
                      'validate': {'type:values': direction_enum},
                      'is_visible': True},
        'status': {'allow_post': False, 'allow_put': False,
                   'is_visible': True}
    }
}


taas_quota_opts = [
    cfg.IntOpt('quota_tap_service',
               default=1,
               help=_('Number of Tap Service instances allowed per tenant')),
    cfg.IntOpt('quota_tap_flow',
               default=10,
               help=_('Number of Tap flows allowed per tenant'))
]
cfg.CONF.register_opts(taas_quota_opts, 'QUOTAS')


TaasOpts = [
    cfg.StrOpt(
        'driver',
        default='',
        help=_("Name of the TaaS Driver")),
    cfg.BoolOpt(
        'enabled',
        default=False,
        help=_("Enable TaaS")),
    cfg.IntOpt(
        'vlan_range_start',
        default=3900,
        help=_("Starting range of TAAS VLAN IDs")),
    cfg.IntOpt(
        'vlan_range_end',
        default=4000,
        help=_("End range of TAAS VLAN IDs")),
]
cfg.CONF.register_opts(TaasOpts, 'taas')


class Taas(extensions.ExtensionDescriptor):
    @classmethod
    def get_name(cls):
        return "Neutron Tap as a Service"

    @classmethod
    def get_alias(cls):
        return "taas"

    @classmethod
    def get_description(cls):
        return "Neutron Tap as a Service Extension."

    @classmethod
    def get_updated(cls):
        return "2015-01-14T10:00:00-00:00"

    @classmethod
    def get_plugin_interface(cls):
        return TaasPluginBase

    @classmethod
    def get_resources(cls):
        """Returns Ext Resources."""
        plural_mappings = resource_helper.build_plural_mappings(
            {}, RESOURCE_ATTRIBUTE_MAP)

        return resource_helper.build_resource_info(plural_mappings,
                                                   RESOURCE_ATTRIBUTE_MAP,
                                                   constants.TAAS,
                                                   translate_name=False,
                                                   allow_bulk=True)

    def update_attributes_map(self, attributes):
        super(Taas, self).update_attributes_map(
            attributes, extension_attrs_map=RESOURCE_ATTRIBUTE_MAP)

    def get_extended_resources(self, version):
        if version == "2.0":
            return RESOURCE_ATTRIBUTE_MAP
        else:
            return {}


@six.add_metaclass(abc.ABCMeta)
class TaasPluginBase(service_base.ServicePluginBase):
    def get_plugin_name(self):
        return constants.TAAS

    def get_plugin_description(self):
        return "Tap Service Plugin"

    @classmethod
    def get_plugin_type(cls):
        return constants.TAAS

    @abc.abstractmethod
    def create_tap_service(self, context, tap_service):
        """Create a Tap Service."""
        pass

    @abc.abstractmethod
    def delete_tap_service(self, context, id):
        """Delete a Tap Service."""
        pass

    @abc.abstractmethod
    def get_tap_service(self, context, id, fields=None):
        """Get a Tap Service."""
        pass

    @abc.abstractmethod
    def get_tap_services(self, context, filters=None, fields=None,
                         sorts=None, limit=None, marker=None,
                         page_reverse=False):
        """List all Tap Services."""
        pass

    @abc.abstractmethod
    def update_tap_service(self, context, id, tap_service):
        """Update a Tap Service."""
        pass

    @abc.abstractmethod
    def create_tap_flow(self, context, tap_flow):
        """Create a Tap Flow."""
        pass

    @abc.abstractmethod
    def get_tap_flow(self, context, id, fields=None):
        """Get a Tap Flow."""
        pass

    @abc.abstractmethod
    def delete_tap_flow(self, context, id):
        """Delete a Tap Flow."""
        pass

    @abc.abstractmethod
    def get_tap_flows(self, context, filters=None, fields=None,
                      sorts=None, limit=None, marker=None,
                      page_reverse=False):
        """List all Tap Flows."""
        pass

    @abc.abstractmethod
    def update_tap_flow(self, context, id, tap_flow):
        """Update a Tap Flow."""
        pass
