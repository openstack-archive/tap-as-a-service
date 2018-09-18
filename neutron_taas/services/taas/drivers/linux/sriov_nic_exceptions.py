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

from neutron_lib import exceptions as qexception

# TaaS SR-IOV driver exception handling classes


class SriovNicSwitchDriverInvocationError(qexception.Invalid):
    message = _("Failed to invoke SR-IOV TaaS driver command: "
                "%(tap_service_pf_device)s, %(tap_service_vf_index)s, "
                "%(source_vf_index)s, %(vlan_filter)s, "
                "%(vf_to_vf_all_vlans)s, %(direction)s")


class PciDeviceNotFoundById(qexception.NotFound):
    message = _("PCI device %(id)s not found")


class PciSlotNotFound(qexception.NotFound):
    message = _("PCI slot (Port-id, MAC): %(port_id)s, %(mac)s not found")
