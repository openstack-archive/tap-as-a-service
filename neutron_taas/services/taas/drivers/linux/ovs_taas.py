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


import re
import netaddr
from neutron.agent.common import ovs_lib
from neutron.agent.linux import utils
# from neutron.plugins.openvswitch.common import constants as ovs_consts
from neutron.plugins.ml2.drivers.openvswitch.agent.common import constants \
    as ovs_consts
from neutron_taas.services.taas.drivers import taas_base
from oslo_config import cfg
from oslo_log import log as logging
import ovs_constants as taas_ovs_consts
import ovs_utils as taas_ovs_utils

LOG = logging.getLogger(__name__)

TaaS_DRIVER_NAME = 'Taas OVS driver'

# Hard coding yet.
REMOTE_IPS = {'ps0101-c42-09': '172.16.0.31',
              'ps0101-c42-11': '172.16.0.33'}
TUNNEL_TYPE = 'vxlan'

def get_tunnel_ip(host):
    return REMOTE_IPS[host]


class OVSBridge_tap_extension(ovs_lib.OVSBridge):
    def __init__(self, br_name, root_helper, datapath_type=""):
        if datapath_type == "":
            super(OVSBridge_tap_extension, self).__init__(br_name)
        else:
            super(OVSBridge_tap_extension, self).__init__(br_name, datapath_type)


