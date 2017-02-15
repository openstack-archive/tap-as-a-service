#! /bin/sh

# Like Neutron, Tap-as-a-service is also introducing a policy check to ensure
# that the unit tests written for policy match with the expected policy installed
# in production

TMPDIR=`mktemp -d /tmp/${0##*/}.XXXXXX` || exit 1
export TMPDIR
trap "rm -rf $TMPDIR" EXIT

FAILURES=$TMPDIR/failures
check_identical_policy_files () {
    # For unit tests, we maintain their own policy.json file to make test suite
    # independent of whether it's executed from the neutron source tree or from
    # site-packages installation path. We don't want two copies of the same
    # file to diverge, so checking that they are identical
    diff etc/policy.json neutron_taas/tests/etc/policy.json 2>&1 > /dev/null
    if [ "$?" -ne 0 ]; then
        echo "policy.json files must be identical!" >>$FAILURES
    fi
}


#Checks are added here
check_identical_policy_files

# Fail, if there are emitted failures
if [ -f $FAILURES ]; then
    cat $FAILURES
    exit 1
fi
