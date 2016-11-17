========
tap flow
========

A **tap flow** represents the port from which the traffic needs to be mirrored.

Network v2

tap flow create
---------------

Create a tap flow

.. program:: tap flow create
.. code:: bash

    openstack tap flow create
        [--name <name>][--description <description>]
        [--direction {IN, OUT, BOTH}]
        <port>
        <tap-service>

.. _tapflow_create:

.. option:: --name

    Name of the Tap Flow

.. option:: --description

    Description for the Tap Flow

.. option:: --direction

    Direction of the packet flow which needs to be mirrored by the tapflow

.. describe:: <port>

    Source port to which the Tap Flow is connected (name or ID)

.. describe:: <tap-service>

    Tap Service with which the tapflow is associated (name or ID)

tap flow delete
---------------

Delete tap flow(s)

.. program:: tap flow delete
.. code:: bash

    openstack tap flow delete
        <tapflow> [<tapflow> ...]

.. _tapflow_delete-tapflow:
.. describe:: <tapflow>

    Tapflow(s) to delete (name or ID)

tap flow list
-------------

List tap flows

.. program:: tap flow list
.. code:: bash

    openstack tap flow list
        [--name <name>]

.. option:: --name <name>

    List tap flows according to their name

tap flow set
----------

Set tap flow properties

.. program:: tap flow set
.. code:: bash

    openstack flow set
        [--name <name>][--description <description>]
        <tap-flow>

.. option:: --name

    Name of the Tap Flow

.. option:: --description

    Description for the Tap Flow

.. describe:: <tap-flow>

    Tap Flow to modify (name or ID)

tap flow show
-----------

Display tap flow details

.. program:: tap flow show
.. code:: bash

    openstack tapflow show
        <tap_flow>

.. _tapflow_show-tapflow:
.. describe:: <tap_flow>

    Tap Flow to display (name or ID)
