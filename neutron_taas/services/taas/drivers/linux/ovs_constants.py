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


# OVS tables used by TaaS in br-tap
TAAS_RECV_LOC = 1
TAAS_RECV_REM = 2

# OVS tables used by TaaS in br-tun
TAAS_SEND_UCAST = 30
TAAS_SEND_FLOOD = 31
TAAS_CLASSIFY = 35
TAAS_DST_CHECK = 36
TAAS_SRC_CHECK = 37
TAAS_DST_RESPOND = 38
TAAS_SRC_RESPOND = 39

# OVS TaaS extension driver type
EXTENSION_DRIVER_TYPE = 'ovs'
