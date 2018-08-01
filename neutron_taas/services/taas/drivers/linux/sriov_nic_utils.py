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
from neutron.extensions import portbindings
from neutron_lib import exceptions as n_exc
from neutron_taas.extensions import taas

import glob
import re

LOG = logging.getLogger(__name__)


class SriovNicUtils(object):
    #
    # Initializes internal state for specified # keys
    #
    def __init__(self):
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
        if vf_to_vf_all_vlans:
            if direction in ['OUT', 'BOTH']:
                sysfs_kobject_path = \
                    '/sys/class/net/' + ts_port_params['pf_device'] + \
                    '/device/sriov/' + src_port_params['vf_index'] + \
                    '/egress_mirror/'
                commit_cmd = ['echo', command, ts_port_params['vf_index'],
                              '>', sysfs_kobject_path]

                if not os.path.exists(sysfs_kobject_path):
                    raise n_exc.Invalid("Invalid PF (%s) and/or "
                                        "Source VF (%s) combination" %
                                        (ts_port_params['pf_device'],
                                         src_port_params['vf_index']))

                try:
                    utils.execute(commit_cmd, run_as_root=True)
                except (OSError, RuntimeError, IndexError, ValueError) as e:
                    LOG.error("Exception while executing Sysfs command "
                              "Exception: %s", e)
                    return

            if direction in ['IN', 'BOTH']:
                sysfs_kobject_path = \
                    '/sys/class/net/' + ts_port_params['pf_device'] + \
                    '/device/sriov/' + src_port_params['vf_index'] + \
                    '/ingress_mirror/'
                commit_cmd = ['echo', command, ts_port_params['vf_index'],
                              '>', sysfs_kobject_path]

                if not os.path.exists(sysfs_kobject_path):
                    raise n_exc.Invalid("Invalid PF (%s) and/or "
                                        "Source VF (%s) combination" %
                                        (ts_port_params['pf_device'],
                                         src_port_params['vf_index']))

                try:
                    utils.execute(commit_cmd, run_as_root=True)
                except (OSError, RuntimeError, IndexError, ValueError) as e:
                    LOG.error("Exception while executing Sysfs command "
                              "Exception: %s", e)
                    return
        else:
            if direction != 'BOTH':
                LOG.warning("SRIOV NIC Switch driver only supports"
                            "direction=BOTH for specific VLANs' mirroring")

            sysfs_kobject_path = '/sys/class/net/' + \
                                 ts_port_params['pf_device'] + \
                                 '/device/sriov/' + \
                                 ts_port_params['vf_index'] + '/'
            commit_cmd = ['echo', command, common_vlans_ranges_str, '>',
                          sysfs_kobject_path]

            if not os.path.exists(sysfs_kobject_path):
                raise n_exc.Invalid("Invalid PF (%s) or Tap-service VF (%s) "
                                    "combination" %
                                    (ts_port_params['pf_device'],
                                     ts_port_params['vf_index']))

            try:
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
            raise taas.PciDeviceNotFoundById(id=pci_addr)

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
            raise taas.PciDeviceNotFoundById(id=pci_addr)

    def get_vf_num_by_pci_address(self, pci_addr):
        """Get the VF number based on a VF's pci address

        A VF is associated with an VF number, which ip link command uses to
        configure it. This can be obtained from the PCI device filesystem.
        """
        VIRTFN_RE = re.compile("virtfn(\d+)")
        virtfns_path = "/sys/bus/pci/devices/%s/physfn/virtfn*" % (pci_addr)
        vf_num = None
        try:
            for vf_path in glob.iglob(virtfns_path):
                if re.search(pci_addr, os.readlink(vf_path)):
                    t = VIRTFN_RE.search(vf_path)
                    vf_num = t.group(1)
                    break
        except Exception:
            pass
        if vf_num is None:
            raise taas.PciDeviceNotFoundById(id=pci_addr)
        return vf_num

    def get_net_name_by_vf_pci_address(self, vfaddress):
        """Given the VF PCI address, returns the net device name.

        Every VF is associated to a PCI network device. This function
        returns the libvirt name given to this network device; e.g.:

            <device>
                <name>net_enp8s0f0_90_e2_ba_5e_a6_40</name>
            ...

        In the libvirt parser information tree, the network device stores the
        network capabilities associated to this device.
        """
        try:
            mac = self.get_mac_by_pci_address(vfaddress).split(':')
            ifname = self.get_ifname_by_pci_address(vfaddress)
            return ("net_%(ifname)s_%(mac)s" %
                    {'ifname': ifname, 'mac': '_'.join(mac)})
        except Exception:
            LOG.warning("No net device was found for VF %(vfaddress)s",
                        {'vfaddress': vfaddress})
            return

    def merge_ranges(self, ranges):
        """Merge overlapping and adjacent ranges

        Merge and yield the merged ranges in order. The argument must be an
        iterable of pairs (start, stop).

        list(merge_ranges([(5,7), (3,5), (-1,3)]))
        [(-1, 7)]

        list(merge_ranges([(5,6), (3,4), (1,2)]))
        [(1, 2), (3, 4), (5, 6)]

        list(merge_ranges([(5,6), (3,4), (1,2)]))
        [(1, 6)]

        list(merge_ranges([(5,6), (3,4), (1,2), (10,20), (1,8)]))
        [(1, 8), (10, 20)]

        list(merge_ranges([(5,6), (3,4), (1,2), (10,20), (1,8), (9,10)]))
        [(1, 20)]
        """
        ranges = iter(sorted(ranges))
        current_start, current_stop = next(ranges)
        for start, stop in ranges:
            if start > (current_stop + 1):
                # Gap between segments: output current segment and start
                # a new one.
                yield current_start, current_stop
                current_start, current_stop = start, stop
            else:
                # Segments adjacent or overlapping: merge.
                current_stop = max(current_stop, stop)
        yield current_start, current_stop

    def get_list_from_ranges_str(self, ranges_str):
        """Convert the range in string format to ranges list

        And yield the merged ranges in order. The argument must be a
        string having comma separated vlan and vlan-ranges.

        get_list_from_ranges_str("4,6,10-13,25-27,100-103")
        [4, 6, 10, 11, 12, 13, 25, 26, 27, 100, 101, 102, 103]
        """
        return sum(((list(range(*[int(range_start) + range_index
                                  for range_index, range_start in
                                  enumerate(range_item.split('-'))]))
                    if '-' in range_item else [int(range_item)])
                    for range_item in ranges_str.split(',')), [])

    def get_ranges_str_from_list(self, ranges):
        """Convert the ranges list to string format

        And yield the merged ranges in order in string format.
        The argument must be an iterable of pairs (start, stop).

        get_ranges_str_from_list([4, 11, 12, 13, 25, 26, 27, 101, 102, 103])
        "4,11-13,25-27,101-103"
        """
        ranges_str = []
        for val in sorted(ranges):
            if not ranges_str or ranges_str[-1][-1] + 1 != val:
                ranges_str.append([val])
            else:
                ranges_str[-1].append(val)
        return ",".join([str(range_item[0]) if len(range_item) == 1
                         else str(range_item[0]) + "-" + str(range_item[-1])
                         for range_item in ranges_str])

    def get_sriov_port_params(self, sriov_port):
        """Returns a dict of common SRIOV parameters for a given SRIOV port

        """
        port_mac = sriov_port['mac_address']

        pci_slot = None
        vlan_mirror = None
        src_vlans = None
        guest_vlans = None

        if sriov_port.get(portbindings.PROFILE):
            pci_slot = sriov_port[portbindings.PROFILE].get('pci_slot')
            vlan_mirror = sriov_port[portbindings.PROFILE].get('vlan_mirror')
            guest_vlans = sriov_port[portbindings.PROFILE].get('guest_vlans')

        if sriov_port.get(portbindings.VIF_DETAILS):
            src_vlans = sriov_port[portbindings.VIF_DETAILS].get('vlan')

        if src_vlans == '0':
            src_vlans = guest_vlans

        if not pci_slot:
            LOG.error("No PCI Slot for sriov_port %(id)s with MAC %(mac)s; ",
                      {'id': sriov_port['id'], 'mac': port_mac})
            return

        vf_index = self.get_vf_num_by_pci_address(pci_slot)
        pf_device = self.get_net_name_by_vf_pci_address(pci_slot)

        return {'mac': port_mac, 'pci_slot': pci_slot,
                'vf_index': vf_index, 'pf_device': pf_device,
                'vlan_mirror': vlan_mirror, 'src_vlans': src_vlans}
