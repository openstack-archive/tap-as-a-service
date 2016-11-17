# Copyright (c) 2016 NEC Technologies India Pvt.Limited.
# All Rights Reserved.
#
#   Licensed under the Apache License, Version 2.0 (the "License"); you may
#   not use this file except in compliance with the License. You may obtain
#   a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#   WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#   License for the specific language governing permissions and limitations
#   under the License.

import argparse
import copy
import mock
import uuid

from oslo_utils import uuidutils
from osc_lib.tests import utils


class TestNeutronClientOSCV2(utils.TestCommand):

    def setUp(self):
        super(TestNeutronClientOSCV2, self).setUp()
        self.namespace = argparse.Namespace()
        self.app.client_manager.session = mock.Mock()
        self.app.client_manager.neutronclient = mock.Mock()
        self.neutronclient = self.app.client_manager.neutronclient


class FakeTapFlow(object):
    """Fake tap flow attributes."""

    @staticmethod
    def create_tap_flow(attrs=None):
        """Create a fake tap flow.

        :param Dictionary attrs:
            A dictionary with all attributes
        :return:
            A Dictionary with id, name, description, source_port,
            tap_service_id, status and tenant_id
        """
        attrs = attrs or {}

        # Set default attributes.
        tap_flow_attrs = {
            'id': uuidutils.generate_uuid(),
            'name': 'tap-flow-name',
            'description': 'description',
            'tap_service_id': uuidutils.generate_uuid(),
            'source_port': uuidutils.generate_uuid(),
            'status': "status",
            'tenant_id': uuidutils.generate_uuid(),
        }

        # Overwrite default attributes.
        tap_flow_attrs.update(attrs)
        return copy.deepcopy(tap_flow_attrs)

    @staticmethod
    def create_tap_flows(attrs=None, count=1):
        """Create multiple tap_flows.

        :param Dictionary attrs:
            A dictionary with all attributes
        :param int count:
            The number of tap_flows to fake
        :return:
            A list of dictionaries faking the tap_flows
        """
        tap_flows = []
        for i in range(0, count):
            tap_flow = tap_flows.append(FakeTapFlow.create_tap_flow(attrs))
        tap_flows.append(tap_flow)

        return {'tap_flows': tap_flows}


class FakeTapService(object):
    """Fake tap service attributes."""

    @staticmethod
    def create_tap_service(attrs=None):
        """Create a fake tap service.

        :param Dictionary attrs:
            A dictionary with all attributes
        :return:
            A Dictionary with id, name, description,
            port_id, status and tenant_id
        """
        attrs = attrs or {}

        # Set default attributes.
        tap_service_attrs = {
            'id': uuidutils.generate_uuid(),
            'name': 'tap-service-name',
            'description': 'description',
            'port_id': uuidutils.generate_uuid(),
            'status': "status",
            'tenant_id': uuidutils.generate_uuid(),
        }

        # Overwrite default attributes.
        tap_service_attrs.update(attrs)
        return copy.deepcopy(tap_service_attrs)

    @staticmethod
    def create_tap_services(attrs=None, count=1):
        """Create multiple tap_services.

        :param Dictionary attrs:
            A dictionary with all attributes
        :param int count:
            The number of tap_services to fake
        :return:
            A list of dictionaries faking the tap_services
        """
        tap_services = []
        for i in range(0, count):
            tap_service = tap_services.append(
                FakeTapFlow.create_tap_service(attrs))
        tap_services.append(tap_service)

        return {'tap_services': tap_services}

