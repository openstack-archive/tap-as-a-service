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
# This class implements a utility functions for SRIOV NIC Switch Driver
#
import os
from oslo_log import log as logging

from neutron.agent.linux import utils
from neutron_lib.api.definitions import portbindings
from neutron_taas.services.taas.drivers.linux import sriov_nic_exceptions \
    as taas_exc

import glob
import re

LOG = logging.getLogger(__name__)


class SriovNicUtils(object):
    #
    # Initializes internal state for specified # keys
    #
    def __init__(self):
        LOG.debug("SriovNicUtils: init called")
        return

    #
    # Returns specified key-value affilation, if it exists.
    #
    def execute_sysfs_command(self, command, ts_port_params,
                              src_port_params,
                              common_vlans_ranges_str,
                              vf_to_vf_all_vlans, direction):
        """Execute the SRIOV NIC Switch Driver's SysFs command.

        # Mirror traffic from VF0 to VF3 on interface p2p1, ex.
        echo add 3 > /sys/class/net/p2p1/device/sriov/0/ingress_mirror
        echo add 3 > /sys/class/net/p2p1/device/sriov/0/egress_mirror

        # Remove traffic mirroring from VF0 to VF3 on interface p2p1, ex.
        echo rem 3 > /sys/class/net/p2p1/device/sriov/0/ingress_mirror
        echo rem 3 > /sys/class/net/p2p1/device/sriov/0/egress_mirror

        # Add VLANs 2,6,18-22 to Mirror traffic to VF3 (port p2p1), ex.
        echo add 2,6,18-22 > /sys/class/net/p2p1/device/sriov/3/vlan_mirror

        # Remove VLANs 2,6,18-22 to Mirror traffic to VF3 (port p2p1), ex.
        echo rem 2,6,18-22 > /sys/class/net/p2p1/device/sriov/3/vlan_mirror

        # Remove all VLANs from mirroring at VF3, ex.
        echo rem 0-4095 > /sys/class/net/p1p1/device/sriov/3/vlan_mirror
        """
        LOG.debug("TaaS sysfs command params %(command)s, "
                  "ts_port_params %(ts_port_params)s, "
                  "src_port_params %(src_port_params)s, "
                  "common_vlans_ranges_str %(common_vlans_ranges_str)s; "
                  "vf_to_vf_all_vlans %(vf_to_vf_all_vlans)s; "
                  "direction %(direction)s; ",
                  {'command': command,
                   'ts_port_params': ts_port_params,
                   'src_port_params': src_port_params,
                   'common_vlans_ranges_str': common_vlans_ranges_str,
                   'vf_to_vf_all_vlans': vf_to_vf_all_vlans,
                   'direction': direction})
        if vf_to_vf_all_vlans:
            if direction in ['OUT', 'BOTH']:
                commit_cmd = ['i40e_sysfs_command',
                              ts_port_params['pf_device'],
                              src_port_params['vf_index'],
                              'egress_mirror',
                              command,
                              ts_port_params['vf_index']]

                try:
                    LOG.info("TaaS executing sysfs_command %(command)s",
                             {'command': commit_cmd})
                    utils.execute(commit_cmd, run_as_root=True)
                except (OSError, RuntimeError, IndexError, ValueError) as e:
                    LOG.error("Exception while executing Sysfs command "
                              "Exception: %s", e)
                    return

            if direction in ['IN', 'BOTH']:
                commit_cmd = ['i40e_sysfs_command',
                              ts_port_params['pf_device'],
                              src_port_params['vf_index'],
                              'ingress_mirror',
                              command,
                              ts_port_params['vf_index']]

                try:
                    LOG.info("TaaS executing sysfs_command %(command)s",
                             {'command': commit_cmd})
                    utils.execute(commit_cmd, run_as_root=True)
                except (OSError, RuntimeError, IndexError, ValueError) as e:
                    LOG.error("Exception while executing Sysfs command "
                              "Exception: %s", e)
                    return
        else:
            if direction != 'BOTH':
                LOG.warning("SRIOV NIC Switch driver only supports"
                            "direction=BOTH for specific VLANs' mirroring")

            commit_cmd = ['i40e_sysfs_command',
                          ts_port_params['pf_device'],
                          ts_port_params['vf_index'],
                          'vlan_mirror',
                          command,
                          common_vlans_ranges_str]

            try:
                LOG.info("TaaS executing sysfs_command %(command)s",
                         {'command': commit_cmd})
                utils.execute(commit_cmd, run_as_root=True)
            except (OSError, RuntimeError, IndexError, ValueError) as e:
                LOG.error("Exception while executing Sysfs command "
                          "Exception: %s", e)
                return

    def _get_sysfs_netdev_path(self, pci_addr, pf_interface):
        """Get the sysfs path based on the PCI address of the device.

        Assumes a networking device - will not check for the existence
        of the path.
        """
        if pf_interface:
            return "/sys/bus/pci/devices/%s/physfn/net" % pci_addr
        return "/sys/bus/pci/devices/%s/net" % pci_addr

    def get_ifname_by_pci_address(self, pci_addr, pf_interface=False):
        """Get the interface name based on a VF's pci address.

        The returned interface name is either the parent PF's or that of
        the VF itself based on the argument of pf_interface.
        """
        dev_path = self._get_sysfs_netdev_path(pci_addr, pf_interface)
        try:
            dev_info = os.listdir(dev_path)
            return dev_info.pop()
        except Exception:
            raise taas_exc.PciDeviceNotFoundById(id=pci_addr)

    def get_mac_by_pci_address(self, pci_addr, pf_interface=False):
        """Get the MAC address of the nic based on its PCI address.

        Raises PciDeviceNotFoundById in case the pci device is not a NIC
        """
        dev_path = self._get_sysfs_netdev_path(pci_addr, pf_interface)
        if_name = self.get_ifname_by_pci_address(pci_addr, pf_interface)
        addr_file = os.path.join(dev_path, if_name, 'address')

        try:
            with open(addr_file) as f:
                mac = next(f).strip()
                return mac
        except (IOError, StopIteration) as e:
            LOG.warning("Could not find the expected sysfs file for "
                        "determining the MAC address of the PCI device "
                        "%(addr)s. May not be a NIC. Error: %(e)s",
                        {'addr': pci_addr, 'e': e})
            raise taas_exc.PciDeviceNotFoundById(id=pci_addr)

    def get_vf_num_by_pci_address(self, pci_addr):
        """Get the VF number based on a VF's pci address

        A VF is associated with an VF number, which ip link command uses to
        configure it. This can be obtained from the PCI device filesystem.
        """
        VIRTFN_RE = re.compile("virtfn(\d+)")
        virtfns_path = "/sys/bus/pci/devices/%s/physfn/virtfn*" % (pci_addr)
        vf_num = None
        LOG.debug("TaaS: pci_addr: %(pci_addr)s "
                  "virtfns_path: %(virtfns_path)s",
                  {'pci_addr': pci_addr,
                   'virtfns_path': virtfns_path})
        try:
            for vf_path in glob.iglob(virtfns_path):
                if re.search(pci_addr, os.readlink(vf_path)):
                    t = VIRTFN_RE.search(vf_path)
                    vf_num = t.group(1)
                    break
        except Exception:
            pass
        if vf_num is None:
            LOG.warning("TaaS: No net device was found for pci: %(pci_addr)s "
                        "virtfns_path: %(virtfns_path)s",
                        {'pci_addr': pci_addr,
                         'virtfns_path': virtfns_path})
            raise taas_exc.PciDeviceNotFoundById(id=pci_addr)
        return vf_num

    def get_net_name_by_vf_pci_address(self, vfaddress, pf_interface=False):
        """Given the VF PCI address, returns the net device name.

        Every VF is associated to a PCI network device. This function
        returns the libvirt name given to this network device; e.g.:

            <device>
                <name>net_enp8s0f0_90_e2_ba_5e_a6_40</name>
            ...

        In the libvirt parser information tree, the network device stores the
        network capabilities associated to this device.
        """
        LOG.debug("TaaS: vfaddr: %(vfaddr)s ",
                  {'vfaddr': vfaddress})
        try:
            mac = self.get_mac_by_pci_address(vfaddress,
                                              pf_interface).split(':')
            ifname = self.get_ifname_by_pci_address(vfaddress, pf_interface)
            LOG.debug("TaaS: mac: %(mac)s, ifname: %(ifname)s",
                      {'mac': mac, 'ifname': ifname})
            return ("net_%(ifname)s_%(mac)s" %
                    {'ifname': ifname, 'mac': '_'.join(mac)})
        except Exception:
            LOG.warning("No net device was found for VF %(vfaddress)s",
                        {'vfaddress': vfaddress})
            return

    def get_sriov_port_params(self, sriov_port):
        """Returns a dict of common SRIOV parameters for a given SRIOV port

        """
        LOG.debug("TaaS: sriov_port %(id)s; ",
                  {'id': sriov_port['id']})

        port_mac = sriov_port['mac_address']

        pci_slot = None
        src_vlans = None

        if sriov_port.get(portbindings.PROFILE):
            pci_slot = sriov_port[portbindings.PROFILE].get('pci_slot')

        if sriov_port.get(portbindings.VIF_DETAILS):
            src_vlans = sriov_port[portbindings.VIF_DETAILS].get('vlan')

        LOG.debug("TaaS: pci_slot %(pci_slot)s; "
                  "src_vlans %(src_vlans)s; ",
                  {'pci_slot': pci_slot,
                   'src_vlans': src_vlans})

        if not pci_slot:
            LOG.error("No PCI Slot for sriov_port %(id)s with MAC %(mac)s; ",
                      {'id': sriov_port['id'], 'mac': port_mac})
            return

        vf_index = self.get_vf_num_by_pci_address(pci_slot)

        pf_device = self.get_ifname_by_pci_address(pci_slot, True)

        return {'mac': port_mac, 'pci_slot': pci_slot,
                'vf_index': vf_index, 'pf_device': pf_device,
                'src_vlans': src_vlans}
