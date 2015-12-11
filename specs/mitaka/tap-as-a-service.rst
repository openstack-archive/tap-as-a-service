..
 This work is licensed under a Creative Commons Attribution 3.0 Unported
 License.

 http://creativecommons.org/licenses/by/3.0/legalcode

============================
Tap-as-a-Service for Neutron
============================

This spec explains an extension for the port mirroring functionality. Port
mirroring involves sending a copy of packets ingressing and/or egressing one
port (where ingress means entering a VM and egress means leaving a VM) to
another port, (usually different from the packet’s original destination).

While the blueprint describes the functionality of mirroring Neutron ports as
an extension to the port object, the spec proposes to offer port mirroring as a
service, which will enable more advanced use-cases (e.g. intrusion detection)
to be deployed.

The proposed port mirroring capability shall be introduced in Neutron as a
service called "Tap-as-a-Service".

Problem description
===================

Neutron currently does not support the functionality of port mirroring for
tenant networks. This feature will greatly benefit tenants who want to debug
their virtual networks and gain visibility into their VMs by monitoring and
analyzing the network traffic associated with them (e.g. IDS).

This spec focuses on mirroring traffic from one Neutron port to another;
future versions may address mirroring from a Neutron port to an arbitrary
interface on a compute host or the network controller.

Different usage scenarios for the service are listed below:

  1. Tapping/mirroring network traffic ingressing and/or egressing a particular
     Neutron port.
  2. Tapping/mirroring all network traffic on a tenant network.


Proposed change
===============

The proposal is to introduce a new Neutron service, called ‘Tap-as-a-Service’,
which provides tapping (port-mirroring) capability for tenant networks. This
service will be modeled similar to other Neutron services such as the firewall,
load-balancer, L3-router etc.

The proposed service will allow the tenants to create a tap service instance
to which they can add Neutron ports that need to be mirrored by creating tap
flows. The tap service itself will be a Neutron port, which will be the
destination port for the mirrored traffic.

The destination Tap-as-a-Service Neutron port will be created on a network
owned by the tenant who is requesting the service. The ports to be
mirrored that are added to the service must be owned by the same tenant who
created the tap service instance. Even on a shared network, a tenant will only
be allowed to mirror the traffic from ports that they own on the shared
network and not traffic from ports that they do not own on the shared network.

The ports owned by the tenant that are mirrored can be on networks other
than the network on which tap service port is created. This allows the tenant
to mirror traffic from any port it owns on a network on to the same
Tap-as-a-Service Neutron port.

In the first version of this service, the tenant can launch a VM specifying
the tap port id (resulting from the creation of tap service instance) for the
VM interface (--nic port-id=tap_port_uuid), thus receiving mirrored traffic for
further processing (dependent on use case) on that VM. In latter versions, the
Neutron port instantiated by the service can be used for purposes other than
just launching a VM on it, for example the port could be used as an
'external-port' [1]_ to get the mirrored data out from the tenant virtual
network on a device or network not managed by openstack.

The following would be the work flow for using this service from a tenant's
point of view

  1. Create a tap service instance. If successful, the UUID of a new Neutron
     port (the destination port for the tap service instance) will be returned
     (this port is created on the specified tenant network).

  2. Launch a monitoring or traffic analysis VM and connect it to the
     destination port for the tap service instance.

  3. Associate Neutron ports with a tap service instance if/when they need to be
     monitored.

  4. Disassociate Neutron ports from a tap service instance if/when then no
     longer need to be monitored.

  5. Destroy a tap-service instance when it is no longer needed. This will
     remove the Neutron port that was serving as the destination port for
     the tap service.

Please note that the normal work flow of launching a VM is not affected while
using TaaS.


Alternatives
------------

As an alternative to introducing port mirroring functionality under Neutron
services, it could be added as an extension to the existing Neutron v2 APIs.


Data model impact
-----------------

Tap-as-a-Service introduces the following data models into Neutron as database
schemas.

1. Tap_Service

