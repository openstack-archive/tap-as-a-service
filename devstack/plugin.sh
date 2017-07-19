#!/bin/bash

# Copyright 2015 Midokura SARL
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# This script is meant to be sourced from devstack.  It is a wrapper of
# devmido scripts that allows proper exporting of environment variables.


function install_taas {
    pip_install --no-deps --editable $TAAS_PLUGIN_PATH
}

function configure_taas_plugin {
    if [ ! -d $NEUTRON_CONF_DIR ]; then
        _create_neutron_conf_dir
    fi
    cp $TAAS_PLUGIN_PATH/etc/taas_plugin.ini $TAAS_PLUGIN_CONF_FILE
    neutron_server_config_add $TAAS_PLUGIN_CONF_FILE
    _neutron_service_plugin_class_add taas
}

if is_service_enabled taas; then
    if [[ "$1" == "stack" ]]; then
        if [[ "$2" == "pre-install" ]]; then
            :
        elif [[ "$2" == "install" ]]; then
            install_taas
            configure_taas_plugin
        elif [[ "$2" == "post-config" ]]; then
            neutron-db-manage --subproject tap-as-a-service upgrade head
            echo "Configuring taas"
            if [ "$TAAS_SERVICE_DRIVER" ]; then
                inicomment $TAAS_PLUGIN_CONF_FILE service_providers service_provider
                iniadd $TAAS_PLUGIN_CONF_FILE service_providers service_provider $TAAS_SERVICE_DRIVER

                if is_service_enabled q-agt neutron-agent; then
                    source $NEUTRON_DIR/devstack/lib/l2_agent
                    plugin_agent_add_l2_agent_extension taas
                    configure_l2_agent
                fi
            fi
        elif [[ "$2" == "extra" ]]; then
            :
        fi
    elif [[ "$1" == "unstack" ]]; then
	:
    fi
fi
