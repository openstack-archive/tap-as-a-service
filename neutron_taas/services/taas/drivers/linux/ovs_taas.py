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


from neutron.agent.common import ovs_lib
from neutron.agent.linux import utils
from neutron.conf.agent import common
# from neutron.plugins.openvswitch.common import constants as ovs_consts
from neutron.plugins.ml2.drivers.openvswitch.agent.common import constants \
    as ovs_consts
from neutron_taas.services.taas.agents.extensions import taas as taas_base
from oslo_config import cfg
from oslo_log import log as logging
import ovs_constants as taas_ovs_consts
import ovs_utils as taas_ovs_utils

LOG = logging.getLogger(__name__)

TaaS_DRIVER_NAME = 'Taas OVS driver'


class OVSBridge_tap_extension(ovs_lib.OVSBridge):
    def __init__(self, br_name, root_helper):
        super(OVSBridge_tap_extension, self).__init__(br_name)


class OvsTaasDriver(taas_base.TaasAgentDriver):
    def __init__(self):
        super(OvsTaasDriver, self).__init__()
        LOG.debug("Initializing Taas OVS Driver")
        self.agent_api = None
        self.root_helper = common.get_root_helper(cfg.CONF)

    def initialize(self):
        self.int_br = self.agent_api.request_int_br()
        self.tun_br = self.agent_api.request_tun_br()
        self.tap_br = OVSBridge_tap_extension('br-tap', self.root_helper)

        # Prepare OVS bridges for TaaS
        self.setup_ovs_bridges()

        # Setup key-value manager for ingress BCMC flows
        self.bcmc_kvm = taas_ovs_utils.key_value_mgr(4096)

    def setup_ovs_bridges(self):
        #
        # br-int : Integration Bridge
        # br-tap : Tap Bridge
        # br-tun : Tunnel Bridge
        #

        # Create br-tap
        self.tap_br.create()

        # Connect br-tap to br-int and br-tun
        self.int_br.add_patch_port('patch-int-tap', 'patch-tap-int')
        self.tap_br.add_patch_port('patch-tap-int', 'patch-int-tap')
        self.tun_br.add_patch_port('patch-tun-tap', 'patch-tap-tun')
        self.tap_br.add_patch_port('patch-tap-tun', 'patch-tun-tap')

        # Get patch port IDs
        patch_tap_int_id = self.tap_br.get_port_ofport('patch-tap-int')
        patch_tap_tun_id = self.tap_br.get_port_ofport('patch-tap-tun')
        patch_tun_tap_id = self.tun_br.get_port_ofport('patch-tun-tap')

        # Purge all existing Taas flows from br-tap and br-tun
        self.tap_br.delete_flows(table=0)
        self.tap_br.delete_flows(table=taas_ovs_consts.TAAS_RECV_LOC)
        self.tap_br.delete_flows(table=taas_ovs_consts.TAAS_RECV_REM)

        self.tun_br.delete_flows(table=0,
                                 in_port=patch_tun_tap_id)
        self.tun_br.delete_flows(table=taas_ovs_consts.TAAS_SEND_UCAST)
        self.tun_br.delete_flows(table=taas_ovs_consts.TAAS_SEND_FLOOD)
        self.tun_br.delete_flows(table=taas_ovs_consts.TAAS_CLASSIFY)
        self.tun_br.delete_flows(table=taas_ovs_consts.TAAS_DST_CHECK)
        self.tun_br.delete_flows(table=taas_ovs_consts.TAAS_SRC_CHECK)
        self.tun_br.delete_flows(table=taas_ovs_consts.TAAS_DST_RESPOND)
        self.tun_br.delete_flows(table=taas_ovs_consts.TAAS_SRC_RESPOND)

        #
        # Configure standard TaaS flows in br-tap
        #
        self.tap_br.add_flow(table=0,
                             priority=1,
                             in_port=patch_tap_int_id,
                             actions="resubmit(,%s)" %
                             taas_ovs_consts.TAAS_RECV_LOC)

        self.tap_br.add_flow(table=0,
                             priority=1,
                             in_port=patch_tap_tun_id,
                             actions="resubmit(,%s)" %
                             taas_ovs_consts.TAAS_RECV_REM)

        self.tap_br.add_flow(table=0,
                             priority=0,
                             actions="drop")

        self.tap_br.add_flow(table=taas_ovs_consts.TAAS_RECV_LOC,
                             priority=0,
                             actions="output:%s" % str(patch_tap_tun_id))

        self.tap_br.add_flow(table=taas_ovs_consts.TAAS_RECV_REM,
                             priority=0,
                             actions="drop")

        #
        # Configure standard Taas flows in br-tun
        #
        self.tun_br.add_flow(table=0,
                             priority=1,
                             in_port=patch_tun_tap_id,
                             actions="resubmit(,%s)" %
                             taas_ovs_consts.TAAS_SEND_UCAST)

        self.tun_br.add_flow(table=taas_ovs_consts.TAAS_SEND_UCAST,
                             priority=0,
                             actions="resubmit(,%s)" %
                             taas_ovs_consts.TAAS_SEND_FLOOD)

        flow_action = self._create_tunnel_flood_flow_action()
        if flow_action != "":
            self.tun_br.add_flow(table=taas_ovs_consts.TAAS_SEND_FLOOD,
                                 priority=0,
                                 actions=flow_action)

        self.tun_br.add_flow(table=taas_ovs_consts.TAAS_CLASSIFY,
                             priority=2,
                             reg0=0,
                             actions="resubmit(,%s)" %
                             taas_ovs_consts.TAAS_DST_CHECK)

        self.tun_br.add_flow(table=taas_ovs_consts.TAAS_CLASSIFY,
                             priority=1,
                             reg0=1,
                             actions="resubmit(,%s)" %
                             taas_ovs_consts.TAAS_DST_CHECK)

        self.tun_br.add_flow(table=taas_ovs_consts.TAAS_CLASSIFY,
                             priority=1,
                             reg0=2,
                             actions="resubmit(,%s)" %
                             taas_ovs_consts.TAAS_SRC_CHECK)

        self.tun_br.add_flow(table=taas_ovs_consts.TAAS_DST_CHECK,
                             priority=0,
                             actions="drop")

        self.tun_br.add_flow(table=taas_ovs_consts.TAAS_SRC_CHECK,
                             priority=0,
                             actions="drop")

        self.tun_br.add_flow(table=taas_ovs_consts.TAAS_DST_RESPOND,
                             priority=2,
                             reg0=0,
                             actions="output:%s" % str(patch_tun_tap_id))

        self.tun_br.add_flow(table=taas_ovs_consts.TAAS_DST_RESPOND,
                             priority=1,
                             reg0=1,
                             actions=(
                                 "output:%s,"
                                 "move:NXM_OF_VLAN_TCI[0..11]->NXM_NX_TUN_ID"
                                 "[0..11],mod_vlan_vid:2,output:in_port" %
                                 str(patch_tun_tap_id)))

        self.tun_br.add_flow(table=taas_ovs_consts.TAAS_SRC_RESPOND,
                             priority=1,
                             actions=(
                                 "learn(table=%s,hard_timeout=60,"
                                 "priority=1,NXM_OF_VLAN_TCI[0..11],"
                                 "load:NXM_OF_VLAN_TCI[0..11]->NXM_NX_TUN_ID"
                                 "[0..11],load:0->NXM_OF_VLAN_TCI[0..11],"
                                 "output:NXM_OF_IN_PORT[])" %
                                 taas_ovs_consts.TAAS_SEND_UCAST))

        return

    def consume_api(self, agent_api):
        self.agent_api = agent_api

    def create_tap_service(self, tap_service):
        taas_id = tap_service['taas_id']
        port = tap_service['port']

        # Get OVS port id for tap service port
        ovs_port = self.int_br.get_vif_port_by_id(port['id'])
        ovs_port_id = ovs_port.ofport

        # Get VLAN id for tap service port
        port_dict = self.int_br.get_port_tag_dict()
        port_vlan_id = port_dict[ovs_port.port_name]

        # Get patch port IDs
        patch_int_tap_id = self.int_br.get_port_ofport('patch-int-tap')
        patch_tap_int_id = self.tap_br.get_port_ofport('patch-tap-int')

        # Add flow(s) in br-int
        self.int_br.add_flow(table=0,
                             priority=25,
                             in_port=patch_int_tap_id,
                             dl_vlan=taas_id,
                             actions="mod_vlan_vid:%s,output:%s" %
                             (str(port_vlan_id), str(ovs_port_id)))

        # Add flow(s) in br-tap
        self.tap_br.add_flow(table=taas_ovs_consts.TAAS_RECV_LOC,
                             priority=1,
                             dl_vlan=taas_id,
                             actions="output:in_port")

        self.tap_br.add_flow(table=taas_ovs_consts.TAAS_RECV_REM,
                             priority=1,
                             dl_vlan=taas_id,
                             actions="output:%s" % str(patch_tap_int_id))

        # Add flow(s) in br-tun
        for tunnel_type in ovs_consts.TUNNEL_NETWORK_TYPES:
            self.tun_br.add_flow(table=ovs_consts.TUN_TABLE[tunnel_type],
                                 priority=1,
                                 tun_id=taas_id,
                                 actions=(
                                     "move:NXM_OF_VLAN_TCI[0..11]->"
                                     "NXM_NX_REG0[0..11],move:NXM_NX_TUN_ID"
                                     "[0..11]->NXM_OF_VLAN_TCI[0..11],"
                                     "resubmit(,%s)" %
                                     taas_ovs_consts.TAAS_CLASSIFY))

        self.tun_br.add_flow(table=taas_ovs_consts.TAAS_DST_CHECK,
                             priority=1,
                             tun_id=taas_id,
                             actions="resubmit(,%s)" %
                             taas_ovs_consts.TAAS_DST_RESPOND)

        #
        # Disable mac-address learning in the Linux bridge to which
        # the OVS port is attached (via the veth pair). This will
        # effectively turn the bridge into a hub, ensuring that all
        # incoming mirrored traffic reaches the tap interface (used
        # for attaching a VM to the bridge) irrespective of the
        # destination mac addresses in mirrored packets.
        #
        ovs_port_name = ovs_port.port_name
        linux_br_name = ovs_port_name.replace('qvo', 'qbr')
        utils.execute(['brctl', 'setageing', linux_br_name, 0],
                      run_as_root=True)

        return

    def delete_tap_service(self, tap_service):
        taas_id = tap_service['taas_id']

        # Get patch port ID
        patch_int_tap_id = self.int_br.get_port_ofport('patch-int-tap')

        # Delete flow(s) from br-int
        self.int_br.delete_flows(table=0,
                                 in_port=patch_int_tap_id,
                                 dl_vlan=taas_id)

        # Delete flow(s) from br-tap
        self.tap_br.delete_flows(table=taas_ovs_consts.TAAS_RECV_LOC,
                                 dl_vlan=taas_id)

        self.tap_br.delete_flows(table=taas_ovs_consts.TAAS_RECV_REM,
                                 dl_vlan=taas_id)

        # Delete flow(s) from br-tun
        for tunnel_type in ovs_consts.TUNNEL_NETWORK_TYPES:
            self.tun_br.delete_flows(table=ovs_consts.TUN_TABLE[tunnel_type],
                                     tun_id=taas_id)

        self.tun_br.delete_flows(table=taas_ovs_consts.TAAS_DST_CHECK,
                                 tun_id=taas_id)

        self.tun_br.delete_flows(table=taas_ovs_consts.TAAS_SRC_CHECK,
                                 tun_id=taas_id)

        return

    def create_tap_flow(self, tap_flow):
        taas_id = tap_flow['taas_id']
        port = tap_flow['port']
        direction = tap_flow['tap_flow']['direction']

        # Get OVS port id for tap flow port
        ovs_port = self.int_br.get_vif_port_by_id(port['id'])
        ovs_port_id = ovs_port.ofport

        # Get patch port ID
        patch_int_tap_id = self.int_br.get_port_ofport('patch-int-tap')

        # Add flow(s) in br-int
        if direction == 'OUT' or direction == 'BOTH':
            self.int_br.add_flow(table=0,
                                 priority=20,
                                 in_port=ovs_port_id,
                                 actions="normal,mod_vlan_vid:%s,output:%s" %
                                 (str(taas_id), str(patch_int_tap_id)))

        if direction == 'IN' or direction == 'BOTH':
            port_mac = tap_flow['port_mac']

            #
            # Note: The ingress side flow (for unicast traffic) should
            #       include a check for the 'VLAN id of the Neutron
            #       network the port belongs to' + 'MAC address of the
            #       port', to comply with the requirement that port MAC
            #       addresses are unique only within a Neutron network.
            #       Unfortunately, at the moment there is no clean way
            #       to implement such a check, given OVS's handling of
            #       VLAN tags and Neutron's use of the NORMAL action in
            #       br-int.
            #
            #       We are therefore temporarily disabling the VLAN id
            #       check until a mechanism is available to implement
            #       it correctly. The {broad,multi}cast flow, which is
            #       also dependent on the VLAN id, has been disabled
            #       for the same reason.
            #

            # Get VLAN id for tap flow port
            # port_dict = self.int_br.get_port_tag_dict()
            # port_vlan_id = port_dict[ovs_port.port_name]

            self.int_br.add_flow(table=0,
                                 priority=20,
                                 # dl_vlan=port_vlan_id,
                                 dl_dst=port_mac,
                                 actions="normal,mod_vlan_vid:%s,output:%s" %
                                 (str(taas_id), str(patch_int_tap_id)))

            # self._add_update_ingress_bcmc_flow(port_vlan_id,
            #                                    taas_id,
            #                                    patch_int_tap_id)

        # Add flow(s) in br-tun
        for tunnel_type in ovs_consts.TUNNEL_NETWORK_TYPES:
            self.tun_br.add_flow(table=ovs_consts.TUN_TABLE[tunnel_type],
                                 priority=1,
                                 tun_id=taas_id,
                                 actions=(
                                     "move:NXM_OF_VLAN_TCI[0..11]->"
                                     "NXM_NX_REG0[0..11],move:NXM_NX_TUN_ID"
                                     "[0..11]->NXM_OF_VLAN_TCI[0..11],"
                                     "resubmit(,%s)" %
                                     taas_ovs_consts.TAAS_CLASSIFY))

        self.tun_br.add_flow(table=taas_ovs_consts.TAAS_SRC_CHECK,
                             priority=1,
                             tun_id=taas_id,
                             actions="resubmit(,%s)" %
                             taas_ovs_consts.TAAS_SRC_RESPOND)

        return

    def delete_tap_flow(self, tap_flow):
        port = tap_flow['port']
        direction = tap_flow['tap_flow']['direction']

        # Get OVS port id for tap flow port
        ovs_port = self.int_br.get_vif_port_by_id(port['id'])
        ovs_port_id = ovs_port.ofport

        # Delete flow(s) from br-int
        if direction == 'OUT' or direction == 'BOTH':
            self.int_br.delete_flows(table=0,
                                     in_port=ovs_port_id)

        if direction == 'IN' or direction == 'BOTH':
            port_mac = tap_flow['port_mac']

            #
            # The VLAN id related checks have been temporarily disabled.
            # Please see comment in create_tap_flow() for details.
            #

            # taas_id = tap_flow['taas_id']

            # Get VLAN id for tap flow port
            # port_dict = self.int_br.get_port_tag_dict()
            # port_vlan_id = port_dict[ovs_port.port_name]

            # Get patch port ID
            # patch_int_tap_id = self.int_br.get_port_ofport('patch-int-tap')

            self.int_br.delete_flows(table=0,
                                     # dl_vlan=port_vlan_id,
                                     dl_dst=port_mac)

            # self._del_update_ingress_bcmc_flow(port_vlan_id,
            #                                    taas_id,
            #                                    patch_int_tap_id)

        return

    def update_tunnel_flood_flow(self):
        flow_action = self._create_tunnel_flood_flow_action()
        if flow_action != "":
            self.tun_br.mod_flow(table=taas_ovs_consts.TAAS_SEND_FLOOD,
                                 actions=flow_action)

    def _create_tunnel_flood_flow_action(self):

        args = ["ovs-vsctl", "list-ports", "br-tun"]
        res = utils.execute(args, run_as_root=True)

        port_name_list = res.splitlines()

        flow_action = ("move:NXM_OF_VLAN_TCI[0..11]->NXM_NX_TUN_ID[0..11],"
                       "mod_vlan_vid:1")

        tunnel_ports_exist = False

        for port_name in port_name_list:
            if (port_name != 'patch-int') and (port_name != 'patch-tun-tap'):
                flow_action += (",output:%d" %
                                self.tun_br.get_port_ofport(port_name))
                tunnel_ports_exist = True

        if tunnel_ports_exist:
            return flow_action
        else:
            return ""

    def _create_ingress_bcmc_flow_action(self, taas_id_list, out_port_id):
        flow_action = "normal"
        for taas_id in taas_id_list:
                flow_action += (",mod_vlan_vid:%d,output:%d" %
                                (taas_id, out_port_id))

        return flow_action

    #
    # Adds or updates a special flow in br-int to mirror (duplicate and
    # redirect to 'out_port_id') all ingress broadcast/multicast traffic,
    # associated with a VLAN, to possibly multiple tap service instances.
    #
    def _add_update_ingress_bcmc_flow(self, vlan_id, taas_id, out_port_id):
        # Add a tap service instance affiliation with VLAN
        self.bcmc_kvm.affiliate(vlan_id, taas_id)

        # Find all tap service instances affiliated with VLAN
        taas_id_list = self.bcmc_kvm.list_affiliations(vlan_id)

        #
        # Add/update flow to mirror ingress BCMC traffic, associated
        # with VLAN, to all affiliated tap-service instances.
        #
        flow_action = self._create_ingress_bcmc_flow_action(taas_id_list,
                                                            out_port_id)
        self.int_br.add_flow(table=0,
                             priority=20,
                             dl_vlan=vlan_id,
                             dl_dst="01:00:00:00:00:00/01:00:00:00:00:00",
                             actions=flow_action)

        return

    #
    # Removes or updates a special flow in br-int to mirror (duplicate
    # and redirect to 'out_port_id') all ingress broadcast/multicast
    # traffic, associated with a VLAN, to possibly multiple tap-service
    # instances.
    #
    def _del_update_ingress_bcmc_flow(self, vlan_id, taas_id, out_port_id):
        # Remove a tap-service instance affiliation with VLAN
        self.bcmc_kvm.unaffiliate(vlan_id, taas_id)

        # Find all tap-service instances affiliated with VLAN
        taas_id_list = self.bcmc_kvm.list_affiliations(vlan_id)

        #
        # If there are tap service instances affiliated with VLAN, update
        # the flow to mirror ingress BCMC traffic, associated with VLAN,
        # to all of them. Otherwise, remove the flow.
        #
        if taas_id_list:
            flow_action = self._create_ingress_bcmc_flow_action(taas_id_list,
                                                                out_port_id)
            self.int_br.add_flow(table=0,
                                 priority=20,
                                 dl_vlan=vlan_id,
                                 dl_dst="01:00:00:00:00:00/01:00:00:00:00:00",
                                 actions=flow_action)
        else:
            self.int_br.delete_flows(table=0,
                                     dl_vlan=vlan_id,
                                     dl_dst=("01:00:00:00:00:00/"
                                             "01:00:00:00:00:00"))

        return
