# Copyright (c) 2016 Midokura SARL
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

import subprocess
import sys

from neutron_lib import constants as lib_const
import os_client_config
from oslo_config import cfg
from oslo_log import log as logging
from oslo_utils import excutils

from neutron.agent.common import config
from neutron.agent.linux import interface
from neutron.common import utils as n_utils

from neutron_taas._i18n import _, _LE

LOG = logging.getLogger(__name__)
NAME = 'taas-tcpdump'


OPTS = [
    cfg.StrOpt('port', help=_('Neutron Port ID to tap')),
]


class _Wrap(object):
    def __init__(self, d):
        self.__dict__.update(d)

    def __getitem__(self, key):
        return self.__dict__[key]


def load_vif_driver(conf):
    try:
        vif_driver_class = n_utils.load_class_by_alias_or_classname(
            'neutron.interface_drivers', conf.interface_driver)
    except ImportError:
        with excutils.save_and_reraise_exception():
            LOG.error(_LE('Error importing interface driver: %s'),
                      conf.interface_driver)
    return vif_driver_class(conf)


def main():
    cfg.CONF.register_cli_opts(OPTS)
    config.register_interface_driver_opts_helper(cfg.CONF)
    cfg.CONF.register_opts(interface.OPTS)
    cfg.CONF(sys.argv[1:], project=NAME)
    logging.setup(cfg.CONF, NAME)

    network_client = os_client_config.make_client('network')

    port = None
    network = None
    tap_service = None
    tap_flow = None
    have_vif = False
    try:
        network = network_client.create_network({
            'network': {
                'name': NAME,
            },
        })['network']
        LOG.debug("network: %s", network['id'])

        device_owner = lib_const.DEVICE_OWNER_COMPUTE_PREFIX + NAME
        port = network_client.create_port({
            'port': {
                'name': NAME,
                'fixed_ips': [],
                'network_id': network['id'],
                'device_owner': device_owner,
                'port_security_enabled': False,
            },
        })['port']
        LOG.debug("port: %s", port['id'])

        vif_driver = load_vif_driver(cfg.CONF)
        prefix = 'ts-'
        interface_name = (prefix + port['id'])[:vif_driver.DEV_NAME_LEN]
        vif_driver.plug(network['id'], port['id'], interface_name,
                        port['mac_address'], prefix=prefix)
        LOG.debug("interface_name: %s", interface_name)
        have_vif = True

        tap_service = network_client.create_tap_service({
            'tap_service': {
                'name': NAME,
                'port_id': port['id'],
            },
        })['tap_service']
        LOG.debug("tap_service: %s", tap_service)

        tap_flow = network_client.create_tap_flow({
            'tap_flow': {
                'name': NAME,
                'tap_service_id': tap_service['id'],
                'source_port': cfg.CONF.port,
                'direction': 'BOTH',
            },
        })['tap_flow']
        LOG.debug("tap_flow: %s", tap_flow)

        subprocess.call(['sudo', 'tcpdump', '-npi', interface_name])

    finally:
        if tap_flow:
            network_client.delete_tap_flow(tap_flow['id'])
        if tap_service:
            network_client.delete_tap_service(tap_service['id'])
        if have_vif:
            vif_driver.unplug(interface_name)
        if port:
            network_client.delete_port(port['id'])
        if network:
            network_client.delete_network(network['id'])
