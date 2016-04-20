# Copyright (C) 2016 Midokura SARL.
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import abc

from oslo_log import log as logging
import six

LOG = logging.getLogger(__name__)


@six.add_metaclass(abc.ABCMeta)
class TaasDriver(object):

    def __init__(self, service_plugin, validator=None):
        self.service_plugin = service_plugin

    @property
    def service_type(self):
        pass

    @abc.abstractmethod
    def create_tap_service(self, context, tap_service):
        pass

    @abc.abstractmethod
    def delete_tap_service(self, context, tap_service):
        pass

    @abc.abstractmethod
    def create_tap_flow(self, context, tap_flow):
        pass

    @abc.abstractmethod
    def delete_tap_flow(self, context, tap_flow):
        pass
