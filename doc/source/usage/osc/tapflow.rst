======
tapflow
======

A **tapflow** represents the port from which the traffic needs to be mirrored.

Network v2

tapflow create
---------------

Create a tap flow

.. program:: tapflow create
.. code:: bash

    os tapflow create
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

tapflow delete
-------------

Delete tapflow(s)

.. program:: tapflow delete
.. code:: bash

    os tapflow delete
        <tapflow> [<tapflow> ...]

.. _tapflow_delete-tapflow:
.. describe:: <tapflow>

    Tapflow(s) to delete (name or ID)

tapflow list
-----------

List tapflows

.. program:: tapflow list
.. code:: bash

    os tapflow list
        [--name <name>]

.. option:: --name <name>

    List tapflows according to their name

tapflow set
----------

Set tapflow properties

.. program:: tapflow set
.. code:: bash

    os router set
        [--name <name>][--description <description>]
        <tap-flow>

.. option:: --name

    Name of the Tap Flow

.. option:: --description

    Description for the Tap Flow

.. describe:: <tap-flow>

    Tap Flow to modify (name or ID)

tapflow show
-----------

Display tapflow details

.. program:: router show
.. code:: bash

    os tapflow show
        <tap_flow>

.. _router_show-router:
.. describe:: <tap_flow>

    Tap Flow to display (name or ID)

