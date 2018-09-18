# Copyright (c) 2018 AT&T Corporation
# Copyright (c) 2015 Midokura SARL
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from oslo_log import log as logging
from tempest.common import utils
from tempest import config
from tempest.lib import decorators

from neutron_taas.tests.tempest_plugin.tests.scenario import base

CONF = config.CONF
LOG = logging.getLogger(__name__)


class TestTaaS(base.TaaSScenarioTest):
    """Config Requirement in tempest.conf:

    - project_network_cidr_bits- specifies the subnet range for each network
    - project_network_cidr
    - public_network_id.
    """

    @classmethod
    def resource_setup(cls):
        LOG.debug("Initializing TaaSScenarioTest Setup")
        super(TestTaaS, cls).resource_setup()
        required_exts = ['taas', 'security-group', 'router']
        for ext in required_exts:
            if not utils.is_extension_enabled(ext, 'network'):
                msg = "%s Extension not enabled." % ext
                raise cls.skipException(msg)
        LOG.debug("TaaSScenarioTest Setup done.")

    def _create_server(self, network, security_group=None):
        keys = self.create_keypair()
        kwargs = {}
        if security_group is not None:
            kwargs['security_groups'] = [{'name': security_group['name']}]
        server = self.create_server(
            key_name=keys['name'],
            networks=[{'uuid': network['id']}],
            wait_until='ACTIVE',
            **kwargs)
        return server, keys

    def _create_test_server(self, network, security_group):
        pub_network_id = CONF.network.public_network_id
        server, keys = self._create_server(
            network, security_group=security_group)
        private_key = keys['private_key']
        vnic_type = CONF.network.port_vnic_type
        server_floating_ip = None
        if vnic_type != 'direct':
            server_floating_ip = self.create_floating_ip(server,
                                                         pub_network_id)
        fixed_ip = list(server['addresses'].values())[0][0]['addr']
        return server, private_key, fixed_ip, server_floating_ip

    def _create_topology(self):
        """Topology

        +----------+             +----------+
        | "server" |             | "server" |
        |  VM-1    |             |  VM-2    |
        |          |             |          |
        +----+-----+             +----+-----+
             |                        |
             |                        |
        +----+----+----+----+----+----+-----+
                            |
                            |
                            |
                     +------+------+
                     | "server"    |
                     | tap-service |
                     +-------------+
        """
        LOG.debug('Starting Topology Creation')
        resp = {}
        # Create Network1 and Subnet1.
        self.network1, self.subnet1, self.router1 = self.create_networks()
        resp['network1'] = self.network1
        resp['subnet1'] = self.subnet1
        resp['router1'] = self.router1

        # Create a security group allowing icmp and ssh traffic.
        security_group = self._create_security_group()

        # Create 3 VMs and assign them a floating IP each.
        server1, private_key1, server_fixed_ip_1, server_floating_ip_1 = (
            self._create_test_server(self.network1, security_group))
        server2, private_key2, server_fixed_ip_2, server_floating_ip_2 = (
            self._create_test_server(self.network1, security_group))
        server3, private_key3, server_fixed_ip_3, server_floating_ip_3 = (
            self._create_test_server(self.network1, security_group))

        # Store the received information to be used later
        resp['server1'] = server1
        resp['private_key1'] = private_key1
        resp['server_fixed_ip_1'] = server_fixed_ip_1
        resp['server_floating_ip_1'] = server_floating_ip_1

        resp['server2'] = server2
        resp['private_key2'] = private_key2
        resp['server_fixed_ip_2'] = server_fixed_ip_2
        resp['server_floating_ip_2'] = server_floating_ip_2

        resp['server3'] = server3
        resp['private_key3'] = private_key3
        resp['server_fixed_ip_3'] = server_fixed_ip_3
        resp['server_floating_ip_3'] = server_floating_ip_3

        return resp

    @decorators.idempotent_id('40903cbd-0e3c-464d-b311-dc77d3894e65')
    def test_tap_flow_data_mirroring(self):
        topology = self._create_topology()

        # Fetch source port and tap-service port to be used for creating
        # Tap Service and Tap flow.
        source_port = self.os_admin.ports_client.list_ports(
            network_id=topology['network1']['id'],
            device_id=topology['server1']['id']
            )['ports'][0]

        tap_service_port = self.os_admin.ports_client.list_ports(
            network_id=topology['network1']['id'],
            device_id=topology['server3']['id']
            )['ports'][0]

        # Create Tap-Service.
        tap_service = self.create_tap_service(port_id=tap_service_port['id'])

        LOG.debug('TaaS Config options: vlan-filter: %s' %
                  CONF.taas_plugin_options.vlan_filter)

        # Create Tap-Flow.
        vnic_type = CONF.network.port_vnic_type
        vlan_filter = None
        if vnic_type == 'direct':
            vlan_filter = CONF.taas_plugin_options.vlan_filter

        self.create_tap_flow(tap_service_id=tap_service['id'],
                             direction='BOTH', source_port=source_port['id'],
                             vlan_filter=vlan_filter)
