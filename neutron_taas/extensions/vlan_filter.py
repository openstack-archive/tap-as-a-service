# Copyright (C) 2018 AT&T
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
#

from neutron_lib.api import extensions

# Regex for a comma-seperate list of integer values (VLANs)
# For ex. "9,18,27-36,45-54" or "0-4095" or "9,18,27,36"
RANGE_REGEX = r"^([0-9]+(-[0-9]+)?)(,([0-9]+(-[0-9]+)?))*$"

EXTENDED_ATTRIBUTES_2_0 = {
    'tap_flows': {
        'vlan_filter': {'allow_post': True, 'allow_put': False,
                        'validate': {'type:regex_or_none': RANGE_REGEX},
                        'is_visible': True, 'default': None}
    }
}


class Vlan_filter(extensions.ExtensionDescriptor):
    """Extension class supporting vlan_filter for tap_flows."""

    @classmethod
    def get_name(cls):
        return "TaaS Vlan Filter Extension"

    @classmethod
    def get_alias(cls):
        return 'taas-vlan-filter'

    @classmethod
    def get_description(cls):
        return "Vlan Filter support for Tap Flows."

    @classmethod
    def get_updated(cls):
        return "2019-01-23T00:00:00-00:00"

    def get_extended_resources(self, version):
        if version == "2.0":
            return EXTENDED_ATTRIBUTES_2_0
        return {}

    def get_required_extensions(self):
        return ["taas"]

    def get_optional_extensions(self):
        return []