+-------------+--------+----------+-----------+---------------+-------------------------+
| Attribute   | Type   | Access   | Default   | Validation/   | Description             |
| Name        |        | (CRUD)   | Value     | Conversion    |                         |
+=============+========+==========+===========+===============+=========================+
| id          | UUID   | CR, all  | generated | N/A           | UUID of the tap         |
|             |        |          |           |               | service inst.           |
+-------------+--------+----------+-----------+---------------+-------------------------+
| project_id  | String | CR, all  | N/A       | N/A           | ID of the               |
|             |        |          |           |               | project creating        |
|             |        |          |           |               | the service             |
+-------------+--------+----------+-----------+---------------+-------------------------+
| name        | String | CRU, all | N/A       | N/A           | Name for the service    |
|             |        |          |           |               | inst.                   |
+-------------+--------+----------+-----------+---------------+-------------------------+
| description | String | CRU, all | N/A       | N/A           | Description of the      |
|             |        |          |           |               | service inst.           |
+-------------+--------+----------+-----------+---------------+-------------------------+
| network_id  | UUID   | CR, all  | N/A       | UUID of a     | A Neutron network       |
|             |        |          |           | valid Neutron | on which the port is    |
|             |        |          |           | network       | to be created           |
|             |        |          |           |               |                         |
+-------------+--------+----------+-----------+---------------+-------------------------+
| port_id     | UUID   | R, all   | N/A       | UUID of a     | A Neutron port          |
|             |        |          |           | valid Neutron | is created by the       |
|             |        |          |           | port          | service for destination |
|             |        |          |           |               | of mirrored traffic     |
+-------------+--------+----------+-----------+---------------+-------------------------+

2. Tap_Flow

+----------------+--------+----------+-----------+---------------+-------------------------+
| Attribute      | Type   | Access   | Default   | Validation/   | Description             |
| Name           |        | (CRUD)   | Value     | Conversion    |                         |
+================+========+==========+===========+===============+=========================+
| id             | UUID   | CR, all  | generated | N/A           | UUID of the             |
|                |        |          |           |               | tap flow instance.      |
+----------------+--------+----------+-----------+---------------+-------------------------+
| name           | String | CRU, all | N/A       | N/A           | Name for the tap flow   |
|                |        |          |           |               | inst.                   |
+----------------+--------+----------+-----------+---------------+-------------------------+
| description    | String | CRU, all | N/A       | N/A           | Description of the      |
|                |        |          |           |               | tap flow inst.          |
+----------------+--------+----------+-----------+---------------+-------------------------+
| tap_service_id | UUID   | CR, all  | N/A       | Valid tap     | UUID of the tap         |
|                |        |          |           | service UUID  | service instance.       |
+----------------+--------+----------+-----------+---------------+-------------------------+
| source_port    | UUID   | CR, all  | N/A       | UUID of a     | UUID of the Neutron     |
|                |        |          |           | valid Neutron | port that needed to be  |
|                |        |          |           | port          | mirrored                |
+----------------+--------+----------+-----------+---------------+-------------------------+
| source_network | UUID   | CR, None | N/A       | UUID of a     | UUID of the Neutron     |
|                |        |          |           | valid Neutron | network that needed to  |
|                |        |          |           | network       | be mirrored             |
|                |        |          |           |               | If this is specified,   |
|                |        |          |           |               | direction and position  |
|                |        |          |           |               | are ignored.            |
+----------------+--------+----------+-----------+---------------+-------------------------+
| position       | ENUM   | CR, all  | PORT      |               | Specify whether packets |
|                | (VNIC, |          |           |               | are captured before or  |
|                | PORT)  |          |           |               | after SG applied        |
|                |        |          |           |               | VNIC: VM side           |
|                |        |          |           |               | PORT: Network side      |
+----------------+--------+----------+-----------+---------------+-------------------------+
| direction      | ENUM   | CR, all  | BOTH      |               | Whether to mirror the   |
|                | (IN,   |          |           |               | traffic leaving or      |
|                | OUT,   |          |           |               | arriving at the         |
|                | BOTH)  |          |           |               | source port             |
|                |        |          |           |               | IN: Network -> VM       |
|                |        |          |           |               | OUT: VM -> Network      |
+----------------+--------+----------+-----------+---------------+-------------------------+

NOTE: source_network and position might or might not be included in the initial
implementation.


REST API impact
---------------

Tap-as-a-Service shall be offered over the RESTFull API interface under
the following namespace:

