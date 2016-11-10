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
    _neutron_service_plugin_class_add taas
}

function configure_taas_openvswitch_agent {
    local conf=$TAAS_OVS_AGENT_CONF_FILE

    cp $TAAS_PLUGIN_PATH/etc/taas.ini $conf
    iniset $conf taas driver neutron_taas.services.taas.drivers.linux.ovs_taas.OvsTaasDriver
    iniset $conf taas enabled True
    iniset $conf taas vlan_range_start 3000
    iniset $conf taas vlan_range_end 3500
}

function start_taas_openvswitch_agent {
    run_process taas_openvswitch_agent "python $TAAS_OVS_AGENT_BINARY --config-file $NEUTRON_CONF --config-file $TAAS_OVS_AGENT_CONF_FILE"
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
            fi
        elif [[ "$2" == "extra" ]]; then
            :
        fi
    elif [[ "$1" == "unstack" ]]; then
        :
    fi
fi

if is_service_enabled taas_openvswitch_agent; then
    if [[ "$1" == "stack" ]]; then
        if [[ "$2" == "pre-install" ]]; then
            :
        elif [[ "$2" == "install" ]]; then
            install_taas
        elif [[ "$2" == "post-config" ]]; then
            configure_taas_openvswitch_agent
        elif [[ "$2" == "extra" ]]; then
            # NOTE(yamamoto): This agent should be run after ovs-agent
            # sets up its bridges.  (bug 1515104)
            start_taas_openvswitch_agent
        fi
    elif [[ "$1" == "unstack" ]]; then
        :
    fi
fi

### for taas-dashboard

function neutron_taas_dashboard_install {
    setup_develop $NEUTRON_TAAS_DASHBOARD_DIR
}

function neutron_taas_dashboard_configure {
    cp $NEUTRON_TAAS_DASHBOARD_ENABLE_FILE \
        $HORIZON_DIR/openstack_dashboard/local/enabled/

    local local_settings=$HORIZON_DIR/openstack_dashboard/local/local_settings.py
    _horizon_config_set $local_settings "" \
        'HORIZON_CONFIG["customization_module"]' \
        '"neutron_taas_dashboard.dashboards.project.tapservices.overrides"'
}

if is_service_enabled horizon && is_service_enabled taas && is_service_enabled neutron_taas_dashboard; then
    if [[ "$1" == "stack" && "$2" == "install" ]]; then
        # Perform installation of service source
        echo_summary "Installing neutron-taas-dashboard"
        neutron_taas_dashboard_install
    elif [[ "$1" == "stack" && "$2" == "post-config" ]]; then
        echo_summary "Configuring neutron-taas-dashboard"
        neutron_taas_dashboard_configure
    elif [[ "$1" == "stack" && "$2" == "extra" ]]; then
        # Initialize and start the TaaS service
        echo_summary "Initializing neutron-taas-dashboard"
    fi
fi

if [[ "$1" == "unstack" ]]; then
    # Shut down TaaS dashboard services
    :
fi

if [[ "$1" == "clean" ]]; then
    # Remove state and transient data
    # Remember clean.sh first calls unstack.sh

    # Remove taas-dashboard enabled file and pyc
    # rm -f ${NEUTRON_TAAS_DASHBOARD_ENABLE_FILE}*
    ENABLE_FILE="${NEUTRON_TAAS_DASHBOARD_ENABLE_FILE##*/}"
    rm -f ${NEUTRON_TAAS_DASHBOARD_ENABLE_FILE}/$ENABLE_FILE*
fi
