# Copyright 2016 NEC Technologies India Pvt. Ltd.  All rights reserved.
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

from nutron_taas._i18n import _


TaasOpts = [
    cfg.StrOpt(
        'driver',
        default='',
        help=_("Name of the TaaS Driver")),
    cfg.BoolOpt(
        'enabled',
        default=False,
        help=_("Enable TaaS")),
]
cfg.CONF.register_opts(TaasOpts, 'taas')
