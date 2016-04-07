================
Tap as a Service
================
Tap-as-a-Service (TaaS) is an extension to the OpenStack network service (Neutron).
It provides remote port mirroring capability for tenant virtual networks.

Port mirroring involves sending a copy of packets entering and/or leaving one
port to another port, which is usually different from the original destinations
of the packets being mirrored.


This service has been primarily designed to help tenants (or the cloud administrator)
debug complex virtual networks and gain visibility into their VMs, by monitoring the
network traffic associated with them. TaaS honors tenant boundaries and its mirror
sessions are capable of spanning across multiple compute and network nodes. It serves
as an essential infrastructure component that can be utilized for supplying data to a
variety of network analytics and security applications (e.g. IDS).

* Free software: Apache license
* API Reference: https://github.com/openstack/tap-as-a-service/blob/master/API_REFERENCE.rst
* Source: https://git.openstack.org/cgit/openstack/tap-as-a-service
* Bugs: https://bugs.launchpad.net/tap-as-a-service

For installing Tap-as-a-Service with Devstack please read the INSTALL.rst file
