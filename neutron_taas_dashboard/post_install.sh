#!/bin/bash -x

# This script will be executed inside npm postinstall task, see package.json

# pull down the test shim from horizon master because it's not
# included in the installed horizon packages
if [ ! -f test-shim.js ];
then
  wget -nv -t 3 https://raw.githubusercontent.com/openstack/horizon/master/test-shim.js
fi

echo "Creating a tox env which will contain xStatic libraries, horizon, and openstack_dashboard"
tox -epy27 --notest;
