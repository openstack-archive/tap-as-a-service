======
tapservice
======

A **tapservice** represents the port on which the mirrored traffic is delivered.
Any service (VM) that uses the mirrored data is attached to the port.

Network v2

tapservice create
---------------

Create a tap service

.. program:: tapservice create
.. code:: bash

    os tapservice create
        [--name <name>][--description <description>]
        <port>

.. _tapservice_create:

.. option:: --name

    Name of the Tap Service

.. option:: --description

    Description for the Tap Service

.. describe:: <port>

    Port to which the Tap service is connected(name or ID)

tapservice delete
-------------

Delete tapservice(s)

.. program:: tapservice delete
.. code:: bash

    os tapservice delete
        <tapservice> [<tapservice> ...]

.. _tapservice_delete-tapservice:
.. describe:: <tapservice>

    Tapservice(s) to delete (name or ID)

tapservice list
-----------

List tapservices

.. program:: tapservice list
.. code:: bash

    os tapservice list
        [--name <name>]

.. option:: --name <name>

    List tapservices according to their name

tapservice set
----------

Set tapservice properties

.. program:: tapservice set
.. code:: bash

    os router set
        [--name <name>][--description <description>]
        <tap-service>

.. option:: --name

    Name of the Tap Service

.. option:: --description

    Description for the Tap Service

.. describe:: <tap-service>

    Tap Service to modify (name or ID)

tapservice show
-----------

Display tapservice details

.. program:: router show
.. code:: bash

    os tapservice show
        <tap_service>

.. _router_show-router:
.. describe:: <tap_service>

    Tap Service to display (name or ID)

