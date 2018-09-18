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


import copy
import mock

from neutron_taas.services.taas.drivers.linux import sriov_nic_exceptions \
    as taas_exc
from neutron_taas.services.taas.drivers.linux import sriov_nic_taas
from neutron_taas.tests import base

FAKE_PORT_PARAMS = {
    'mac': '52:54:00:12:35:02', 'pci_slot': 3, 'vf_index': '89',
    'pf_device': 'net_enp0s3_52_54_00_12_35_02', 'src_vlans': '20'}

FAKE_TAP_SERVICE = {'port': {
    'id': 'fake_1', 'mac_address': "52:54:00:12:35:02",
    'binding:profile': {'pci_slot': 3},
    'binding:vif_details': {'vlan': '20'}}}

FAKE_TAP_FLOW = {'port': FAKE_TAP_SERVICE['port'],
                 'ts_port': FAKE_TAP_SERVICE['port'],
                 'source_vlans_list': ['4-6', '8-10', '15-18,20'],
                 'vlan_filter_list': '1-5,9,18,20,27-30,4000-4095',
                 'tap_flow': {'direction': 'IN', 'vlan_filter': '20'}}


class TestSriovNicTaas(base.TaasTestCase):
    def setUp(self):
        super(TestSriovNicTaas, self).setUp()

    @mock.patch.object(sriov_nic_taas, 'sriov_utils')
    def test_create_tap_service(self, mock_sriov_utils):
        tap_service = FAKE_TAP_SERVICE
        mock_sriov_utils.SriovNicUtils().get_sriov_port_params.\
            return_value = FAKE_PORT_PARAMS
        obj = sriov_nic_taas.SriovNicTaasDriver()
        obj.initialize()
        obj.create_tap_service(tap_service)
        mock_sriov_utils.SriovNicUtils().get_sriov_port_params.\
            assert_called_once_with(tap_service['port'])

    @mock.patch.object(sriov_nic_taas, 'sriov_utils')
    def test_create_tap_service_no_pf_device_and_vf_index(
            self, mock_sriov_utils):
        tap_service = FAKE_TAP_SERVICE
        temp_fake_port_params = copy.deepcopy(FAKE_PORT_PARAMS)
        temp_fake_port_params['pf_device'] = None
        temp_fake_port_params['vf_index'] = None
        mock_sriov_utils.SriovNicUtils().get_sriov_port_params.\
            return_value = FAKE_PORT_PARAMS
        obj = sriov_nic_taas.SriovNicTaasDriver()
        obj.initialize()
        self.assertIsNone(obj.create_tap_service(tap_service))
        mock_sriov_utils.SriovNicUtils().get_sriov_port_params.\
            assert_called_once_with(tap_service['port'])

    @mock.patch.object(sriov_nic_taas, 'sriov_utils')
    def test_delete_tap_service(self, mock_sriov_utils):
        tap_service = FAKE_TAP_SERVICE
        mock_sriov_utils.SriovNicUtils().get_sriov_port_params.\
            return_value = FAKE_PORT_PARAMS
        obj = sriov_nic_taas.SriovNicTaasDriver()
        obj.initialize()
        obj.create_tap_service(tap_service)
        mock_sriov_utils.SriovNicUtils().get_sriov_port_params.\
            assert_called_once_with(tap_service['port'])

    @mock.patch.object(sriov_nic_taas, 'sriov_utils')
    def test_delete_tap_service_no_pf_device_and_vf_index(
            self, mock_sriov_utils):
        tap_service = FAKE_TAP_SERVICE
        temp_fake_port_params = copy.deepcopy(FAKE_PORT_PARAMS)
        temp_fake_port_params['pf_device'] = None
        temp_fake_port_params['vf_index'] = None
        mock_sriov_utils.SriovNicUtils().get_sriov_port_params.\
            return_value = FAKE_PORT_PARAMS
        obj = sriov_nic_taas.SriovNicTaasDriver()
        obj.initialize()
        self.assertIsNone(obj.create_tap_service(tap_service))
        mock_sriov_utils.SriovNicUtils().get_sriov_port_params.\
            assert_called_once_with(tap_service['port'])

    @mock.patch.object(sriov_nic_taas, 'sriov_utils')
    def test_create_tap_flow(self, mock_sriov_utils):
        tap_flow = {'port': FAKE_TAP_SERVICE['port'],
                    'tap_service_port': FAKE_TAP_SERVICE['port'],
                    'vlan_filter_list': '1-5,9,18,20,27-30,4000-4095',
                    'tap_flow': {'direction': 'IN', 'vlan_filter': '20'}}
        src_port_params = ts_port_params = copy.deepcopy(FAKE_PORT_PARAMS)
        mock_sriov_utils.SriovNicUtils().get_sriov_port_params.\
            side_effect = [src_port_params, ts_port_params]
        obj = sriov_nic_taas.SriovNicTaasDriver()
        obj.initialize()
        obj.create_tap_flow(tap_flow)
        mock_sriov_utils.SriovNicUtils().execute_sysfs_command.\
            assert_called_once_with('add', ts_port_params, src_port_params,
                                    '20', False, 'IN')

    @mock.patch.object(sriov_nic_taas, 'sriov_utils')
    def test_create_tap_flow_no_vlan_filter_on_source_and_probe(
            self, mock_sriov_utils):
        tap_flow = {'port': FAKE_TAP_SERVICE['port'],
                    'tap_service_port': FAKE_TAP_SERVICE['port'],
                    'tap_flow': {'direction': 'IN', 'vlan_filter': '20'}}
        src_port_params = ts_port_params = copy.deepcopy(FAKE_PORT_PARAMS)
        ts_port_params['vlan_filter'] = None
        src_port_params['src_vlans'] = None
        mock_sriov_utils.SriovNicUtils().get_sriov_port_params.\
            side_effect = [src_port_params, ts_port_params]
        obj = sriov_nic_taas.SriovNicTaasDriver()
        obj.initialize()
        obj.create_tap_flow(tap_flow)
        mock_sriov_utils.SriovNicUtils().execute_sysfs_command.\
            assert_called_once_with('add', ts_port_params, src_port_params,
                                    '20', False, 'IN')

    @mock.patch.object(sriov_nic_taas, 'sriov_utils')
    def test_create_tap_flow_no_source_pci_slot(
            self, mock_sriov_utils):
        tap_flow = {'port': FAKE_TAP_SERVICE['port'],
                    'tap_service_port': FAKE_TAP_SERVICE['port'],
                    'tap_flow': {'direction': 'IN', 'vlan_filter': 20}}
        src_port_params = ts_port_params = copy.deepcopy(FAKE_PORT_PARAMS)
        src_port_params['pci_slot'] = None
        mock_sriov_utils.SriovNicUtils().get_sriov_port_params.\
            side_effect = [src_port_params, ts_port_params]
        obj = sriov_nic_taas.SriovNicTaasDriver()
        obj.initialize()
        self.assertRaises(
            taas_exc.PciSlotNotFound, obj.create_tap_flow, tap_flow)

    @mock.patch.object(sriov_nic_taas, 'sriov_utils')
    def test_create_tap_flow_no_ts_pci_slot(
            self, mock_sriov_utils):
        tap_flow = {'port': FAKE_TAP_SERVICE['port'],
                    'tap_service_port': FAKE_TAP_SERVICE['port'],
                    'tap_flow': {'direction': 'IN', 'vlan_filter': 20}}
        src_port_params = copy.deepcopy(FAKE_PORT_PARAMS)
        ts_port_params = copy.deepcopy(FAKE_PORT_PARAMS)
        ts_port_params['pci_slot'] = None
        mock_sriov_utils.SriovNicUtils().get_sriov_port_params.\
            side_effect = [src_port_params, ts_port_params]
        obj = sriov_nic_taas.SriovNicTaasDriver()
        obj.initialize()
        self.assertRaises(
            taas_exc.PciSlotNotFound, obj.create_tap_flow, tap_flow)

    @mock.patch.object(sriov_nic_taas, 'sriov_utils')
    def test_create_tap_flow_different_pf_devices(
            self, mock_sriov_utils):
        tap_flow = {'port': FAKE_TAP_SERVICE['port'],
                    'tap_service_port': FAKE_TAP_SERVICE['port'],
                    'tap_flow': {'direction': 'IN', 'vlan_filter': 20}}
        src_port_params = copy.deepcopy(FAKE_PORT_PARAMS)
        ts_port_params = copy.deepcopy(FAKE_PORT_PARAMS)
        ts_port_params['pf_device'] = 'net_enp0s3_52_54_00_12_35_02'
        src_port_params['pf_device'] = 'net_enp0s8_52_54_00_12_35_01'
        mock_sriov_utils.SriovNicUtils().get_sriov_port_params.\
            side_effect = [src_port_params, ts_port_params]
        obj = sriov_nic_taas.SriovNicTaasDriver()
        obj.initialize()
        self.assertIsNotNone(obj.create_tap_flow, tap_flow)

    @mock.patch.object(sriov_nic_taas, 'sriov_utils')
    def test_delete_tap_flow(self, mock_sriov_utils):
        tap_flow = {'port': FAKE_TAP_SERVICE['port'],
                    'tap_service_port': FAKE_TAP_SERVICE['port'],
                    'source_vlans_list': ['4-6', '8-10', '15-18,20'],
                    'vlan_filter_list': ['1-5,9,18,20,27-30,4000-4095'],
                    'tap_flow': {'direction': 'IN', 'vlan_filter': '20'}}
        src_port_params = ts_port_params = copy.deepcopy(FAKE_PORT_PARAMS)
        mock_sriov_utils.SriovNicUtils().get_sriov_port_params.\
            side_effect = [src_port_params, ts_port_params]
        obj = sriov_nic_taas.SriovNicTaasDriver()
        obj.initialize()
        self.assertIsNone(obj.delete_tap_flow(tap_flow))
        self.assertEqual(2, mock_sriov_utils.SriovNicUtils().
                         execute_sysfs_command.call_count)

    @mock.patch.object(sriov_nic_taas, 'sriov_utils')
    def test_delete_tap_flow_no_source_pci_slot(
            self, mock_sriov_utils):
        tap_flow = {'port': FAKE_TAP_SERVICE['port'],
                    'tap_service_port': FAKE_TAP_SERVICE['port'],
                    'source_vlans_list': [4, 5, 9],
                    'tap_flow': {'direction': 'IN', 'vlan_filter': 20}}
        src_port_params = copy.deepcopy(FAKE_PORT_PARAMS)
        ts_port_params = copy.deepcopy(FAKE_PORT_PARAMS)
        src_port_params['pci_slot'] = None
        mock_sriov_utils.SriovNicUtils().get_sriov_port_params.\
            side_effect = [src_port_params, ts_port_params]
        obj = sriov_nic_taas.SriovNicTaasDriver()
        obj.initialize()
        self.assertRaises(taas_exc.PciSlotNotFound, obj.delete_tap_flow,
                          tap_flow)

    @mock.patch.object(sriov_nic_taas, 'sriov_utils')
    def test_delete_tap_flow_no_ts_pci_slot(
            self, mock_sriov_utils):
        tap_flow = {'port': FAKE_TAP_SERVICE['port'],
                    'tap_service_port': FAKE_TAP_SERVICE['port'],
                    'tap_flow': {'direction': 'IN', 'vlan_filter': 20}}
        src_port_params = copy.deepcopy(FAKE_PORT_PARAMS)
        ts_port_params = copy.deepcopy(FAKE_PORT_PARAMS)
        ts_port_params['pci_slot'] = None
        mock_sriov_utils.SriovNicUtils().get_sriov_port_params.\
            side_effect = [src_port_params, ts_port_params]
        obj = sriov_nic_taas.SriovNicTaasDriver()
        obj.initialize()
        self.assertRaises(taas_exc.PciSlotNotFound, obj.delete_tap_flow,
                          tap_flow)
