# Copyright 2015 NEC Corporation
# All Rights Reserved
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
#
from mox3 import mox
import sys

from neutronclient.neutron import v2_0
from neutronclient import shell as neutronshell
from neutronclient.tests.unit import test_cli20

TOKEN = test_cli20.TOKEN
end_url = test_cli20.end_url
class MyResp(test_cli20.MyResp):

    pass


class MyApp(test_cli20.MyApp):

    pass


class MyComparator(test_cli20.MyComparator):

    pass

class CLITestV20Base(test_cli20.CLITestV20Base):

    def setUp(self, plurals=None):
        super(CLITestV20Base, self).setUp()

    # Need to override the test_create_resource function because of the variation in path(/taas/%s)
    def _test_create_resource(self, resource, cmd, name, myid, args,
                              position_names, position_values,
                              tenant_id=None, tags=None, admin_state_up=True,
                              extra_body=None, cmd_resource=None,
                              parent_id=None, **kwargs):
        self.mox.StubOutWithMock(cmd, "get_client")
        self.mox.StubOutWithMock(self.client.httpclient, "request")
        cmd.get_client().MultipleTimes().AndReturn(self.client)
        if not cmd_resource:
            cmd_resource = resource
        body = {resource: {}, }
        body[resource].update(kwargs)

        for i in range(len(position_names)):
            body[resource].update({position_names[i]: position_values[i]})
        ress = {resource:
                {self.id_field: myid}, }
        if name:
            ress[resource].update({'name': name})
        self.client.format = self.format
        resstr = self.client.serialize(ress)
        # url method body
        resource_plural = v2_0._get_resource_plural(cmd_resource,
                                                             self.client)
        #resource_plural = "taas/" + resource_plural  
        path = getattr(self.client, resource_plural + "_path")
        if self.format == 'json':
            mox_body = MyComparator(body, self.client)
        else:
            mox_body = self.client.serialize(body)
        self.client.httpclient.request(
            end_url(path, format=self.format), 'POST',
            body=mox_body,
            headers=mox.ContainsKeyValue(
                'X-Auth-Token', TOKEN)).AndReturn((MyResp(200), resstr))
#        self.assertEqual(path,"",str(path))
        args.extend(['--request-format', self.format])
        self.mox.ReplayAll()
        cmd_parser = cmd.get_parser('create_' + resource)
        neutronshell.run_command(cmd, cmd_parser, args)
        self.mox.VerifyAll()
        self.mox.UnsetStubs()
        _str = self.fake_stdout.make_string()
        self.assertIn(myid, _str)
        if name:
            self.assertIn(name, _str)
