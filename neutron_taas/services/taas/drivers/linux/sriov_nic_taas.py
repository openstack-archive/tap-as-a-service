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
from neutron_taas.common import constants as taas_consts
from neutron_taas.common import utils as common_utils
from neutron_taas.services.taas.agents.extensions import taas as taas_base
from neutron_taas.services.taas.drivers.linux import sriov_nic_exceptions \
    as taas_exc
from neutron_taas.services.taas.drivers.linux import sriov_nic_utils \
    as sriov_utils

from oslo_config import cfg
from oslo_log import log as logging
from oslo_utils import excutils
import threading

LOG = logging.getLogger(__name__)

TaaS_DRIVER_NAME = 'Taas SRIOV NIC Switch driver'


class SriovNicTaasDriver(taas_base.TaasAgentDriver):
    def __init__(self):
        super(SriovNicTaasDriver, self).__init__()
        LOG.debug("Initializing Taas SRIOV NIC Switch Driver")
        self.agent_api = None
        self.root_helper = common.get_root_helper(cfg.CONF)
        self.lock = threading.Lock()

    def initialize(self):
        LOG.debug("Initialize routine called for Taas SRIOV NIC Switch Driver")
        self.sriov_utils = sriov_utils.SriovNicUtils()
        return

    def consume_api(self, agent_api):
        self.agent_api = agent_api

    def create_tap_service(self, tap_service):
        ts_port = tap_service['port']

        LOG.debug("SRIOV Driver: Inside create_tap_service: "
                  "Port-id: %(port_id)s",
                  {'port_id': ts_port['id']})

        port_params = self.sriov_utils.get_sriov_port_params(ts_port)

        LOG.info("TaaS SRIOV: create_tap_service RPC invoked for "
                 "port %(id)s, MAC %(ts_port_mac)s, PCI %(ts_pci_slot)s, "
                 "VF-Index %(vf_index)s, PF-Device %(pf_device)s, "
                 "src_vlans %(src_vlans)s; ",
                 {'id': ts_port['id'],
                  'ts_port_mac': port_params['mac'],
                  'ts_pci_slot': port_params['pci_slot'],
                  'vf_index': port_params['vf_index'],
                  'pf_device': port_params['pf_device'],
                  'src_vlans': port_params['src_vlans']})

        return

    def delete_tap_service(self, tap_service):
        ts_port = tap_service['port']

        LOG.debug("SRIOV Driver: Inside delete_tap_service: "
                  "Port-id: %(port_id)s",
                  {'port_id': ts_port['id']})

        port_params = self.sriov_utils.get_sriov_port_params(ts_port)

        LOG.info("TaaS SRIOV: delete_tap_service RPC invoked for "
                 "port %(id)s, MAC %(ts_port_mac)s, PCI %(ts_pci_slot)s, "
                 "VF-Index %(vf_index)s, PF-Device %(pf_device)s, "
                 "src_vlans %(src_vlans)s; ",
                 {'id': ts_port['id'],
                  'ts_port_mac': port_params['mac'],
                  'ts_pci_slot': port_params['pci_slot'],
                  'vf_index': port_params['vf_index'],
                  'pf_device': port_params['pf_device'],
                  'src_vlans': port_params['src_vlans']})

        return

    def create_tap_flow(self, tap_flow):
        source_port = tap_flow['port']
        ts_port = tap_flow['tap_service_port']
        direction = tap_flow['tap_flow']['direction']
        vlan_filter = tap_flow['tap_flow']['vlan_filter']
        vf_to_vf_all_vlans = False

        LOG.debug("SRIOV Driver: Inside create_tap_flow: "
                  "SRC Port-id: %(src_port_id)s, "
                  "DEST Port-id: %(dest_port_id)s "
                  "Direction: %(direction)s",
                  {'src_port_id': source_port['id'],
                   'dest_port_id': ts_port['id'],
                   'direction': direction})

        src_port_params = self.sriov_utils.get_sriov_port_params(source_port)
        ts_port_params = self.sriov_utils.get_sriov_port_params(ts_port)

        LOG.info("TaaS src_port_params "
                 "port %(id)s, MAC %(port_mac)s, PCI %(pci_slot)s, "
                 "VF-Index %(vf_index)s, PF-Device %(pf_device)s, "
                 "src_vlans %(src_vlans)s; ",
                 {'id': source_port['id'],
                  'port_mac': src_port_params['mac'],
                  'pci_slot': src_port_params['pci_slot'],
                  'vf_index': src_port_params['vf_index'],
                  'pf_device': src_port_params['pf_device'],
                  'src_vlans': src_port_params['src_vlans']})

        LOG.info("TaaS ts_port_params "
                 "port %(id)s, MAC %(port_mac)s, PCI %(pci_slot)s, "
                 "VF-Index %(vf_index)s, PF-Device %(pf_device)s, "
                 "VLAN-Filter %(vlan_filter)s, src_vlans %(src_vlans)s; ",
                 {'id': ts_port['id'],
                  'port_mac': ts_port_params['mac'],
                  'pci_slot': ts_port_params['pci_slot'],
                  'vf_index': ts_port_params['vf_index'],
                  'pf_device': ts_port_params['pf_device'],
                  'vlan_filter': vlan_filter,
                  'src_vlans': ts_port_params['src_vlans']})

        # If no VLAN filter configured on source port, then include all vlans
        if not src_port_params['src_vlans'] or \
                src_port_params['src_vlans'] == '0':
            src_port_params['src_vlans'] = taas_consts.VLAN_RANGE
            LOG.debug("TaaS no src_vlans in src_port")

        # If no VLAN filter configured on probe port, then include all vlans
        if not vlan_filter:
            vlan_filter = taas_consts.VLAN_RANGE
            vf_to_vf_all_vlans = True
            LOG.debug("VF to VF mirroring for all VLANs. "
                      "Direction %(direction)s",
                      {'direction': direction})

        if not src_port_params['pci_slot']:
            LOG.error("No PCI Slot for source_port %(id)s with MAC %(mac)s; ",
                      {'id': source_port['id'],
                       'mac': src_port_params['mac'],
                       'source_vlans': src_port_params['src_vlans']})
            raise taas_exc.PciSlotNotFound(port_id=source_port['id'],
                                           mac=src_port_params['mac'])

        if not ts_port_params['pci_slot']:
            LOG.error("No PCI Slot for ts_port %(id)s with MAC %(mac)s; ",
                      {'id': ts_port['id'], 'mac': ts_port_params['mac'],
                       'vlan_filter': vlan_filter})
            raise taas_exc.PciSlotNotFound(port_id=ts_port['id'],
                                           mac=ts_port_params['mac'])

        if src_port_params['pf_device'] != ts_port_params['pf_device']:
            LOG.error("SRIOV NIC Driver only supports mirroring b/w "
                      "VF_src %(VF_src)s -> VF_probe %(VF_probe)s on same PF. "
                      "PF_src %(PF_src)s and PF_probe %(PF_probe)s "
                      "are different; ",
                      {'VF_src': src_port_params['vf_index'],
                       'VF_probe': ts_port_params['vf_index'],
                       'PF_src': src_port_params['pf_device'],
                       'PF_probe': ts_port_params['pf_device']})
            return

        # Fetch common VLAN tags
        src_vlans_list = sorted(set(common_utils.get_list_from_ranges_str(
            src_port_params['src_vlans'])))
        vlan_filter_list = sorted(set(
            common_utils.get_list_from_ranges_str(vlan_filter)))

        common_vlans_list = list(set(src_vlans_list).intersection(
            vlan_filter_list))
        common_vlans_rng_str = common_utils.get_ranges_str_from_list(
            common_vlans_list)

        LOG.info("TaaS src_vlans_list %(src_vlans_list)s, "
                 "vlan_filter_list %(vlan_filter_list)s, "
                 "common_vlans_list %(common_vlans_list)s, "
                 "common_vlans_rng_str %(common_vlans_rng_str)s; ",
                 {'src_vlans_list': src_vlans_list,
                  'vlan_filter_list': vlan_filter_list,
                  'common_vlans_list': common_vlans_list,
                  'common_vlans_rng_str': common_vlans_rng_str})

        if ts_port_params['pf_device'] and \
                ts_port_params['vf_index'] and \
                src_port_params['vf_index']:
            with self.lock:
                try:
                    LOG.info("TaaS invoking execute_sysfs_command")
                    self.sriov_utils.execute_sysfs_command(
                        'add',
                        ts_port_params,
                        src_port_params,
                        common_vlans_rng_str,
                        vf_to_vf_all_vlans,
                        direction)
                except Exception:
                    LOG.error("TaaS error in invoking execute_sysfs_command")
                    with excutils.save_and_reraise_exception():
                        raise taas_exc.SriovNicSwitchDriverInvocationError(
                            ts_pf_dev=ts_port_params['pf_device'],
                            ts_vf_index=ts_port_params['vf_index'],
                            source_vf_index=src_port_params['vf_index'],
                            common_vlans_rng_str=common_vlans_rng_str,
                            vf_to_vf_all_vlans=vf_to_vf_all_vlans,
                            direction=direction)
        return

    def delete_tap_flow(self, tap_flow):
        source_port = tap_flow['port']
        ts_port = tap_flow['tap_service_port']
        vlan_filter = tap_flow['tap_flow']['vlan_filter']
        direction = tap_flow['tap_flow']['direction']

        LOG.debug("SRIOV Driver: Inside delete_tap_flow: "
                  "SRC Port-id: %(src_port_id)s, "
                  "DEST Port-id: %(dest_port_id)s "
                  "Direction: %(direction)s",
                  {'src_port_id': source_port['id'],
                   'dest_port_id': ts_port['id'],
                   'direction': direction})

        src_port_params = self.sriov_utils.get_sriov_port_params(source_port)
        ts_port_params = self.sriov_utils.get_sriov_port_params(ts_port)

        LOG.info("TaaS src_port_params "
                 "port %(id)s, MAC %(port_mac)s, PCI %(pci_slot)s, "
                 "VF-Index %(vf_index)s, PF-Device %(pf_device)s, "
                 "src_vlans %(src_vlans)s; ",
                 {'id': source_port['id'],
                  'port_mac': src_port_params['mac'],
                  'pci_slot': src_port_params['pci_slot'],
                  'vf_index': src_port_params['vf_index'],
                  'pf_device': src_port_params['pf_device'],
                  'src_vlans': src_port_params['src_vlans']})

        LOG.info("TaaS ts_port_params "
                 "port %(id)s, MAC %(port_mac)s, PCI %(pci_slot)s, "
                 "VF-Index %(vf_index)s, PF-Device %(pf_device)s, "
                 "VLAN-Filter %(vlan_filter)s, src_vlans %(src_vlans)s; ",
                 {'id': ts_port['id'],
                  'port_mac': ts_port_params['mac'],
                  'pci_slot': ts_port_params['pci_slot'],
                  'vf_index': ts_port_params['vf_index'],
                  'pf_device': ts_port_params['pf_device'],
                  'vlan_filter': vlan_filter,
                  'src_vlans': ts_port_params['src_vlans']})

        # If no VLAN filter configured on source port, then include all vlans
        if not src_port_params['src_vlans']:
            src_port_params['src_vlans'] = taas_consts.VLAN_RANGE
            LOG.debug("TaaS no src_vlans in src_port")

        # If no VLAN filter configured on probe port, then include all vlans
        if not vlan_filter:
            vf_to_vf_all_vlans = True
            LOG.debug("VF to VF mirroring for all VLANs. "
                      "Direction %(direction)s",
                      {'direction': direction})

        if not src_port_params['pci_slot']:
            LOG.error("No PCI Slot for source_port %(id)s with MAC %(mac)s; ",
                      {'id': source_port['id'],
                       'mac': src_port_params['mac'],
                       'source_vlans': src_port_params['src_vlans']})
            raise taas_exc.PciSlotNotFound(port_id=source_port['id'],
                                           mac=src_port_params['mac'])

        if not ts_port_params['pci_slot']:
            LOG.error("No PCI Slot for ts_port %(id)s with MAC %(mac)s; ",
                      {'id': ts_port['id'], 'mac': ts_port_params['mac']})
            raise taas_exc.PciSlotNotFound(port_id=ts_port['id'],
                                           mac=ts_port_params['mac'])

        # Fetch common VLAN tags
        src_vlans_list = []
        for src_vlans_str in tap_flow['source_vlans_list']:
            src_vlans_list.extend(common_utils.get_list_from_ranges_str(
                src_vlans_str))

        src_vlans_list = sorted(set(src_vlans_list))

        vlan_filter_list = []
        for vlan_filter_str in tap_flow['vlan_filter_list']:
            vlan_filter_list.extend(common_utils.get_list_from_ranges_str(
                vlan_filter_str))

        vlan_filter_list = sorted(set(vlan_filter_list))

        common_vlans_list = \
            list(set(src_vlans_list).intersection(vlan_filter_list))

        common_vlans_rng_str = \
            common_utils.get_ranges_str_from_list(common_vlans_list)

        LOG.info("TaaS src_vlans_list %(src_vlans_list)s, "
                 "vlan_filter_list %(vlan_filter_list)s, "
                 "common_vlans_list %(common_vlans_list)s, "
                 "common_vlans_rng_str %(common_vlans_rng_str)s; ",
                 {'src_vlans_list': src_vlans_list,
                  'vlan_filter_list': vlan_filter_list,
                  'common_vlans_list': common_vlans_list,
                  'common_vlans_rng_str': common_vlans_rng_str})

        if ts_port_params['pf_device'] and \
                ts_port_params['vf_index'] and \
                src_port_params['vf_index']:

            with self.lock:
                try:
                    LOG.info("TaaS invoking execute_sysfs_command")
                    self.sriov_utils.execute_sysfs_command('rem',
                                                           ts_port_params,
                                                           src_port_params,
                                                           taas_consts.
                                                           VLAN_RANGE,
                                                           False,
                                                           'BOTH')
                except Exception:
                    LOG.error("TaaS error in invoking execute_sysfs_command")
                    with excutils.save_and_reraise_exception():
                        raise taas_exc.SriovNicSwitchDriverInvocationError(
                            ts_pf_dev=ts_port_params['pf_device'],
                            ts_vf_index=ts_port_params['vf_index'],
                            source_vf_index=src_port_params['vf_index'],
                            common_vlans_rng_str=taas_consts.VLAN_RANGE,
                            vf_to_vf_all_vlans=vf_to_vf_all_vlans,
                            direction=direction)

                if common_vlans_rng_str:
                    try:
                        LOG.info("TaaS invoking execute_sysfs_command")
                        self.sriov_utils.execute_sysfs_command(
                            'add',
                            ts_port_params,
                            src_port_params,
                            common_vlans_rng_str,
                            False,
                            'BOTH')
                    except Exception:
                        LOG.error("TaaS error in invoking "
                                  "execute_sysfs_command")
                        with excutils.save_and_reraise_exception():
                            raise taas_exc.SriovNicSwitchDriverInvocationError(
                                ts_pf_dev=ts_port_params['pf_device'],
                                ts_vf_index=ts_port_params['vf_index'],
                                source_vf_index=src_port_params['vf_index'],
                                common_vlans_rng_str=common_vlans_rng_str,
                                vf_to_vf_all_vlans=vf_to_vf_all_vlans,
                                direction=direction)

        return
