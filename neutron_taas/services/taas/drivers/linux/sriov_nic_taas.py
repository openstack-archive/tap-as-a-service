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


from neutron.conf.agent import common
from neutron_taas.services.taas.agents.extensions import taas as taas_base
from neutron_taas.services.taas.drivers.linux \
    import sriov_nic_constants as taas_sriov_consts
from neutron_taas.services.taas.drivers.linux.sriov_nic_utils \
    import SriovNicUtils as sriov_utils
from oslo_config import cfg
from oslo_log import log as logging
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
        ts_port = tap_service['port']

        LOG.debug("SRIOV Driver: Inside create_tap_service: "
                  "Port-id: %(port_id)s",
                  {'port_id': ts_port['id']})

        port_params = sriov_utils.get_sriov_port_params(ts_port)

        if port_params['pf_device'] and port_params['vf_index']:
            LOG.debug("TaaS SRIOV: create_tap_service RPC invoked for "
                      "port %(id)s, MAC %(ts_port_mac)s, PCI %(ts_pci_slot)s, "
                      "VF-Index %(vf_index)s, PF-Device %(pf_device)s, "
                      "VLAN-Mirror %(vlan_mirror)s; ",
                      {'id': ts_port['id'],
                       'ts_port_mac': port_params['mac'],
                       'ts_pci_slot': port_params['pci_slot'],
                       'vf_index': port_params['vf_index'],
                       'pf_device': port_params['pf_device'],
                       'vlan_mirror': port_params['vlan_mirror']})

        return

    def delete_tap_service(self, tap_service):
        ts_port = tap_service['port']

        LOG.debug("SRIOV Driver: Inside delete_tap_service: "
                  "Port-id: %(port_id)s",
                  {'port_id': ts_port['id']})

        port_params = sriov_utils.get_sriov_port_params(ts_port)

        if port_params['pf_device'] and port_params['vf_index']:
            LOG.debug("TaaS SRIOV: delete_tap_service RPC invoked for "
                      "port %(id)s, MAC %(ts_port_mac)s, PCI %(ts_pci_slot)s, "
                      "VF-Index %(vf_index)s, PF-Device %(pf_device)s, "
                      "VLAN-Mirror %(vlan_mirror)s; ",
                      {'id': ts_port['id'],
                       'ts_port_mac': port_params['mac'],
                       'ts_pci_slot': port_params['pci_slot'],
                       'vf_index': port_params['vf_index'],
                       'pf_device': port_params['pf_device'],
                       'vlan_mirror': port_params['vlan_mirror']})

        return

    def create_tap_flow(self, tap_flow):
        source_port = tap_flow['port']
        ts_port = tap_flow['tap_service_port']
        direction = tap_flow['tap_flow']['direction']
        vf_to_vf_all_vlans = False

        LOG.debug("SRIOV Driver: Inside create_tap_flow: "
                  "SRC Port-id: %(src_port_id)s, "
                  "DEST Port-id: %(dest_port_id)s "
                  "Direction: %(direction)s",
                  {'src_port_id': source_port['id'],
                   'dest_port_id': ts_port['id'],
                   'direction': direction})

        src_port_params = sriov_utils.get_sriov_port_params(source_port)
        ts_port_params = sriov_utils.get_sriov_port_params(ts_port)

        # If no VLAN filter configured on source port, then include all vlans
        if not src_port_params['src_vlans']:
            src_port_params['src_vlans'] = taas_sriov_consts.VLAN_RANGE

        # If no VLAN filter configured on probe port, then include all vlans
        if not ts_port_params['vlan_mirror']:
            ts_port_params['vlan_mirror'] = taas_sriov_consts.VLAN_RANGE
            vf_to_vf_all_vlans = True
            LOG.debug("VF to VF mirroring for all VLANs. "
                      "Direction %(direction)",
                      {'Direction': direction})

        if not src_port_params['pci_slot']:
            LOG.error("No PCI Slot for source_port %(id)s with MAC %(mac)s; ",
                      {'id': source_port['id'],
                       'mac': src_port_params['mac'],
                       'source_vlans': src_port_params['src_vlans']})
            raise taas.PciSlotNotFound(port_id=source_port['id'],
                                       mac=src_port_params['mac'])

        if not ts_port_params['pci_slot']:
            LOG.error("No PCI Slot for ts_port %(id)s with MAC %(mac)s; ",
                      {'id': ts_port['id'], 'mac': ts_port_params['mac'],
                       'vlan_mirror': ts_port_params['vlan_mirror']})
            raise taas.PciSlotNotFound(port_id=ts_port['id'],
                                       mac=ts_port_params['mac'])

        if src_port_params['pf_device'] != ts_port_params['pf_device']:
            LOG.error("SRIOV NIC Driver only supports mirroring b/w "
                      "VF_src %(VF_src) -> VF_probe %(VF_probe) on same PF. "
                      "PF_src %(PF_src) and PF_probe %(PF_probe) "
                      "are different; ",
                      {'VF_src': src_port_params['vf_index'],
                       'VF_probe': ts_port_params['vf_index'],
                       'PF_src': src_port_params['pf_device'],
                       'PF_probe': ts_port_params['pf_device']})
            return

        # Fetch common VLAN tags
        src_vlans_list = sorted(set(sriov_utils.get_list_from_ranges_str(
            src_port_params['src_vlans'])))
        vlan_mirror_list = sorted(set(sriov_utils.get_list_from_ranges_str(
            ts_port_params['vlan_mirror'])))

        common_vlans_list = list(set(src_vlans_list).intersection(
            vlan_mirror_list))
        common_vlans_ranges_str = sriov_utils.get_ranges_str_from_list(
            common_vlans_list)

        if ts_port_params['pf_device'] and \
                ts_port_params['vf_index'] and \
                src_port_params['vf_index']:
            try:
                sriov_utils.execute_sysfs_command('add',
                                                  ts_port_params,
                                                  src_port_params,
                                                  common_vlans_ranges_str,
                                                  vf_to_vf_all_vlans,
                                                  direction)
            except Exception:
                with excutils.save_and_reraise_exception():
                    raise taas.SriovNicSwitchDriverInvocationError(
                        ts_pf_dev=ts_port_params['pf_device'],
                        ts_vf_index=ts_port_params['vf_index'],
                        source_vf_index=src_port_params['vf_index'],
                        common_vlans_ranges_str=common_vlans_ranges_str,
                        vf_to_vf_all_vlans=vf_to_vf_all_vlans,
                        direction=direction)
        return

    def delete_tap_flow(self, tap_flow):
        source_port = tap_flow['port']
        ts_port = tap_flow['tap_service_port']
        direction = tap_flow['tap_flow']['direction']

        LOG.debug("SRIOV Driver: Inside delete_tap_flow: "
                  "SRC Port-id: %(src_port_id)s, "
                  "DEST Port-id: %(dest_port_id)s "
                  "Direction: %(direction)s",
                  {'src_port_id': source_port['id'],
                   'dest_port_id': ts_port['id'],
                   'direction': direction})

        src_port_params = sriov_utils.get_sriov_port_params(source_port)
        ts_port_params = sriov_utils.get_sriov_port_params(ts_port)

        # If no VLAN filter configured on source port, then include all vlans
        if not src_port_params['src_vlans']:
            src_port_params['src_vlans'] = taas_sriov_consts.VLAN_RANGE

        # If no VLAN filter configured on probe port, then include all vlans
        if not ts_port_params['vlan_mirror']:
            ts_port_params['vlan_mirror'] = taas_sriov_consts.VLAN_RANGE
            vf_to_vf_all_vlans = True
            LOG.debug("VF to VF mirroring for all VLANs. "
                      "Direction %(direction)",
                      {'Direction': direction})

        if not src_port_params['pci_slot']:
            LOG.error("No PCI Slot for source_port %(id)s with MAC %(mac)s; ",
                      {'id': source_port['id'],
                       'mac': src_port_params['mac'],
                       'source_vlans': src_port_params['src_vlans']})
            raise taas.PciSlotNotFound(port_id=source_port['id'],
                                       mac=src_port_params['mac'])

        if not ts_port_params['pci_slot']:
            LOG.error("No PCI Slot for ts_port %(id)s with MAC %(mac)s; ",
                      {'id': ts_port['id'], 'mac': ts_port_params['mac'],
                       'vlan_mirror': ts_port_params['vlan_mirror']})
            raise taas.PciSlotNotFound(port_id=ts_port['id'],
                                       mac=ts_port_params['mac'])

        # Fetch common VLAN tags
        src_vlans_list = []
        for src_vlans_str in tap_flow['src_vlans_list']:
            src_vlans_list.extend(sriov_utils.get_list_from_ranges_str(
                src_vlans_str))

        src_vlans_list = sorted(set(src_vlans_list))
        vlan_mirror_list = sorted(set(sriov_utils.get_list_from_ranges_str(
            ts_port_params['vlan_mirror'])))

        common_vlans_list = \
            list(set(src_vlans_list).intersection(vlan_mirror_list))
        common_vlans_ranges_str = \
            sriov_utils.get_ranges_str_from_list(common_vlans_list)

        if ts_port_params['pf_device'] and \
                ts_port_params['vf_index'] and \
                src_port_params['vf_index']:
            try:
                sriov_utils.execute_sysfs_command('rem',
                                                  ts_port_params,
                                                  src_port_params,
                                                  taas_sriov_consts.VLAN_RANGE,
                                                  False,
                                                  'BOTH')
            except Exception:
                with excutils.save_and_reraise_exception():
                    raise taas.SriovNicSwitchDriverInvocationError(
                        ts_pf_dev=ts_port_params['pf_device'],
                        ts_vf_index=ts_port_params['vf_index'],
                        source_vf_index=src_port_params['vf_index'],
                        common_vlans_ranges_str=taas_sriov_consts.VLAN_RANGE,
                        vf_to_vf_all_vlans=vf_to_vf_all_vlans,
                        direction=direction)

            try:
                sriov_utils.execute_sysfs_command('add',
                                                  ts_port_params['pf_device'],
                                                  ts_port_params['vf_index'],
                                                  src_port_params['vf_index'],
                                                  common_vlans_ranges_str,
                                                  False,
                                                  'BOTH')
            except Exception:
                with excutils.save_and_reraise_exception():
                    raise taas.SriovNicSwitchDriverInvocationError(
                        ts_pf_dev=ts_port_params['pf_device'],
                        ts_vf_index=ts_port_params['vf_index'],
                        source_vf_index=src_port_params['vf_index'],
                        common_vlans_ranges_str=common_vlans_ranges_str,
                        vf_to_vf_all_vlans=vf_to_vf_all_vlans,
                        direction=direction)

        return
