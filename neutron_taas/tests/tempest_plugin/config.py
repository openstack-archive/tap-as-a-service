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


taas_plugin_group = cfg.OptGroup(name='taas_plugin_options',
                                 title='TaaS Tempest Plugin Options')

TaaSPluginGroup = [
    cfg.StrOpt('provider_physical_network',
               default='',
               help='Physical network to be used for creating SRIOV network.'),
    cfg.StrOpt('provider_segmentation_id',
               default='',
               help='Segmentation-id to be used for creating SRIOV network.'),
    cfg.StrOpt('vlan_filter',
               default='',
               help='Comma separated list of VLANs to be mirrored '
                    'for a Tap-Flow.'),
]