http://wiki.openstack.org/Neutron/TaaS/API_1.0

The resource attribute map for TaaS is provided below:

.. code-block:: python

  direction_enum = [None, 'IN', 'OUT', 'BOTH']

  RESOURCE_ATTRIBUTE_MAP = {
      Tap_Service: {
          'id': {'allow_post': False, 'allow_put': False,
                 'validate': {'type:uuid': None}, 'is_visible': True,
                 'primary_key': True},
          'project_id': {'allow_post': True, 'allow_put': False,
                         'validate': {'type:string': None},
                         'required_by_policy': True, 'is_visible': True},
          'name': {'allow_post': True, 'allow_put': True,
                   'validate': {'type:string': None},
                   'is_visible': True, 'default': ''},
          'description': {'allow_post': True, 'allow_put': True,
                          'validate': {'type:string': None},
                          'is_visible': True, 'default': ''},
          'port_id': {'allow_post': False, 'allow_put': False,
                               'validate': {'type:uuid': None},
                               'is_visible': True},
          'network_id': {'allow_post': True, 'allow_put': False,
                               'validate': {'type:uuid': None},
                               'is_visible': False}
      },
      Tap_Flow: {
          'id': {'allow_post': False, 'allow_put': False,
                 'validate': {'type:uuid': None}, 'is_visible': True,
                 'primary_key': True},
          'name': {'allow_post': True, 'allow_put': True,
                   'validate': {'type:string': None},
                   'is_visible': True, 'default': ''},
          'description': {'allow_post': True, 'allow_put': True,
                          'validate': {'type:string': None},
                          'is_visible': True, 'default': ''},
          'tap_service_id': {'allow_post': True, 'allow_put': False,
                        'validate': {'type:uuid': None},
                        'required_by_policy': True, 'is_visible': True},
          'source_port': {'allow_post': True, 'allow_put': False,
                        'validate': {'type:uuid': None},
                        'required_by_policy': True, 'is_visible': True},
          'source_network': {'allow_post': True, 'allow_put': False,
                             'validate': {'type:uuid': None},
                             'required_by_policy': True, 'is_visible': True},
          'position': {'allow_post': True, 'allow_put': False,
                       'validate': {'type:string': position_enum},
                       'is_visible': True}
          'direction': {'allow_post': True, 'allow_put': False,
                               'validate': {'type:string': direction_enum},
                               'is_visible': True}
      }
  }

Security impact
---------------

A TaaS instance comprises a collection of source Neutron ports (whose
ingress and/or egress traffic are being mirrored) and a destination Neutron
port (where the mirrored traffic is received). Security Groups will be
handled differently for these two classes of ports, as described below:

Destination Side:

Ingress Security Group filters, including the filter that prevents MAC-address
spoofing, will be disabled for the destination Neutron port. This will ensure
that all of the mirrored packets received at this port are able to reach the
monitoring VM attached to it.

Source Side:

Ideally it would be nice to mirror all packets entering and/or leaving the
virtual NICs associated with the VMs that are being monitored. This means
capturing ingress traffic after it passes the inbound Security Group filters
and capturing egress traffic before it passes the outbound Security Group
filters.

However, due to the manner in which Security Groups are currently implemented
in OpenStack (i.e. north of the Open vSwitch ports, using Linux IP Tables) this
is not possible because port mirroring support resides inside Open vSwitch.
Therefore, in the first version of TaaS, Security Groups will be ignored for
the source Neutron ports; this effectively translates into capturing ingress
traffic before it passes the inbound Security Group filters and capturing
egress traffic after it passes the outbound Security Group filters. In other
words, port mirroring will be implemented for all packets entering and/or
leaving the Open vSwitch ports associated with the respective virtual NICs of
the VMs that are being monitored.

There is a separate effort that has been initiated to implement Security Groups
within OpenvSwitch. A later version of TaaS may make use of this feature, if
and when it is available, so that we can realize the ideal behavior described
above. It should be noted that such an enhancement should not require a change
to the TaaS data model.

Keeping data privacy aspects in mind and preventing the data center admin
from snooping on tenant's network traffic without their knowledge, the admin
shall not be allowed to mirror traffic from any ports that belong to tenants.
Hence creation of 'Tap_Flow' is only permitted on ports that are owned by the
creating tenant.

