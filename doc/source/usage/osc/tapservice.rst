======
tapservice
======

A **tap service** represents the port on which the mirrored traffic is delivered.
Any service (VM) that uses the mirrored data is attached to the port.

Network v2

tap service create
------------------

Create a tap service

.. program:: tap service create
.. code:: bash

    openstack tap service create
        [--name <name>][--description <description>]
        <port>

.. _tapservice_create:

.. option:: --name

    Name of the Tap Service

.. option:: --description

    Description for the Tap Service

.. describe:: <port>

    Port to which the Tap service is connected(name or ID)

tap service delete
------------------

Delete tap service(s)

.. program:: tap service delete
.. code:: bash

    openstack tapservice delete
        <tapservice> [<tapservice> ...]

.. _tapservice_delete-tapservice:
.. describe:: <tapservice>

    Tap service(s) to delete (name or ID)

tap service list
----------------

List tap services

.. program:: tap service list
.. code:: bash

    openstack tap service list
        [--name <name>]

.. option:: --name <name>

    List tap services

tap service set
---------------

Set tap service properties

.. program:: tap service set
.. code:: bash

    openstack tap service set
        [--name <name>][--description <description>]
        <tap-service>

.. option:: --name

    Name of the Tap Service

.. option:: --description

    Description for the Tap Service

.. describe:: <tap-service>

    Tap Service to modify (name or ID)

tap service show
----------------

Display tap service details

.. program:: taps ervice show
.. code:: bash

    openstack tap service show
        <tap_service>

.. _router_show-router:
.. describe:: <tap_service>

    Tap Service to display (name or ID)

