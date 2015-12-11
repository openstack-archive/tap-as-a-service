..
 This work is licensed under a Creative Commons Attribution 3.0 Unported
 License.

 http://creativecommons.org/licenses/by/3.0/legalcode

============================
Tap-as-a-Service for Neutron
============================


Launchpad blueprint:

  https://blueprints.launchpad.net/neutron/+spec/tap-as-a-service

This spec explains an extension for the port mirroring functionality. Port
mirroring involves sending a copy of packets ingressing and/or egressing one
port (where ingress means entering a VM and egress means leaving a VM) to
another port, (usually different from the packet's original destination).
A port could be attached to a VM or a networking resource like router.

While the blueprint describes the functionality of mirroring Neutron ports as
an extension to the port object, the spec proposes to offer port mirroring as a
service, which will enable more advanced use-cases (e.g. intrusion detection)
to be deployed.

The proposed port mirroring capability shall be introduced in Neutron as a
service called "Tap-as-a-Service".

Problem description
===================

Neutron currently does not support the functionality of port mirroring for
tenant networks. This feature will greatly benefit tenants and admins, who
want to debug their virtual networks and gain visibility into their VMs by
monitoring and analyzing the network traffic associated with them (e.g. IDS).

This spec focuses on mirroring traffic from one Neutron port to another;
future versions may address mirroring from a Neutron port to an arbitrary
interface (not managed by Neutron) on a compute host or the network controller.

Different usage scenarios for the service are listed below:

  1. Tapping/mirroring network traffic ingressing and/or egressing a particular
     Neutron port.
  2. Tapping/mirroring all network traffic on a tenant network.
  3. Tenant or admin will be able to do tap/traffic mirroring based on a
     policy rule and set destination as a Neutron port, which can be linked
     to a virtual machine as normal Nova operations or to a physical machine
     via l2-gateway functionality.
  4. Admin will be able to do packet level network debugging for the virtual
     network.
  5. Provide a way for real time analytics based on different criteria, like
     tenants, ports, traffic types (policy) etc.

Note that some of the above use-cases are not covered by this proposal, at
least for the first step.


Proposed change
===============

The proposal is to introduce a new Neutron service plugin, called
"Tap-as-a-Service",
which provides tapping (port-mirroring) capability for Neutron networks;
tenant or provider networks. This service will be modeled similar to other
Neutron services such as the firewall, load-balancer, L3-router etc.

The proposed service will allow the tenants to create a tap service instance
to which they can add Neutron ports that need to be mirrored by creating tap
flows. The tap service itself will be a Neutron port, which will be the
destination port for the mirrored traffic.

The destination Tap-as-a-Service Neutron port should be created beforehand on
a network owned by the tenant who is requesting the service. The ports to be
mirrored that are added to the service must be owned by the same tenant who
created the tap service instance. Even on a shared network, a tenant will only
be allowed to mirror the traffic from ports that they own on the shared
network and not traffic from ports that they do not own on the shared network.

The ports owned by the tenant that are mirrored can be on networks other
than the network on which tap service port is created. This allows the tenant
to mirror traffic from any port it owns on a network on to the same
Tap-as-a-Service Neutron port.

The tenant can launch a VM specifying the tap destination port for the VM
interface (--nic port-id=tap_port_uuid), thus receiving mirrored traffic for
further processing (dependent on use case) on that VM.

The following would be the work flow for using this service from a tenant's
point of view

  0. Create a Neutron port which will be used as the destination port.
     This can be a part of ordinary VM launch.

  1. Create a tap service instance, specifying the Neutron port.

  2. If you haven't yet, launch a monitoring or traffic analysis VM and
     connect it to the destination port for the tap service instance.

  3. Associate Neutron ports with a tap service instance if/when they need to be
     monitored.

  4. Disassociate Neutron ports from a tap service instance if/when they no
     longer need to be monitored.

  5. Destroy a tap-service instance when it is no longer needed.

  6. Delete the destination port when it is no longer neeeded.

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

1. tap_service

+-------------+--------+----------+-----------+---------------+-------------------------+
| Attribute   | Type   | Access   | Default   | Validation/   | Description             |
| Name        |        | (CRUD)   | Value     | Conversion    |                         |
+=============+========+==========+===========+===============+=========================+
| id          | UUID   | R, all   | generated | N/A           | UUID of the tap         |
|             |        |          |           |               | service instance.       |
+-------------+--------+----------+-----------+---------------+-------------------------+
| project_id  | String | CR, all  | Requester | N/A           | ID of the               |
|             |        |          |           |               | project creating        |
|             |        |          |           |               | the service             |
+-------------+--------+----------+-----------+---------------+-------------------------+
| name        | String | CRU, all | Empty     | N/A           | Name for the service    |
|             |        |          |           |               | instance.               |
+-------------+--------+----------+-----------+---------------+-------------------------+
| description | String | CRU, all | Empty     | N/A           | Description of the      |
|             |        |          |           |               | service instance.       |
+-------------+--------+----------+-----------+---------------+-------------------------+
| port_id     | UUID   | CR, all  | N/A       | UUID of a     | An existing Neutron port|
|             |        |          |           | valid Neutron | to which traffic will   |
|             |        |          |           | port          | be mirrored             |
+-------------+--------+----------+-----------+---------------+-------------------------+
| status      | String | R, all   | N/A       | N/A           | The operation status of |
|             |        |          |           |               | the resource            |
|             |        |          |           |               | (ACTIVE, PENDING_foo,   |
|             |        |          |           |               |  ERROR, ...)            |
+-------------+--------+----------+-----------+---------------+-------------------------+

2. tap_flow

+----------------+--------+----------+-----------+---------------+-------------------------+
| Attribute      | Type   | Access   | Default   | Validation/   | Description             |
| Name           |        | (CRUD)   | Value     | Conversion    |                         |
+================+========+==========+===========+===============+=========================+
| id             | UUID   | R, all   | generated | N/A           | UUID of the             |
|                |        |          |           |               | tap flow instance.      |
+----------------+--------+----------+-----------+---------------+-------------------------+
| name           | String | CRU, all | Empty     | N/A           | Name for the tap flow   |
|                |        |          |           |               | instance.               |
+----------------+--------+----------+-----------+---------------+-------------------------+
| description    | String | CRU, all | Empty     | N/A           | Description of the      |
|                |        |          |           |               | tap flow instance.      |
+----------------+--------+----------+-----------+---------------+-------------------------+
| tap_service_id | UUID   | CR, all  | N/A       | Valid tap     | UUID of the tap         |
|                |        |          |           | service UUID  | service instance.       |
+----------------+--------+----------+-----------+---------------+-------------------------+
| source_port    | UUID   | CR, all  | N/A       | UUID of a     | UUID of the Neutron     |
|                |        |          |           | valid Neutron | port that needed to be  |
|                |        |          |           | port          | mirrored                |
+----------------+--------+----------+-----------+---------------+-------------------------+
| direction      | ENUM   | CR, all  | BOTH      |               | Whether to mirror the   |
|                | (IN,   |          |           |               | traffic leaving or      |
|                | OUT,   |          |           |               | arriving at the         |
|                | BOTH)  |          |           |               | source port             |
|                |        |          |           |               | IN: Network -> VM       |
|                |        |          |           |               | OUT: VM -> Network      |
+----------------+--------+----------+-----------+---------------+-------------------------+
| status         | String | R, all   | N/A       | N/A           | The operation status of |
|                |        |          |           |               | the resource            |
|                |        |          |           |               | (ACTIVE, PENDING_foo,   |
|                |        |          |           |               |  ERROR, ...)            |
+----------------+--------+----------+-----------+---------------+-------------------------+


REST API impact
---------------

Tap-as-a-Service shall be offered over the RESTFull API interface under
the following namespace:

http://wiki.openstack.org/Neutron/TaaS/API_1.0

The resource attribute map for TaaS is provided below:

.. code-block:: python

  direction_enum = ['IN', 'OUT', 'BOTH']

  RESOURCE_ATTRIBUTE_MAP = {
      'tap_service': {
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
          'port_id': {'allow_post': True, 'allow_put': False,
                               'validate': {'type:uuid': None},
                               'is_visible': True},
          'status': {'allow_post': False, 'allow_put': False,
                     'is_visible': True},
      },
      'tap_flow': {
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
          'direction': {'allow_post': True, 'allow_put': False,
                               'validate': {'type:string': direction_enum},
                               'is_visible': True},
          'status': {'allow_post': False, 'allow_put': False,
                     'is_visible': True},
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

A set of new RPC calls for communication between the TaaS server and agents
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

A new bridge (br-tap) mentioned in Implementation section.


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

We might want to ensure exclusive use of the destination port.

We might want to create the destination port automatically on tap-service
creation, rather than specifying an existing port.  In that case, network_id
should be taken as a parameter for tap-service creation, instead of port_id.

We might want to allow the destination port be used for purposes other than
just launching a VM on it, for example the port could be used as an
'external-port' [1]_ to get the mirrored data out from the tenant virtual
network on a device or network not managed by openstack.

We might want to introduce a way to tap a whole traffic for the specified
network.

We need a mechanism to coordinate usage of various resources with other
agent extensions.  E.g. OVS flows, tunnel IDs, VLAN IDs.


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
