==============================
Tap as a Service API REFERENCE
==============================

This documents is an API REFERENCE for Tap-as-a-Service Neutron extension.

The documents is organized into three section, TaaS Resources, API Reference
and WorkFlow.

TaaS Resources
==============

TaaS consists of two resources, TapService and TapFlow.

TapService
----------

TapService Represents the port on which the mirrored traffic is delivered.
Any service (VM) that uses the mirrored data is attached to the port.

.. code-block:: python

    'tap_services': {
        'id': {'allow_post': False, 'allow_put': False,
               'validate': {'type:uuid': None}, 'is_visible': True,
               'primary_key': True},
        'tenant_id': {'allow_post': True, 'allow_put': False,
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
        'network_id': {'allow_post': True, 'allow_put': False,
                       'validate': {'type:uuid': None},
                       'is_visible': False}
    }

TapFlow
-------

TapFlow Represents the port from which the traffic needs to be mirrored.

.. code-block:: python

    'tap_flows': {
        'id': {'allow_post': False, 'allow_put': False,
               'validate': {'type:uuid': None}, 'is_visible': True,
               'primary_key': True},
        'tenant_id': {'allow_post': True, 'allow_put': False,
                      'validate': {'type:string': None},
                      'required_by_policy': True, 'is_visible': True},
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
                      'is_visible': True}
    }

    direction_enum = [None, 'IN', 'OUT', 'BOTH']


Multiple TapFlow instances can be associated with a single TapService
instance.

API REFERENCE
=============

Below is the list of REST APIs that can be used to interact with TaaS Neutron
extension

1. Create TapService

\

   **POST        /v2.0/taas/tap-services**

\

    Json Request:

.. code-block:: python

    {
        "tap_service": {
            "description": "Test_Tap",
            "name": "Test",
            "network_id": "8686f7d1-14e3-46ab-be3c-ccc0eead93cd",
            "port_id": "c9beb5a1-21f5-4225-9eaf-02ddccdd50a9",
            "tenant_id": "97e1586d580745d7b311406697aaf097"
        }
    }

\

    Json Response:

.. code-block:: python

    {
        "tap_service": {
            "description": "Test_Tap",
            "id": "c352f537-ad49-48eb-ab05-1c6b8cb900ff",
            "name": "Test",
            "port_id": "c9beb5a1-21f5-4225-9eaf-02ddccdd50a9",
            "tenant_id": "97e1586d580745d7b311406697aaf097"
        }
    }

2. List TapServices

\

    **GET        /v2.0/taas/tap-services/{tap_service_uuid}**

\

    Json Response:

.. code-block:: python

    {
        "tap_services": [
            {
                "description": "Test_Tap",
                "id": "c352f537-ad49-48eb-ab05-1c6b8cb900ff",
                "name": "Test",
                "port_id": "c9beb5a1-21f5-4225-9eaf-02ddccdd50a9",
                "tenant_id": "97e1586d580745d7b311406697aaf097"
            }
        ]
    }

3. Delete TapService

\

    **DELETE        /v2.0/taas/tap-services/{tap_service_uuid}**

\

4. Create TapFlow

\

   **POST        /v2.0/taas/tap-flows**

\

    Json Request:

.. code-block:: python

    {
        "tap_flow": {
            "description": "Test_flow1",
            "direction": "BOTH",
            "name": "flow1",
            "source_port": "775a58bb-e2c6-4529-a918-2f019169b5b1",
            "tap_service_id": "69bd12b2-0e13-45ec-9045-b674fd9f0468",
            "tenant_id": "97e1586d580745d7b311406697aaf097"
        }
    }

\

    Json Response:

.. code-block:: python

    {
        "tap_flow": {
            "description": "Test_flow1",
            "direction": "BOTH",
            "id": "cc47f881-345f-4e62-ad24-bea79eb28304",
            "name": "flow1",
            "source_port": "775a58bb-e2c6-4529-a918-2f019169b5b1",
            "tap_service_id": "69bd12b2-0e13-45ec-9045-b674fd9f0468",
            "tenant_id": "97e1586d580745d7b311406697aaf097"
        }
    }

5. List TapFlows

\

    **GET        /v2.0/taas/tap-flows/{tap_flow_uuid}**

\

    Json Response:

.. code-block:: python

    {
        "tap_flows": [
            {
                "description": "Test_flow1",
                "direction": "BOTH",
                "id": "cc47f881-345f-4e62-ad24-bea79eb28304",
                "name": "flow1",
                "source_port": "775a58bb-e2c6-4529-a918-2f019169b5b1",
                "tap_service_id": "c352f537-ad49-48eb-ab05-1c6b8cb900ff",
                "tenant_id": "97e1586d580745d7b311406697aaf097"
            }
        ]
    }

6. Delete TapFlow

\

    **DELETE        /v2.0/taas/tap-flows/{tap_flow_uuid}**

\


The TaaS client can be used to send REST request and interact with the TaaS
extension. For usage type **taas --help** in the terminal after TaaS has been
installed.

Work Flow
=========

In this section we describe a simple sequence of steps to use TaaS.

Work Flow Sequence
------------------

1. Create a Neutron port with 'port_security_enabled' set to 'false'.

2. Launch a VM (VM on which you want to monitor/receive the mirrored data).
   Assoiciate the Neutron port created in step 1 while creating the VM.

3. Using TaaS client command **taas tap-service-create** or REST APIs
   create a Tap Service instance by associating the port created in step 1.

4. Using TaaS client command **taas tap-flow-create** or REST APIs
   Create a Tap Flow instance by associating the Tap Service instance created
   in step 3 and Neutron port from which you want to mirror traffic (assuming
   the Neutron port from which the traffic needs to be monitored already
   exists)

5. Observe the mirrored traffic on the monitoring VM by running tools such as
   tcpdump.


You can watch our tech talk session which included a live demo for more
information about using TaaS, https://www.youtube.com/watch?v=_cAkRUB3TCE

