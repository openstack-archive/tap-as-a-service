#!/bin/bash

# Command and Devstack path are mandatory and sql password is only required
# when the command is install
COMMAND=$1
DEVSTACK_PATH=$2
MYSQL_PASS=$3

if [ -z $COMMAND ] || [ -z $DEVSTACK_PATH ]; then
    echo "Usage: $0 <install_plugin|install_agent|run_agent> <devstack install path> [mysql password]"
    exit 1
fi

if [ "$COMMAND" != "install_plugin" ] && [ "$COMMAND" != "install_agent" ] && [ "$COMMAND" != "run_agent" ]; then
    echo "Usage: $0 <install_plugin|install_agent|run_agent> <devstack install path> [mysql password]"
    exit 1
fi

# Switch on the command

if [ "$COMMAND" = "install_plugin" ] || [ "$COMMAND" = "install_agent" ]; then
    # Check if mysql password has been provided if the case is install_plugin
    if [ "$COMMAND" = "install_plugin" ] && [ -z $MYSQL_PASS  ]; then
        echo "Please provide the mysql password with the install_plugin command\n"
        echo "Usage: $0 <install_plugin|install_agent|run_agent> <devstack install path> [mysql password]"
        exit 1
    fi

    # Copy the neutron_taas folder into the devstack neutron folder
    cp -r ./neutron_taas $DEVSTACK_PATH
    if [ $? = 0 ]; then
        echo "Copied the neutron_taas directory..."
    else
        echo "Install failed while copying neturon_taas"
        exit 1
    fi

    cp ./neutron_taas/neutron_dependencies/repos.py $DEVSTACK_PATH/neutron/common/repos.py
    if [ $? = 0 ]; then
        echo "Copied the common/repos.py file...."
    else
        echo "Install failed while copying repos.py file"
        exit 1
    fi

    # patch the neutron.conf file to support TaaS plugin
    ./neutron_taas/neutron_dependencies/patch_conf_file.sh ./neutron_taas/neutron_dependencies/taas.conf /etc/neutron/neutron.conf
    if [ $? = 0 ]; then
        echo "Patched the neutron.conf file...."
    else
        echo "Install failed while patching the neutron.conf file"
        exit 1
    fi

    #invoke the database creator script
    if [ "$COMMAND" = "install_plugin" ]; then
        /usr/bin/python ./neutron_taas/neutron_dependencies/neutron_taas_db_init.py $MYSQL_PASS
        if [ $? = 0 ]; then
            echo "Created the DB schema required for TaaS...."
        else
            echo "Install failed while creating DB schema for TaaS"
            exit 1
        fi
    fi

    # Install the taas_cli
    sudo ln -s $DEVSTACK_PATH/neutron_taas/taas_cli/taas_cli.py /usr/local/bin/taas
    if [ $? = 0 ]; then
        echo "Installed the TaaS client in /usr/local/bin...."
    else
        echo "Install TaaS client failed"
        exit 1
    fi

else
    python $DEVSTACK_PATH/neutron_taas/services/taas/agents/ovs/agent.py --config-file /etc/neutron/neutron.conf
fi
