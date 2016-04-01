=================================
TaaS dashboard installation guide
=================================

This is an installation guide for TaaS dashboard.

Installation
============

1. Clone horizon tree::

   $ cd /opt/stack
   $ git clone git://git.openstack.org/openstack/horizon.git

2. Checkout commit:37d85d122e536178327add1a75571e53cf65d233[1]::

   $ git checkout 37d85d122e536178327add1a75571e53cf65d233

   [1] This commit has the network topology view based on kilo and works fine with other newest modules.

3. Apply TaaS dashbaord patch to horizon tree::

   $ cd /opt/stack/thorizon
   $ patch -p1 < taas_dashboard.patch

4. Apply https://review.openstack.org/#/c/275011/ patch to taas tree::

   $ cd /opt/stack/tap-as-a-service
   $ patch -p1 < 5b95b3b8.diff

5. Run devstack::

   $ cd ~/devstack
   $ ./stack.sh