If an admin wants to monitor tenant's traffic, the admin will have to join that
tenant as a member. This will ensure that the tenant is aware that the admin
might be monitoring their traffic.

Notifications impact
--------------------

A set of new RCP calls for communication between the TaaS server and agents
are required and will be put in place as part of the reference implementation.

IPv6 impact
--------------------
None

Other end user impact
---------------------

Users will be able to invoke and access the TaaS APIs through
python-neutronclient.

Performance Impact
------------------

The performance impact of mirroring traffic needs to be examined and
quantified. The impact of a tenant potentially mirroring all traffic from
all ports could be large and needs more examination.

Some alternatives to reduce the amount of mirrored traffic are listed below.

  1. Rate limiting on the ports being mirrored.
  2. Filters to select certain flows ingressing/egressing a port to be
     mirrored.
  3. Having a quota on the number of TaaS Flows that can be defined by the
     tenant.

Other deployer impact
---------------------

Configurations for the service plugin will be added later.


Developer impact
----------------
This will be a new extension API, and will not affect the existing API.

Community impact
----------------
None

Follow up work
--------------

Going forward, TaaS would be incorporated with Service Insertion [2]_ similar
to other existing services like FWaaS, LBaaS, and VPNaaS.

While integrating Tap-as-a-Service with Service Insertion the key changes to
the data model needed would be the removal of 'network_id' and 'port_id' from
the 'Tap_Service' data model.

Some policy based filtering rules would help alleviate the potential performance
issues.

Implementation
==============

The reference implementation for TaaS will be based on Open vSwitch. In
addition to the existing integration (br-int) and tunnel (br-tun) bridges, a
separate tap bridge (br-tap) will be used. The tap bridge provides nice
isolation for supporting more complex TaaS features (e.g. filtering mirrored
packets) in the future.

The tapping operation will be realized by adding higher priority flows in
br-int, which duplicate the ingress and/or egress packets associated with
specific ports (belonging to the VMs being monitored) and send the copies to
br-tap. Packets sent to br-tap will also be tagged with an appropriate VLAN id
corresponding to the associated TaaS instance (in the initial release these
VLAN ids may be reserved from highest to lowest; in later releases it should be
coordinated with the Neutron service). The original packets will continue to be
processed normally, so as not to affect the traffic patterns of the VMs being
monitored.

Flows will be placed in br-tap to determine if the mirrored traffic should be
sent to br-tun or not. If the destination port of a Tap-aaS instance happens to
reside on the same host as a source port, packets from that source port will be
returned to br-int; otherwise they will be forwarded to br-tun for delivery to
a remote node.

Packets arriving at br-tun from br-tap will get routed to the destination ports
of appropriate TaaS instances using the same GRE or VXLAN tunnel network that
is used to pass regular traffic between hosts. Separate tunnel IDs will be used
to isolate different TaaS instances from one another and from the normal
(non-mirrored) traffic passing through the bridge. This will ensure that proper
action can be taken on the receiving end of a tunnel so that mirrored traffic
is sent to br-tap instead of br-int. Special flows will be used in br-tun to
automatically learn about the location of the destination ports of TaaS
instances.

Packets entering br-tap from br-tun will be forwarded to br-int only if the
destination port of the corresponding TaaS instance resides on the same host.
Finally, packets entering br-int from br-tap will be delivered to the
appropriate destination port after the TaaS instance VLAN id is replaced with
the VLAN id for the port.

Assignee(s)
-----------

* Vinay Yadhav

Work Items
----------

* TaaS API and data model implementation.
* TaaS OVS driver.
* OVS agent changes for port mirroring.

Dependencies
============

None

Testing
=======

* Unit Tests to be added.
* Functional tests in tempest to be added.
* API Tests in Tempest to be added.

Documentation Impact
====================

* User Documentation needs to be updated
* Developer Documentation needs to be updated

References
==========

.. [1] External port
   https://review.openstack.org/#/c/87825

.. [2] Service base and insertion
   https://review.openstack.org/#/c/93128

.. [3] NFV unaddressed interfaces
   https://review.openstack.org/#/c/97715/
