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

import copy
import mock
import re

from neutron_taas.common import utils as common_utils
from neutron_taas.services.taas.drivers.linux import sriov_nic_exceptions \
    as taas_exc
from neutron_taas.services.taas.drivers.linux import sriov_nic_utils
from neutron_taas.tests import base

FAKE_SRIOV_PORT = {
    'id': 'fake_1', 'mac_address': "52:54:00:12:35:02",
    'binding:profile': {
        'pci_slot': None}, 'binding:vif_details': {'vlan': 20}
    }


class TestSriovNicUtils(base.TaasTestCase):
    def setUp(self):
        super(TestSriovNicUtils, self).setUp()

    def test_get_sysfs_netdev_path_with_pf_interface(self):
        self.assertEqual(
            "/sys/bus/pci/devices/12/physfn/net",
            sriov_nic_utils.SriovNicUtils().
            _get_sysfs_netdev_path(12, True))

    def test_get_sysfs_netdev_path_without_pf_interface(self):
        self.assertEqual(
            "/sys/bus/pci/devices/12/net",
            sriov_nic_utils.SriovNicUtils().
            _get_sysfs_netdev_path(12, False))

    @mock.patch.object(sriov_nic_utils, 'os')
    def test_get_ifname_by_pci_address(self, mock_os):
        mock_os.listdir.return_value = ['random1', 'random2']
        self.assertEqual(sriov_nic_utils.SriovNicUtils().
                         get_ifname_by_pci_address(12, False), 'random2')

    @mock.patch.object(sriov_nic_utils, 'os')
    def test_get_ifname_by_pci_address_no_dev_info(self, mock_os):
        mock_os.listdir.return_value = list()
        self.assertRaises(
            taas_exc.PciDeviceNotFoundById,
            sriov_nic_utils.SriovNicUtils().get_ifname_by_pci_address, 12, 9)

    @mock.patch.object(sriov_nic_utils, 'os')
    @mock.patch.object(sriov_nic_utils, 'open', create=True)
    def test_get_mac_by_pci_address(self, mock_open, mock_os):
        mock_os.listdir.return_value = ['random1', 'random2']
        mock_os.path.join.return_value = 'random'
        fake_file_handle = ["52:54:00:12:35:02"]
        fake_file_iter = fake_file_handle.__iter__()
        mock_open.return_value.__enter__.return_value = fake_file_iter
        self.assertEqual(
            "52:54:00:12:35:02", sriov_nic_utils.SriovNicUtils().
            get_mac_by_pci_address(12, False))

    @mock.patch.object(sriov_nic_utils, 'os')
    @mock.patch.object(sriov_nic_utils, 'open', create=True)
    def test_get_mac_by_pci_address_no_content(self, mock_open, mock_os):
        mock_os.listdir.return_value = ['random1', 'random2']
        mock_os.path.join.return_value = 'random'
        fake_file_handle = []
        fake_file_iter = fake_file_handle.__iter__()
        mock_open.return_value.__enter__.return_value = fake_file_iter
        self.assertRaises(
            taas_exc.PciDeviceNotFoundById,
            sriov_nic_utils.SriovNicUtils().get_mac_by_pci_address, 12, False)

    @mock.patch.object(sriov_nic_utils, 'os')
    def test_get_mac_by_pci_address_wrong_dev_path(self, mock_os):
        mock_os.listdir.return_value = ['random1', 'random2']
        mock_os.path.join.return_value = 'random'
        self.assertRaises(
            taas_exc.PciDeviceNotFoundById,
            sriov_nic_utils.SriovNicUtils().get_mac_by_pci_address, 12, False)

    @mock.patch.object(sriov_nic_utils, 'os')
    @mock.patch.object(sriov_nic_utils, 'open', create=True)
    def test_get_net_name_by_vf_pci_address(self, mock_open, mock_os):
        mock_os.listdir.return_value = ['enp0s3', 'enp0s2']
        mock_os.path.join.return_value = 'random'
        fake_file_handle = ["52:54:00:12:35:02"]
        fake_file_iter = fake_file_handle.__iter__()
        mock_open.return_value.__enter__.return_value = fake_file_iter
        self.assertEqual(
            'net_enp0s3_52_54_00_12_35_02',
            sriov_nic_utils.SriovNicUtils().
            get_net_name_by_vf_pci_address(12))

    def _common_merge_utility(self, value):
        output_list = list()
        for v in value:
            output_list.append(v)
        return output_list

    def test_get_ranges_str_from_list(self):
        input_list = [4, 11, 12, 13, 25, 26, 27]
        self.assertEqual("4,11-13,25-27", common_utils.
                         get_ranges_str_from_list(input_list))

    def test_get_list_from_ranges_str(self):
        input_str = "4,6,10-13,25-27"
        expected_output = [4, 6, 10, 11, 12, 13, 25, 26, 27]
        self.assertEqual(expected_output, common_utils.
                         get_list_from_ranges_str(input_str))

    def test_get_vf_num_by_pci_address_neg(self):
        self.assertRaises(
            taas_exc.PciDeviceNotFoundById,
            sriov_nic_utils.SriovNicUtils().get_vf_num_by_pci_address, 12)

    @mock.patch.object(sriov_nic_utils, 'glob')
    @mock.patch.object(sriov_nic_utils, 're')
    @mock.patch.object(sriov_nic_utils, 'os')
    def test_get_vf_num_by_pci_address(self, mock_os, mock_re, mock_glob):
        mock_glob.iglob.return_value = ['file1']
        mock_os.readlink.return_value = 12
        mock_re.compile().search.return_value = re.match(r"(\d+)", "89")
        self.assertEqual(
            '89', sriov_nic_utils.SriovNicUtils().
            get_vf_num_by_pci_address(12))

    @mock.patch.object(sriov_nic_utils, 'glob')
    @mock.patch.object(sriov_nic_utils, 're')
    @mock.patch.object(sriov_nic_utils, 'os')
    @mock.patch.object(sriov_nic_utils, 'open', create=True)
    @mock.patch.object(sriov_nic_utils, 'portbindings')
    def test_get_sriov_port_params(self, mock_port_bindings, mock_open,
                                   mock_os, mock_re, mock_glob):
        sriov_port = copy.deepcopy(FAKE_SRIOV_PORT)
        fake_profile = mock_port_bindings.PROFILE = 'binding:profile'
        mock_port_bindings.VIF_DETAILS = 'binding:vif_details'
        sriov_port[fake_profile]['pci_slot'] = 3
        mock_glob.iglob.return_value = ['file1']
        mock_os.readlink.return_value = 12
        mock_re.compile().search.return_value = re.match(r"(\d+)", "89")
        mock_os.listdir.return_value = ['net_enp0s2_52_54_00_12_35_02',
                                        'net_enp0s3_52_54_00_12_35_02']
        mock_os.path.join.return_value = 'random'
        fake_file_handle = ["52:54:00:12:35:02"]
        fake_file_iter = fake_file_handle.__iter__()
        mock_open.return_value.__enter__.return_value = fake_file_iter
        expected_output = {
            'mac': '52:54:00:12:35:02', 'pci_slot': 3, 'vf_index': '89',
            'pf_device': 'net_enp0s3_52_54_00_12_35_02', 'src_vlans': 20}
        self.assertEqual(
            expected_output, sriov_nic_utils.SriovNicUtils().
            get_sriov_port_params(sriov_port))

    @mock.patch.object(sriov_nic_utils, 'glob')
    @mock.patch.object(sriov_nic_utils, 're')
    @mock.patch.object(sriov_nic_utils, 'os')
    @mock.patch.object(sriov_nic_utils, 'open', create=True)
    @mock.patch.object(sriov_nic_utils, 'portbindings')
    def test_get_sriov_port_params_no_pci_slot(self, mock_port_bindings,
                                               mock_open, mock_os, mock_re,
                                               mock_glob):
        sriov_port = copy.deepcopy(FAKE_SRIOV_PORT)
        mock_port_bindings.PROFILE = 'binding:profile'
        mock_port_bindings.VIF_DETAILS = 'binding:vif_details'
        mock_glob.iglob.return_value = ['file1']
        mock_os.readlink.return_value = 12
        mock_re.compile().search.return_value = re.match(r"(\d+)", "89")
        mock_os.listdir.return_value = ['enp0s3', 'enp0s2']
        mock_os.path.join.return_value = 'random'
        fake_file_handle = ["52:54:00:12:35:02"]
        fake_file_iter = fake_file_handle.__iter__()
        mock_open.return_value.__enter__.return_value = fake_file_iter
        self.assertIsNone(sriov_nic_utils.SriovNicUtils().
                          get_sriov_port_params(sriov_port))

    @mock.patch.object(sriov_nic_utils, 'utils')
    @mock.patch.object(sriov_nic_utils, 'os')
    def test_execute_sysfs_command_egress_add(self, mock_os,
                                              mock_neutron_utils):
        sriov_nic_utils.SriovNicUtils().execute_sysfs_command(
            'add', {'pf_device': 'p2p1', 'vf_index': '9'}, {'vf_index': '18'},
            "4,11-13", True, "OUT")
        egress_cmd = ['i40e_sysfs_command', 'p2p1', '18',
                      'egress_mirror', 'add', '9']
        mock_neutron_utils.execute.assert_called_once_with(
            egress_cmd, run_as_root=True)

    @mock.patch.object(sriov_nic_utils, 'utils')
    @mock.patch.object(sriov_nic_utils, 'os')
    def test_execute_sysfs_command_ingress_add(self, mock_os,
                                               mock_neutron_utils):
        sriov_nic_utils.SriovNicUtils().execute_sysfs_command(
            'add', {'pf_device': 'p2p1', 'vf_index': '9'}, {'vf_index': '18'},
            "4,11-13", True, "IN")
        ingress_cmd = ['i40e_sysfs_command', 'p2p1', '18',
                       'ingress_mirror', 'add', '9']
        mock_neutron_utils.execute.assert_called_once_with(
            ingress_cmd, run_as_root=True)

    @mock.patch.object(sriov_nic_utils, 'utils')
    @mock.patch.object(sriov_nic_utils, 'os')
    def test_execute_sysfs_command_both_add(
            self, mock_os, mock_neutron_utils):
        sriov_nic_utils.SriovNicUtils().execute_sysfs_command(
            'add', {'pf_device': 'p2p1', 'vf_index': '9'}, {'vf_index': '18'},
            "4,11-13", True, "BOTH")
        self.assertEqual(2, mock_neutron_utils.execute.call_count)

    @mock.patch.object(sriov_nic_utils, 'utils')
    @mock.patch.object(sriov_nic_utils, 'os')
    def test_execute_sysfs_command_egress_rem(self, mock_os,
                                              mock_neutron_utils):
        sriov_nic_utils.SriovNicUtils().execute_sysfs_command(
            'rem', {'pf_device': 'p2p1', 'vf_index': '9'}, {'vf_index': '18'},
            "4,11-13", True, "OUT")
        egress_cmd = ['i40e_sysfs_command', 'p2p1', '18',
                      'egress_mirror', 'rem', '9']
        mock_neutron_utils.execute.assert_called_once_with(
            egress_cmd, run_as_root=True)

    @mock.patch.object(sriov_nic_utils, 'utils')
    @mock.patch.object(sriov_nic_utils, 'os')
    def test_execute_sysfs_command_ingress_rem(self, mock_os,
                                               mock_neutron_utils):
        sriov_nic_utils.SriovNicUtils().execute_sysfs_command(
            'rem', {'pf_device': 'p2p1', 'vf_index': '9'}, {'vf_index': '18'},
            "4,11-13", True, "IN")
        ingress_cmd = ['i40e_sysfs_command', 'p2p1', '18',
                       'ingress_mirror', 'rem', '9']
        mock_neutron_utils.execute.assert_called_once_with(
            ingress_cmd, run_as_root=True)

    @mock.patch.object(sriov_nic_utils, 'utils')
    @mock.patch.object(sriov_nic_utils, 'os')
    def test_execute_sysfs_command_both_rem(
            self, mock_os, mock_neutron_utils):
        sriov_nic_utils.SriovNicUtils().execute_sysfs_command(
            'rem', {'pf_device': 'p2p1', 'vf_index': '9'}, {'vf_index': '18'},
            "4,11-13", True, "BOTH")
        self.assertEqual(2, mock_neutron_utils.execute.call_count)

    @mock.patch.object(sriov_nic_utils, 'utils')
    @mock.patch.object(sriov_nic_utils, 'os')
    def test_execute_sysfs_command_not_both_vf_to_vf_all_vlans_False(
            self, mock_os, mock_neutron_utils):
        cmd = ['i40e_sysfs_command', 'p2p1', '9',
               'vlan_mirror', 'rem', '4,11-13']
        sriov_nic_utils.SriovNicUtils().execute_sysfs_command(
            'rem', {'pf_device': 'p2p1', 'vf_index': '9'}, {'vf_index': '18'},
            "4,11-13", False, "FAKE")
        mock_neutron_utils.execute.assert_called_once_with(
            cmd, run_as_root=True)
