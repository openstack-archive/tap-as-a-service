# Copyright (c) 2018 AT&T Corporation
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

from oslo_config import cfg
from tempest import config


CONF = config.CONF


TaasPluginOptGroup = cfg.OptGroup(name='taas_plugin_options',
                                  title='TaaS Tempest Plugin Config')

TaaSPluginOptions = [
    cfg.ListOpt('sriov_vlans',
                default=[],
                help='List of VLANs to be configured for sriov network.'),
    cfg.ListOpt('vlan_filter',
                default=[],
                help='List of VLANs to be mirrored for a Tap-Flow.'),
]

