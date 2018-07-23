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


from neutron.agent.linux import utils
from neutron.conf.agent import common
from neutron_taas.services.taas.agents.extensions import taas as taas_base
from neutron_taas.services.taas.drivers.linux.sriov_nic_utils \
    import sriov_nic_utils as taas_sriov_nic_utils
from oslo_config import cfg
from oslo_log import log as logging
from neutron.extensions import portbindings
#from nova.pci import utils as pci_lib
from oslo_utils import excutils
from neutron_taas.extensions import taas

LOG = logging.getLogger(__name__)

TaaS_DRIVER_NAME = 'Taas SRIOV NIC Switch driver'

class SriovNicTaasDriver(taas_base.TaasAgentDriver):
    def __init__(self):
        super(SriovNicTaasDriver, self).__init__()
        LOG.debug("Initializing Taas SRIOV NIC Switch Driver")
        self.agent_api = None
        self.root_helper = common.get_root_helper(cfg.CONF)

    def initialize(self):
        return

    def consume_api(self, agent_api):
        self.agent_api = agent_api

    def create_tap_service(self, tap_service):
        tap_service_port = tap_service['port']
        tap_service_port_mac = tap_service_port['mac_address']

        tap_service_pci_slot = None
        vlan_mirror = None
        if tap_service_port.get(portbindings.PROFILE):
            tap_service_pci_slot = tap_service_port[portbindings.PROFILE].get('pci_slot')
            vlan_mirror = tap_service_port[portbindings.PROFILE].get('vlan_mirror')

        if not tap_service_pci_slot:
            LOG.error("No PCI Slot for port %(id) with MAC %(mac); ",
                      {'id': tap_service_port['id'], 'mac': tap_service_port_mac})
            return

        vf_index = taas_sriov_nic_utils.get_vf_num_by_pci_address(tap_service_pci_slot)
        pf_device = taas_sriov_nic_utils.get_net_name_by_vf_pci_address(tap_service_pci_slot)

        if pf_device and vf_index:
            LOG.debug("TaaS SRIOV Nic Switch Driver: create_tap_service RPC called for port %(id) "
                      "with MAC %(tap_service_port_mac), PCI %(tap_service_pci_slot), "
                      "VF-Index %(vf_index), PF-Device %(pf_device), VLAN-Mirror %(vlan_mirror); ",
                     {'id': tap_service_port['id'], 'tap_service_port_mac': tap_service_port_mac,
                      'tap_service_pci_slot': tap_service_pci_slot,
                      'vf_index': vf_index, 'pf_device': pf_device, 'vlan_mirror': vlan_mirror})

        return

    def delete_tap_service(self, tap_service):
        tap_service_port = tap_service['port']
        tap_service_port_mac = tap_service_port['mac_address']

        tap_service_pci_slot = None
        vlan_mirror = None
        if tap_service_port.get(portbindings.PROFILE):
            tap_service_pci_slot = tap_service_port[portbindings.PROFILE].get('pci_slot')
            vlan_mirror = tap_service_port[portbindings.PROFILE].get('vlan_mirror')

        if not tap_service_pci_slot:
            LOG.error("No PCI Slot for port %(id) with MAC %(mac); ",
                      {'id': tap_service_port['id'], 'mac': tap_service_port_mac})
            return

        vf_index = taas_sriov_nic_utils.get_vf_num_by_pci_address(tap_service_pci_slot)
        pf_device = taas_sriov_nic_utils.get_net_name_by_vf_pci_address(tap_service_pci_slot)

        if pf_device and vf_index:
            LOG.debug("TaaS SRIOV Nic Switch Driver: delete_tap_service RPC called for port %(id) "
                      "with MAC %(tap_service_port_mac), PCI %(tap_service_pci_slot), "
                      "VF-Index %(vf_index), PF-Device %(pf_device), VLAN-Mirror %(vlan_mirror); ",
                      {'id': tap_service_port['id'], 'tap_service_port_mac': tap_service_port_mac,
                       'tap_service_pci_slot': tap_service_pci_slot,
                       'vf_index': vf_index, 'pf_device': pf_device, 'vlan_mirror': vlan_mirror})

        return

    def create_tap_flow(self, tap_flow):
        source_port = tap_flow['port']
        tap_service_port = tap_flow['tap_service_port']
        direction = tap_flow['tap_flow']['direction']
        source_port_mac = source_port['mac_address']
        tap_service_port_mac = tap_service_port['mac_address']
        vf_to_vf_all_vlans = False

        source_pci_slot = None
        tap_service_pci_slot = None
        src_vlans_str = None
        vlan_mirror_str = None

        if source_port.get(portbindings.PROFILE):
            source_pci_slot = source_port[portbindings.PROFILE].get('pci_slot')
            guest_vlans_str = tap_service_port[portbindings.PROFILE].get('guest_vlans')

        if source_port.get(portbindings.VIF_DETAILS):
            src_vlans_str = source_port[portbindings.VIF_DETAILS].get('vlan')

        if src_vlans_str == '0':
            src_vlans_str = guest_vlans_str

        # If no VLAN filter configured on source port, then include all vlans
        if not src_vlans_str:
            src_vlans_str = '0-4095'

        if not source_pci_slot:
            LOG.error("No PCI Slot for source_port %(id)s with MAC %(mac)s; ",
                      {'id': source_port['id'], 'mac': source_port_mac,
                       'source_vlans': src_vlans_str})
            return

        if tap_service_port.get(portbindings.PROFILE):
            tap_service_pci_slot = tap_service_port[portbindings.PROFILE].get('pci_slot')
            vlan_mirror_str = tap_service_port[portbindings.PROFILE].get('vlan_mirror')

        # If no VLAN filter configured on probe port, then include all vlans
        if not vlan_mirror_str:
            vlan_mirror_str = '0-4095'
            vf_to_vf_all_vlans = True
            LOG.debug("VF to VF mirroring for all VLANs. Direction %(direction)",
                      {'Direction': direction})

        if not tap_service_pci_slot:
            LOG.error("No PCI Slot for tap_service_port %(id)s with MAC %(mac)s; ",
                      {'id': tap_service_port['id'], 'mac': tap_service_port_mac,
                       'vlan_mirror': vlan_mirror_str})
            return

        source_vf_index = taas_sriov_nic_utils.get_vf_num_by_pci_address(source_pci_slot)
        source_pf_device = taas_sriov_nic_utils.get_net_name_by_vf_pci_address(source_pci_slot)
        tap_service_vf_index = taas_sriov_nic_utils.get_vf_num_by_pci_address(tap_service_pci_slot)
        tap_service_pf_device = taas_sriov_nic_utils.get_net_name_by_vf_pci_address(tap_service_pci_slot)

        if source_pf_device != tap_service_pf_device:
            LOG.error("SRIOV NIC Driver only supports mirroring b/w VF_src %(VF_src) -> "
                      "VF_probe %(VF_probe) on same PF. PF_src %(PF_src) and "
                      "PF_probe %(PF_probe) are different; ",
                      {'VF_src': source_vf_index, 'VF_probe': tap_service_vf_index,
                       'PF_src': source_pf_device, 'PF_probe': tap_service_pf_device})
            return

        # Fetch common VLAN tags
        src_vlans_list = sorted(set(taas_sriov_nic_utils.get_list_from_ranges_str(src_vlans_str)))
        vlan_mirror_list = \
            sorted(set(taas_sriov_nic_utils.get_list_from_ranges_str(vlan_mirror_str)))

        common_vlans_list = list(set(src_vlans_list).intersection(vlan_mirror_list))
        common_vlans_ranges_str = taas_sriov_nic_utils.get_ranges_str_from_list(common_vlans_list)

        #####################################

        if tap_service_pf_device and tap_service_vf_index and source_vf_index:
            try:
                taas_sriov_nic_utils.execute_sysfs_command('add',
                                                           tap_service_pf_device,
                                                           tap_service_vf_index,
                                                           source_vf_index,
                                                           common_vlans_ranges_str,
                                                           vf_to_vf_all_vlans,
                                                           direction)
            except Exception:
                with excutils.save_and_reraise_exception():
                    raise taas.SriovNicSwitchDriverInvocationError(
                        tap_service_pf_device=tap_service_pf_device,
                        tap_service_vf_index=tap_service_vf_index,
                        source_vf_index=source_vf_index,
                        common_vlans_ranges_str=common_vlans_ranges_str,
                        vf_to_vf_all_vlans=vf_to_vf_all_vlans,
                        direction=direction)
        return

    def delete_tap_flow(self, tap_flow):
        source_port = tap_flow['port']
        tap_service_port = tap_flow['tap_service_port']
        tap_service_port_mac = tap_service_port['mac_address']

        source_pci_slot = None
        vlan_mirror_str = None
        tap_service_pci_slot = None

        if source_port.get(portbindings.PROFILE):
            source_pci_slot = source_port[portbindings.PROFILE].get('pci_slot')

        if tap_service_port.get(portbindings.PROFILE):
            tap_service_pci_slot = tap_service_port[portbindings.PROFILE].get('pci_slot')
            vlan_mirror_str = tap_service_port[portbindings.PROFILE].get('vlan_mirror')

        if not tap_service_pci_slot:
            LOG.error("No PCI Slot for tap_service_port %(id)s with MAC %(mac)s; ",
                      {'id': tap_service_port['id'], 'mac': tap_service_port_mac,
                       'vlan_mirror': vlan_mirror_str})
            return

        source_vf_index = taas_sriov_nic_utils.get_vf_num_by_pci_address(source_pci_slot)
        tap_service_vf_index = taas_sriov_nic_utils.get_vf_num_by_pci_address(tap_service_pci_slot)
        tap_service_pf_device = taas_sriov_nic_utils.get_net_name_by_vf_pci_address(tap_service_pci_slot)

        # Fetch common VLAN tags
        src_vlans_list = []
        for src_vlans_str in tap_flow['src_vlans_list']:
            src_vlans_list.extend(taas_sriov_nic_utils.get_list_from_ranges_str(src_vlans_str))

        src_vlans_list = sorted(set(src_vlans_list))
        vlan_mirror_list = \
            sorted(set(taas_sriov_nic_utils.get_list_from_ranges_str(vlan_mirror_str)))

        common_vlans_list = list(set(src_vlans_list).intersection(vlan_mirror_list))
        common_vlans_ranges_str = taas_sriov_nic_utils.get_ranges_str_from_list(common_vlans_list)

        #####################################
        if tap_service_pf_device and tap_service_vf_index and source_vf_index:
            try:
                taas_sriov_nic_utils.execute_sysfs_command('rem',
                                                           tap_service_pf_device,
                                                           tap_service_vf_index,
                                                           source_vf_index,
                                                           '0-4095',
                                                           False,
                                                           'BOTH')
            except Exception:
                with excutils.save_and_reraise_exception():
                    raise taas.SriovNicSwitchDriverInvocationError(
                        tap_service_pf_device=tap_service_pf_device,
                        tap_service_vf_index=tap_service_vf_index,
                        source_vf_index=source_vf_index,
                        common_vlans_ranges_str='0-4095',
                        vf_to_vf_all_vlans=vf_to_vf_all_vlans,
                        direction=direction)

            try:
                taas_sriov_nic_utils.execute_sysfs_command('add',
                                                           tap_service_pf_device,
                                                           tap_service_vf_index,
                                                           source_vf_index,
                                                           common_vlans_ranges_str,
                                                           False,
                                                           'BOTH')
            except Exception:
                with excutils.save_and_reraise_exception():
                    raise taas.SriovNicSwitchDriverInvocationError(
                        tap_service_pf_device=tap_service_pf_device,
                        tap_service_vf_index=tap_service_vf_index,
                        source_vf_index=source_vf_index,
                        common_vlans_ranges_str=common_vlans_ranges_str,
                        vf_to_vf_all_vlans=vf_to_vf_all_vlans,
                        direction=direction)

        return