class OvsTaasDriver(taas_base.TaasDriverBase):
    def __init__(self, root_helper):
        LOG.debug("Initializing Taas OVS Driver")

        self.normal_action = "normal"
        self.root_helper = root_helper

        self.int_br = OVSBridge_tap_extension('br-int', self.root_helper)

        self.datapath_type = self.int_br.db_get_val("Bridge", "br-int",
                                                    "datapath_type")
        self.tap_br = OVSBridge_tap_extension('br-tap', self.root_helper,
                                              self.datapath_type)

        # Prepare OVS bridges for TaaS
        self.setup_ovs_bridges()

        # Setup key-value manager for ingress BCMC flows
        self.bcmc_kvm = taas_ovs_utils.key_value_mgr(4096)

        # Setup key-value manager for tap flows
        self.tap_kvm = taas_ovs_utils.key_value_mgr(4096)

    def setup_ovs_bridges(self):
        #
        # br-int : Integration Bridge
        # br-tap : Tap Bridge
        #

        # Create br-tap
        self.tap_br.create()

        # Connect br-tap to br-int
        self.int_br.add_patch_port('patch-int-tap', 'patch-tap-int')
        self.tap_br.add_patch_port('patch-tap-int', 'patch-int-tap')

        # Get patch port IDs
        patch_tap_int_id = self.tap_br.get_port_ofport('patch-tap-int')

        # Purge all existing Taas flows from br-tap
        self.tap_br.delete_flows(table=0)

        self.tap_br.add_flow(table=0,
                             priority=0,
                             actions="drop")
        return

    def create_tap_service(self, tap_service):
        LOG.debug("Entering create_tap_service")
        taas_id = tap_service['taas_id']
        port = tap_service['port']

        # Get OVS port id for tap service port
        ovs_port = self.int_br.get_vif_port_by_id(port['id'])
        ovs_port_name = ovs_port.port_name

        # Get VLAN id for tap service port
        port_dict = self.int_br.get_port_tag_dict()
        port_vlan_id = port_dict[ovs_port_name]

        external_ids = self.int_br.db_get_val("Interface", ovs_port_name,
                                              "external_ids")

        self.int_br.delete_port(ovs_port_name)
        self.tap_br.add_port(ovs_port_name, ('external_ids', external_ids))
        self.tap_br.set_db_attribute('Port', ovs_port_name, 'tag', port_vlan_id)

        ovs_port = self.tap_br.get_vif_port_by_id(port['id'])
        ovs_port_id = ovs_port.ofport

        # Add flow(s) in br-int
        self.add_vlan_submit_flow()

        # Add flow(s) in br-tap
        self.tap_br.add_flow(table=0,
                             priority=25,
                             dl_vlan=taas_id,
                             actions="output:%s" %
                             ovs_port_id)

        #
        # Disable mac-address learning in the Linux bridge to which
        # the OVS port is attached (via the veth pair). This will
        # effectively turn the bridge into a hub, ensuring that all
        # incoming mirrored traffic reaches the tap interface (used
        # for attaching a VM to the bridge) irrespective of the
        # destination mac addresses in mirrored packets.
        #
        linux_br_name = ovs_port_name.replace('qvo', 'qbr')
        utils.execute(['brctl', 'setageing', linux_br_name, 0],
                      run_as_root=True)

        return

    def delete_tap_service(self, tap_service):
        LOG.debug("Entering delete_tap_service")
        taas_id = tap_service['taas_id']
        port = tap_service['port']

        # Delete flow(s) from br-int
        self.del_vlan_submit_flow()

        # Delete flow(s) from br-tap
        self.tap_br.delete_flows(table=0,
                                 dl_vlan=taas_id)

        # Get OVS port id for tap service port
        ovs_port = self.tap_br.get_vif_port_by_id(port['id'])
        if ovs_port == None:
            return
        ovs_port_name = ovs_port.port_name

        # Get VLAN id for tap service port
        port_dict = self.tap_br.get_port_tag_dict()
        port_vlan_id = port_dict[ovs_port_name]

        external_ids = self.tap_br.db_get_val("Interface", ovs_port_name,
                                              "external_ids")

        self.tap_br.delete_port(ovs_port_name)
        self.int_br.add_port(ovs_port_name, ('external_ids', external_ids))
        self.int_br.set_db_attribute('Port', ovs_port_name, 'tag', port_vlan_id)

        return

    def create_tap_flow(self, tap_flow):
        LOG.debug("Entering create_tap_flow")
        taas_id = tap_flow['taas_id']
        port = tap_flow['port']
        direction = tap_flow['tap_flow']['direction']

        service_host = tap_flow['service_host']
        source_host = tap_flow['source_host']
        if service_host != source_host:
            service_ip = get_tunnel_ip(service_host)
            source_ip = get_tunnel_ip(source_host)
            if service_host == cfg.CONF.host:
                remote_ip = source_ip
            elif source_host == cfg.CONF.host:
                remote_ip = service_ip
            else:
                raise Exception('Source port and Service port are not on this host')

            tun_port_name = "%s-%s" % (TUNNEL_TYPE, self.get_ip_in_hex(remote_ip))
            local_ip = get_tunnel_ip(cfg.CONF.host)
            self.tap_br.add_tunnel_port(tun_port_name, remote_ip, local_ip,
                                        TUNNEL_TYPE)
            tun_port_id = self.tap_br.get_port_ofport(tun_port_name)
            patch_tap_int_id = self.tap_br.get_port_ofport('patch-tap-int')

            self.tap_br.add_flow(table=0,
                                 priority=20,
                                 in_port=patch_tap_int_id,
                                 dl_vlan=taas_id,
                                 actions="output:%s" % str(tun_port_id))

            tf = tap_flow['tap_flow']
            tap_flow_id = tf['id']

            self.tap_kvm.affiliate(taas_id, [tap_flow_id, source_host])

        if source_host == cfg.CONF.host:
            # Get OVS port id for tap flow port
            ovs_port = self.int_br.get_vif_port_by_id(port['id'])
            ovs_port_id = ovs_port.ofport

            # Get VLAN id for tap flow port
            port_dict = self.int_br.get_port_tag_dict()
            port_vlan_id = port_dict[ovs_port.port_name]

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
                self.int_br.add_flow(table=0,
                                     priority=20,
                                     dl_dst=port_mac,
                                     actions="%s,mod_vlan_vid:%s,output:%s" %
                                     (self.normal_action, str(taas_id), str(patch_int_tap_id)))

                self._add_update_ingress_bcmc_flow(port_vlan_id,
                                                   taas_id,
                                                   patch_int_tap_id)

        return

    def delete_tap_flow(self, tap_flow):
        LOG.debug("Entering delete_tap_flow")
        taas_id = tap_flow['taas_id']
        port = tap_flow['port']
        direction = tap_flow['tap_flow']['direction']

        service_host = tap_flow['service_host']
        source_host = tap_flow['source_host']
        if source_host == cfg.CONF.host: 
            # Get OVS port id for tap flow port
            ovs_port = self.int_br.get_vif_port_by_id(port['id'])
            ovs_port_id = ovs_port.ofport

            # Get VLAN id for tap flow port
            port_dict = self.int_br.get_port_tag_dict()
            port_vlan_id = port_dict[ovs_port.port_name]

            # Get patch port ID
            patch_int_tap_id = self.int_br.get_port_ofport('patch-int-tap')

            # Delete flow(s) from br-int
            if direction == 'OUT' or direction == 'BOTH':
                self.int_br.delete_flows(table=0,
                                         in_port=ovs_port_id)

            if direction == 'IN' or direction == 'BOTH':
                port_mac = tap_flow['port_mac']
                self.int_br.delete_flows(table=0,
                                         dl_dst=port_mac)

                self._del_update_ingress_bcmc_flow(port_vlan_id,
                                                   taas_id,
                                                   patch_int_tap_id)

        if service_host != source_host:
            tf = tap_flow['tap_flow']
            tap_flow_id = tf['id']
            self.tap_kvm.unaffiliate(taas_id, [tap_flow_id, source_host])

            for id, src in self.tap_kvm.list_affiliations(taas_id):
                if src == source_host:
                    LOG.debug("Do not remove tunnel in use.")
                    return
            LOG.debug("Remove tunnel")

            patch_tap_int_id = self.tap_br.get_port_ofport('patch-tap-int')
            self.tap_br.delete_flows(table=0,
                                     in_port=patch_tap_int_id,
                                     dl_vlan=taas_id)

            service_ip = get_tunnel_ip(service_host)
            source_ip = get_tunnel_ip(source_host)
            if service_host == cfg.CONF.host:
                remote_ip = source_ip
            elif source_host == cfg.CONF.host:
                remote_ip = service_ip
            else:
                raise Exception('Source port and Service port are not on this host')

            tun_port_name = "%s-%s" % (TUNNEL_TYPE, self.get_ip_in_hex(remote_ip))
            self.tap_br.delete_port(tun_port_name)

        return


    def add_update_vlan_submit_flow(self):
        LOG.debug("Entering add_update_vlan_submit_flow")
        if self.normal_action == "normal":
            return
        entries3 = dict()
        entries20 = dict()
        # Read current flow entries
        flows = self.int_br.dump_flows_for_table(0)
        for flow in flows.split('\n'):
            s = flow.split(" ")
            c1 = s[-2]
            LOG.debug("add_update_vlan_submit_flow: %s %s" % (s[-2], s[-1]))
            if re.match("priority=3", c1):
                c2 = re.sub("priority=\d+", "priority=20", c1)
                c3 = re.sub("in_port=\d+", "in_port=1000", c2)
                entries3[c3] = s[-1]
            elif re.match("priority=20,in_port=1000", c1):
                if c1 != "priority=20,in_port=1000":
                    entries20[c1] = s[-1]

        # Remove duplicated entries.
        for c in entries20.keys():
            if c in entries3:
                del entries20[c]
                del entries3[c]
        
        # Add new entries.
        for c in entries3.keys():
            cond = [t.split('=') for t in c.split(',')]
            actions = [entries3[c].split('=')]
            cond.extend(actions)
            self.int_br.add_flow(table=0, **dict(cond))

        # Delete obsolete entries.
        for c in entries20:
            cond = [t.split('=') for t in c.split(',')]
            self.delete_flows_strict("br-int", table=0, **dict(cond))

    def add_vlan_submit_flow(self):
        LOG.debug("Entering add_vlan_submit_flow")
        # Read current flow entries
        flows = self.int_br.dump_flows_for_table(0)
        for flow in flows.split('\n'):
            s = flow.split(" ")
            c1 = s[-2]
            if re.match("priority=3", c1):
                self.normal_action = "resubmit:1000"
                c2 = re.sub("priority=\d+", "priority=20", c1)
                c3 = re.sub("in_port=\d+", "in_port=1000", c2)
                cond = [t.split('=') for t in c3.split(',')]
                actions = [s[-1].split('=')]
                cond.extend(actions)
                self.int_br.add_flow(table=0, **dict(cond))
        if self.normal_action == "resubmit:1000":
            self.int_br.add_flow(table=0, priority=20,
                                 in_port=1000, actions="normal")

    def delete_flows_strict(self, br_name, **kwargs):
        LOG.debug("Entering delete_flows_strict")
        args = []
        for k, v in kwargs.items():
            args.append("%s=%s" % (k, v))
        full_args = ["ovs-ofctl", "del-flows", "--strict", br_name] + \
                    [",".join(args)]
        try:
            return utils.execute(full_args, run_as_root=True)
        except Exception as e:
            Log.error(e)
            raise e

    def del_vlan_submit_flow(self):
        LOG.debug("Entering del_vlan_submit_flow")
        self.delete_flows_strict("br-int", table=0, priority=20, in_port=1000)
        # Read current flow entries
        flows = self.int_br.dump_flows_for_table(0)
        for flow in flows.split('\n'):
            s = flow.split(" ")
            c1 = s[-2]
            if re.match("priority=3", c1):
                self.normal_action = "normal"
            elif re.match("priority=20", c1):
                cond = [t.split('=') for t in c1.split(',')]
                self.delete_flows_strict("br-int", table=0, **dict(cond))


    def _create_ingress_bcmc_flow_action(self, taas_id_list, out_port_id):
        if self.normal_action == None:
            flow_action = "normal"
        else:
            flow_action = self.normal_action
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
                                 dl_dst="01:00:00:00:00:00/01:00:00:00:00:00",
                                 actions=flow_action)
        else:
            self.int_br.delete_flows(table=0,
                                     dl_dst=("01:00:00:00:00:00/"
                                             "01:00:00:00:00:00"))

        return

    def get_ip_in_hex(self, ip_address):
        try:
            return '%08x' % netaddr.IPAddress(ip_address, version=4)
        except Exception:
            LOG.warn(_LW("Invalid remote IP: %s"), ip_address)
            return

