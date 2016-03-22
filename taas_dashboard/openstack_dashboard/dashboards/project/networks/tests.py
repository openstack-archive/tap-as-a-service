# Copyright 2012 NEC Corporation
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

from django.core.urlresolvers import reverse
from django import http
from django.utils.html import escape

from horizon.workflows import views

from mox import IsA  # noqa

from openstack_dashboard import api
from openstack_dashboard.dashboards.project.networks.subnets import tables\
    as subnets_tables
from openstack_dashboard.dashboards.project.networks import tables\
    as networks_tables
from openstack_dashboard.dashboards.project.networks import workflows
from openstack_dashboard.test import helpers as test
from openstack_dashboard.usage import quotas


INDEX_URL = reverse('horizon:project:networks:index')


def form_data_subnet(subnet,
                     name=None, cidr=None, ip_version=None,
                     gateway_ip='', enable_dhcp=None,
                     allocation_pools=None,
                     dns_nameservers=None,
                     host_routes=None):
    def get_value(value, default):
        return default if value is None else value

    data = {}
    data['subnet_name'] = get_value(name, subnet.name)
    data['cidr'] = get_value(cidr, subnet.cidr)
    data['ip_version'] = get_value(ip_version, subnet.ip_version)

    gateway_ip = subnet.gateway_ip if gateway_ip == '' else gateway_ip
    data['gateway_ip'] = gateway_ip or ''
    data['no_gateway'] = (gateway_ip is None)

    data['enable_dhcp'] = get_value(enable_dhcp, subnet.enable_dhcp)
    if data['ip_version'] == 6:
        data['ipv6_modes'] = subnet.ipv6_modes

    pools = get_value(allocation_pools, subnet.allocation_pools)
    data['allocation_pools'] = _str_allocation_pools(pools)
    nameservers = get_value(dns_nameservers, subnet.dns_nameservers)
    data['dns_nameservers'] = _str_dns_nameservers(nameservers)
    routes = get_value(host_routes, subnet.host_routes)
    data['host_routes'] = _str_host_routes(routes)

    return data


def form_data_no_subnet():
    return {'subnet_name': '',
            'cidr': '',
            'ip_version': 4,
            'gateway_ip': '',
            'no_gateway': False,
            'enable_dhcp': True,
            'allocation_pools': '',
            'dns_nameservers': '',
            'host_routes': ''}


def _str_allocation_pools(allocation_pools):
    if isinstance(allocation_pools, str):
        return allocation_pools
    return '\n'.join(['%s,%s' % (pool['start'], pool['end'])
                      for pool in allocation_pools])


def _str_dns_nameservers(dns_nameservers):
    if isinstance(dns_nameservers, str):
        return dns_nameservers
    return '\n'.join(dns_nameservers)


def _str_host_routes(host_routes):
    if isinstance(host_routes, str):
        return host_routes
    return '\n'.join(['%s,%s' % (route['destination'], route['nexthop'])
                      for route in host_routes])


class NetworkTests(test.TestCase):

    @test.create_stubs({api.neutron: ('network_list',),
                        quotas: ('tenant_quota_usages',)})
    def test_index(self):
        quota_data = self.quota_usages.first()
        quota_data['networks']['available'] = 5
        quota_data['subnets']['available'] = 5
        api.neutron.network_list(
            IsA(http.HttpRequest),
            tenant_id=self.tenant.id,
            shared=False).AndReturn(self.networks.list())
        api.neutron.network_list(
            IsA(http.HttpRequest),
            shared=True).AndReturn([])
        quotas.tenant_quota_usages(
            IsA(http.HttpRequest)) \
            .MultipleTimes().AndReturn(quota_data)

        self.mox.ReplayAll()

        res = self.client.get(INDEX_URL)
        self.assertTemplateUsed(res, 'project/networks/index.html')
        networks = res.context['networks_table'].data
        self.assertItemsEqual(networks, self.networks.list())

    @test.create_stubs({api.neutron: ('network_list',),
                        quotas: ('tenant_quota_usages',)})
    def test_index_network_list_exception(self):
        quota_data = self.neutron_quota_usages.first()
        api.neutron.network_list(
            IsA(http.HttpRequest),
            tenant_id=self.tenant.id,
            shared=False).MultipleTimes().AndRaise(self.exceptions.neutron)
        quotas.tenant_quota_usages(
            IsA(http.HttpRequest)) \
            .MultipleTimes().AndReturn(quota_data)
        self.mox.ReplayAll()

        res = self.client.get(INDEX_URL)

        self.assertTemplateUsed(res, 'project/networks/index.html')
        self.assertEqual(len(res.context['networks_table'].data), 0)
        self.assertMessageCount(res, error=1)

    @test.create_stubs({api.neutron: ('network_get',
                                      'subnet_list',
                                      'port_list',
                                      'is_extension_supported',),
                        quotas: ('tenant_quota_usages',)})
    def test_network_detail(self):
        self._test_network_detail()

    @test.create_stubs({api.neutron: ('network_get',
                                      'subnet_list',
                                      'port_list',
                                      'is_extension_supported',),
                        quotas: ('tenant_quota_usages',)})
    def test_network_detail_with_mac_learning(self):
        self._test_network_detail(mac_learning=True)

    def _test_network_detail(self, mac_learning=False):
        quota_data = self.neutron_quota_usages.first()
        network_id = self.networks.first().id
        api.neutron.network_get(IsA(http.HttpRequest), network_id)\
            .AndReturn(self.networks.first())
        api.neutron.subnet_list(IsA(http.HttpRequest), network_id=network_id)\
            .AndReturn([self.subnets.first()])
        api.neutron.port_list(IsA(http.HttpRequest), network_id=network_id)\
            .AndReturn([self.ports.first()])
        api.neutron.network_get(IsA(http.HttpRequest), network_id)\
            .AndReturn(self.networks.first())
        api.neutron.is_extension_supported(IsA(http.HttpRequest),
                                           'mac-learning')\
            .AndReturn(mac_learning)
        quotas.tenant_quota_usages(
            IsA(http.HttpRequest)) \
            .MultipleTimes().AndReturn(quota_data)
        self.mox.ReplayAll()

        res = self.client.get(reverse('horizon:project:networks:detail',
                                      args=[network_id]))

        self.assertTemplateUsed(res, 'project/networks/detail.html')
        subnets = res.context['subnets_table'].data
        ports = res.context['ports_table'].data
        self.assertItemsEqual(subnets, [self.subnets.first()])
        self.assertItemsEqual(ports, [self.ports.first()])

    @test.create_stubs({api.neutron: ('network_get',
                                      'subnet_list',
                                      'port_list',
                                      'is_extension_supported',)})
    def test_network_detail_network_exception(self):
        self._test_network_detail_network_exception()

    @test.create_stubs({api.neutron: ('network_get',
                                      'subnet_list',
                                      'port_list',
                                      'is_extension_supported',)})
    def test_network_detail_network_exception_with_mac_learning(self):
        self._test_network_detail_network_exception(mac_learning=True)

    def _test_network_detail_network_exception(self, mac_learning=False):
        network_id = self.networks.first().id
        api.neutron.network_get(IsA(http.HttpRequest), network_id)\
            .AndRaise(self.exceptions.neutron)
        api.neutron.is_extension_supported(IsA(http.HttpRequest),
                                           'mac-learning')\
            .AndReturn(mac_learning)
        self.mox.ReplayAll()

        url = reverse('horizon:project:networks:detail', args=[network_id])
        res = self.client.get(url)

        redir_url = INDEX_URL
        self.assertRedirectsNoFollow(res, redir_url)

    @test.create_stubs({api.neutron: ('network_get',
                                      'subnet_list',
                                      'port_list',
                                      'is_extension_supported',),
                        quotas: ('tenant_quota_usages',)})
    def test_network_detail_subnet_exception(self):
        self._test_network_detail_subnet_exception()

    @test.create_stubs({api.neutron: ('network_get',
                                      'subnet_list',
                                      'port_list',
                                      'is_extension_supported',),
                        quotas: ('tenant_quota_usages',)})
    def test_network_detail_subnet_exception_with_mac_learning(self):
        self._test_network_detail_subnet_exception(mac_learning=True)

    def _test_network_detail_subnet_exception(self, mac_learning=False):
        network_id = self.networks.first().id
        quota_data = self.neutron_quota_usages.first()
        quota_data['networks']['available'] = 5
        quota_data['subnets']['available'] = 5
        api.neutron.network_get(IsA(http.HttpRequest), network_id).\
            AndReturn(self.networks.first())
        api.neutron.subnet_list(IsA(http.HttpRequest), network_id=network_id).\
            AndRaise(self.exceptions.neutron)
        api.neutron.port_list(IsA(http.HttpRequest), network_id=network_id).\
            AndReturn([self.ports.first()])
        # Called from SubnetTable
        api.neutron.is_extension_supported(IsA(http.HttpRequest),
                                           'mac-learning')\
            .AndReturn(mac_learning)
        quotas.tenant_quota_usages(
            IsA(http.HttpRequest)) \
            .MultipleTimes().AndReturn(quota_data)
        self.mox.ReplayAll()

        res = self.client.get(reverse('horizon:project:networks:detail',
                                      args=[network_id]))

        self.assertTemplateUsed(res, 'project/networks/detail.html')
        subnets = res.context['subnets_table'].data
        ports = res.context['ports_table'].data
        self.assertEqual(len(subnets), 0)
        self.assertItemsEqual(ports, [self.ports.first()])

    @test.create_stubs({api.neutron: ('network_get',
                                      'subnet_list',
                                      'port_list',
                                      'is_extension_supported',),
                        quotas: ('tenant_quota_usages',)})
    def test_network_detail_port_exception(self):
        self._test_network_detail_port_exception()

    @test.create_stubs({api.neutron: ('network_get',
                                      'subnet_list',
                                      'port_list',
                                      'is_extension_supported',),
                        quotas: ('tenant_quota_usages',)})
    def test_network_detail_port_exception_with_mac_learning(self):
        self._test_network_detail_port_exception(mac_learning=True)

    def _test_network_detail_port_exception(self, mac_learning=False):
        network_id = self.networks.first().id
        quota_data = self.neutron_quota_usages.first()
        quota_data['subnets']['available'] = 5
        api.neutron.network_get(IsA(http.HttpRequest), network_id).\
            AndReturn(self.networks.first())
        api.neutron.subnet_list(IsA(http.HttpRequest), network_id=network_id).\
            AndReturn([self.subnets.first()])
        api.neutron.port_list(IsA(http.HttpRequest), network_id=network_id).\
            AndRaise(self.exceptions.neutron)
        # Called from SubnetTable
        api.neutron.network_get(IsA(http.HttpRequest), network_id).\
            AndReturn(self.networks.first())
        api.neutron.is_extension_supported(IsA(http.HttpRequest),
                                           'mac-learning')\
            .AndReturn(mac_learning)
        quotas.tenant_quota_usages(
            IsA(http.HttpRequest)) \
            .MultipleTimes().AndReturn(quota_data)
        self.mox.ReplayAll()

        res = self.client.get(reverse('horizon:project:networks:detail',
                                      args=[network_id]))

        self.assertTemplateUsed(res, 'project/networks/detail.html')
        subnets = res.context['subnets_table'].data
        ports = res.context['ports_table'].data
        self.assertItemsEqual(subnets, [self.subnets.first()])
        self.assertEqual(len(ports), 0)

    def test_network_create_get(self):
        self.mox.ReplayAll()

        url = reverse('horizon:project:networks:create')
        res = self.client.get(url)

        workflow = res.context['workflow']
        self.assertTemplateUsed(res, views.WorkflowView.template_name)
        self.assertEqual(workflow.name, workflows.CreateNetwork.name)
        expected_objs = ['<CreateNetworkInfo: createnetworkinfoaction>',
                         '<CreateSubnetInfo: createsubnetinfoaction>',
                         '<CreateSubnetDetail: createsubnetdetailaction>']
        self.assertQuerysetEqual(workflow.steps, expected_objs)

    @test.create_stubs({api.neutron: ('network_create',)})
    def test_network_create_post(self):
        network = self.networks.first()
        params = {'name': network.name,
                  'admin_state_up': network.admin_state_up}
        api.neutron.network_create(IsA(http.HttpRequest),
                                   **params).AndReturn(network)
        self.mox.ReplayAll()

        form_data = {'net_name': network.name,
                     'admin_state': network.admin_state_up,
                     # subnet
                     'with_subnet': False}
        form_data.update(form_data_no_subnet())
        url = reverse('horizon:project:networks:create')
        res = self.client.post(url, form_data)

        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, INDEX_URL)

    @test.create_stubs({api.neutron: ('network_create',
                                      'subnet_create')})
    def test_network_create_post_with_subnet(self,
                                             test_with_ipv6=True):
        network = self.networks.first()
        subnet = self.subnets.first()
        params = {'name': network.name,
                  'admin_state_up': network.admin_state_up}
        subnet_params = {'network_id': network.id,
                         'name': subnet.name,
                         'cidr': subnet.cidr,
                         'ip_version': subnet.ip_version,
                         'gateway_ip': subnet.gateway_ip,
                         'enable_dhcp': subnet.enable_dhcp}
        if not test_with_ipv6:
            subnet.ip_version = 4
            subnet_params['ip_version'] = subnet.ip_version
        api.neutron.network_create(IsA(http.HttpRequest),
                                   **params).AndReturn(network)
        api.neutron.subnet_create(IsA(http.HttpRequest),
                                  **subnet_params).AndReturn(subnet)
        self.mox.ReplayAll()

        form_data = {'net_name': network.name,
                     'admin_state': network.admin_state_up,
                     'with_subnet': True}
        form_data.update(form_data_subnet(subnet, allocation_pools=[]))
        url = reverse('horizon:project:networks:create')
        res = self.client.post(url, form_data)

        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, INDEX_URL)

    @test.update_settings(OPENSTACK_NEUTRON_NETWORK={'enable_ipv6': False})
    def test_create_network_with_ipv6_disabled(self):
        self.test_network_create_post_with_subnet(test_with_ipv6=False)

    @test.create_stubs({api.neutron: ('network_create',)})
    def test_network_create_post_network_exception(self):
        network = self.networks.first()
        params = {'name': network.name,
                  'admin_state_up': network.admin_state_up}
        api.neutron.network_create(IsA(http.HttpRequest),
                                   **params).AndRaise(self.exceptions.neutron)
        self.mox.ReplayAll()

        form_data = {'net_name': network.name,
                     'admin_state': network.admin_state_up,
                     # subnet
                     'with_subnet': False}
        form_data.update(form_data_no_subnet())
        url = reverse('horizon:project:networks:create')
        res = self.client.post(url, form_data)

        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, INDEX_URL)

    @test.create_stubs({api.neutron: ('network_create',)})
    def test_network_create_post_with_subnet_network_exception(self):
        network = self.networks.first()
        subnet = self.subnets.first()
        params = {'name': network.name,
                  'admin_state_up': network.admin_state_up}
        api.neutron.network_create(IsA(http.HttpRequest),
                                   **params).AndRaise(self.exceptions.neutron)
        self.mox.ReplayAll()

        form_data = {'net_name': network.name,
                     'admin_state': network.admin_state_up,
                     'with_subnet': True}
        form_data.update(form_data_subnet(subnet, allocation_pools=[]))
        url = reverse('horizon:project:networks:create')
        res = self.client.post(url, form_data)

        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, INDEX_URL)

    @test.create_stubs({api.neutron: ('network_create',
                                      'network_delete',
                                      'subnet_create')})
    def test_network_create_post_with_subnet_subnet_exception(self):
        network = self.networks.first()
        subnet = self.subnets.first()
        params = {'name': network.name,
                  'admin_state_up': network.admin_state_up}
        api.neutron.network_create(IsA(http.HttpRequest),
                                   **params).AndReturn(network)
        api.neutron.subnet_create(IsA(http.HttpRequest),
                                  network_id=network.id,
                                  name=subnet.name,
                                  cidr=subnet.cidr,
                                  ip_version=subnet.ip_version,
                                  gateway_ip=subnet.gateway_ip,
                                  enable_dhcp=subnet.enable_dhcp)\
            .AndRaise(self.exceptions.neutron)
        api.neutron.network_delete(IsA(http.HttpRequest),
                                   network.id)
        self.mox.ReplayAll()

        form_data = {'net_name': network.name,
                     'admin_state': network.admin_state_up,
                     'with_subnet': True}
        form_data.update(form_data_subnet(subnet, allocation_pools=[]))
        url = reverse('horizon:project:networks:create')
        res = self.client.post(url, form_data)

        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, INDEX_URL)

    def test_network_create_post_with_subnet_nocidr(self):
        network = self.networks.first()
        subnet = self.subnets.first()
        self.mox.ReplayAll()

        form_data = {'net_name': network.name,
                     'admin_state': network.admin_state_up,
                     'with_subnet': True}
        form_data.update(form_data_subnet(subnet, cidr='',
                                          allocation_pools=[]))
        url = reverse('horizon:project:networks:create')
        res = self.client.post(url, form_data)

        self.assertContains(res, escape('Specify "Network Address" or '
                                        'clear "Create Subnet" checkbox.'))

    def test_network_create_post_with_subnet_cidr_without_mask(self):
        network = self.networks.first()
        subnet = self.subnets.first()

        form_data = {'net_name': network.name,
                     'admin_state': network.admin_state_up,
                     'with_subnet': True}
        form_data.update(form_data_subnet(subnet, cidr='10.0.0.0',
                                          allocation_pools=[]))
        url = reverse('horizon:project:networks:create')
        res = self.client.post(url, form_data)

        expected_msg = "The subnet in the Network Address is too small (/32)."
        self.assertContains(res, expected_msg)

    def test_network_create_post_with_subnet_cidr_inconsistent(self):
        network = self.networks.first()
        subnet = self.subnets.first()
        self.mox.ReplayAll()

        # dummy IPv6 address
        cidr = '2001:0DB8:0:CD30:123:4567:89AB:CDEF/60'
        form_data = {'net_name': network.name,
                     'admin_state': network.admin_state_up,
                     'with_subnet': True}
        form_data.update(form_data_subnet(subnet, cidr=cidr,
                                          allocation_pools=[]))
        url = reverse('horizon:project:networks:create')
        res = self.client.post(url, form_data)

        expected_msg = 'Network Address and IP version are inconsistent.'
        self.assertContains(res, expected_msg)

    def test_network_create_post_with_subnet_gw_inconsistent(self):
        network = self.networks.first()
        subnet = self.subnets.first()
        self.mox.ReplayAll()

        # dummy IPv6 address
        gateway_ip = '2001:0DB8:0:CD30:123:4567:89AB:CDEF'
        form_data = {'net_name': network.name,
                     'admin_state': network.admin_state_up,
                     'with_subnet': True}
        form_data.update(form_data_subnet(subnet, gateway_ip=gateway_ip,
                                          allocation_pools=[]))
        url = reverse('horizon:project:networks:create')
        res = self.client.post(url, form_data)

        self.assertContains(res, 'Gateway IP and IP version are inconsistent.')

    @test.create_stubs({api.neutron: ('network_get',)})
    def test_network_update_get(self):
        network = self.networks.first()
        api.neutron.network_get(IsA(http.HttpRequest), network.id)\
            .AndReturn(network)

        self.mox.ReplayAll()

        url = reverse('horizon:project:networks:update', args=[network.id])
        res = self.client.get(url)

        self.assertTemplateUsed(res, 'project/networks/update.html')

    @test.create_stubs({api.neutron: ('network_get',)})
    def test_network_update_get_exception(self):
        network = self.networks.first()
        api.neutron.network_get(IsA(http.HttpRequest), network.id)\
            .AndRaise(self.exceptions.neutron)

        self.mox.ReplayAll()

        url = reverse('horizon:project:networks:update', args=[network.id])
        res = self.client.get(url)

        redir_url = INDEX_URL
        self.assertRedirectsNoFollow(res, redir_url)

    @test.create_stubs({api.neutron: ('network_update',
                                      'network_get',)})
    def test_network_update_post(self):
        network = self.networks.first()
        api.neutron.network_update(IsA(http.HttpRequest), network.id,
                                   name=network.name,
                                   admin_state_up=network.admin_state_up)\
            .AndReturn(network)
        api.neutron.network_get(IsA(http.HttpRequest), network.id)\
            .AndReturn(network)
        self.mox.ReplayAll()

        form_data = {'network_id': network.id,
                     'name': network.name,
                     'admin_state': network.admin_state_up,
                     'tenant_id': network.tenant_id}
        url = reverse('horizon:project:networks:update', args=[network.id])
        res = self.client.post(url, form_data)

        self.assertRedirectsNoFollow(res, INDEX_URL)

    @test.create_stubs({api.neutron: ('network_update',
                                      'network_get',)})
    def test_network_update_post_exception(self):
        network = self.networks.first()
        api.neutron.network_update(IsA(http.HttpRequest), network.id,
                                   name=network.name,
                                   admin_state_up=network.admin_state_up)\
            .AndRaise(self.exceptions.neutron)
        api.neutron.network_get(IsA(http.HttpRequest), network.id)\
            .AndReturn(network)
        self.mox.ReplayAll()

        form_data = {'network_id': network.id,
                     'name': network.name,
                     'admin_state': network.admin_state_up,
                     'tenant_id': network.tenant_id}
        url = reverse('horizon:project:networks:update', args=[network.id])
        res = self.client.post(url, form_data)

        self.assertRedirectsNoFollow(res, INDEX_URL)

    @test.create_stubs({api.neutron: ('network_get',
                                      'network_list',
                                      'network_delete')})
    def test_delete_network_no_subnet(self):
        network = self.networks.first()
        network.subnets = []
        api.neutron.network_get(IsA(http.HttpRequest),
                                network.id,
                                expand_subnet=False)\
            .AndReturn(network)
        api.neutron.network_list(IsA(http.HttpRequest),
                                 tenant_id=network.tenant_id,
                                 shared=False)\
            .AndReturn([network])
        api.neutron.network_list(IsA(http.HttpRequest),
                                 shared=True)\
            .AndReturn([])
        api.neutron.network_delete(IsA(http.HttpRequest), network.id)

        self.mox.ReplayAll()

        form_data = {'action': 'networks__delete__%s' % network.id}
        res = self.client.post(INDEX_URL, form_data)
        self.assertRedirectsNoFollow(res, INDEX_URL)

    @test.create_stubs({api.neutron: ('network_get',
                                      'network_list',
                                      'network_delete',
                                      'subnet_delete')})
    def test_delete_network_with_subnet(self):
        network = self.networks.first()
        network.subnets = [subnet.id for subnet in network.subnets]
        subnet_id = network.subnets[0]
        api.neutron.network_get(IsA(http.HttpRequest),
                                network.id,
                                expand_subnet=False)\
            .AndReturn(network)
        api.neutron.network_list(IsA(http.HttpRequest),
                                 tenant_id=network.tenant_id,
                                 shared=False)\
            .AndReturn([network])
        api.neutron.network_list(IsA(http.HttpRequest), shared=True)\
            .AndReturn([])
        api.neutron.subnet_delete(IsA(http.HttpRequest), subnet_id)
        api.neutron.network_delete(IsA(http.HttpRequest), network.id)

        self.mox.ReplayAll()

        form_data = {'action': 'networks__delete__%s' % network.id}
        res = self.client.post(INDEX_URL, form_data)

        self.assertRedirectsNoFollow(res, INDEX_URL)

    @test.create_stubs({api.neutron: ('network_get',
                                      'network_list',
                                      'network_delete',
                                      'subnet_delete')})
    def test_delete_network_exception(self):
        network = self.networks.first()
        network.subnets = [subnet.id for subnet in network.subnets]
        subnet_id = network.subnets[0]
        api.neutron.network_get(IsA(http.HttpRequest),
                                network.id,
                                expand_subnet=False)\
            .AndReturn(network)
        api.neutron.network_list(IsA(http.HttpRequest),
                                 tenant_id=network.tenant_id,
                                 shared=False)\
            .AndReturn([network])
        api.neutron.network_list(IsA(http.HttpRequest),
                                 shared=True)\
            .AndReturn([])
        api.neutron.subnet_delete(IsA(http.HttpRequest), subnet_id)
        api.neutron.network_delete(IsA(http.HttpRequest), network.id)\
            .AndRaise(self.exceptions.neutron)

        self.mox.ReplayAll()

        form_data = {'action': 'networks__delete__%s' % network.id}
        res = self.client.post(INDEX_URL, form_data)

        self.assertRedirectsNoFollow(res, INDEX_URL)


class NetworkSubnetTests(test.TestCase):

    @test.create_stubs({api.neutron: ('network_get', 'subnet_get',)})
    def test_subnet_detail(self):
        network = self.networks.first()
        subnet = self.subnets.first()

        api.neutron.network_get(IsA(http.HttpRequest), network.id)\
            .AndReturn(network)
        api.neutron.subnet_get(IsA(http.HttpRequest), subnet.id)\
            .AndReturn(subnet)

        self.mox.ReplayAll()

        url = reverse('horizon:project:networks:subnets:detail',
                      args=[subnet.id])
        res = self.client.get(url)

        self.assertTemplateUsed(res, 'project/networks/subnets/detail.html')
        self.assertEqual(res.context['subnet'].id, subnet.id)

    @test.create_stubs({api.neutron: ('subnet_get',)})
    def test_subnet_detail_exception(self):
        subnet = self.subnets.first()
        api.neutron.subnet_get(IsA(http.HttpRequest), subnet.id)\
            .AndRaise(self.exceptions.neutron)

        self.mox.ReplayAll()

        url = reverse('horizon:project:networks:subnets:detail',
                      args=[subnet.id])
        res = self.client.get(url)

        self.assertRedirectsNoFollow(res, INDEX_URL)

    @test.create_stubs({api.neutron: ('network_get',)})
    def test_subnet_create_get(self):
        network = self.networks.first()
        api.neutron.network_get(IsA(http.HttpRequest),
                                network.id)\
            .AndReturn(self.networks.first())
        self.mox.ReplayAll()

        url = reverse('horizon:project:networks:addsubnet',
                      args=[network.id])
        res = self.client.get(url)

        self.assertTemplateUsed(res, views.WorkflowView.template_name)

    @test.create_stubs({api.neutron: ('network_get',
                                      'subnet_create',)})
    def test_subnet_create_post(self):
        network = self.networks.first()
        subnet = self.subnets.first()
        api.neutron.network_get(IsA(http.HttpRequest),
                                network.id)\
            .AndReturn(self.networks.first())
        api.neutron.subnet_create(IsA(http.HttpRequest),
                                  network_id=network.id,
                                  name=subnet.name,
                                  cidr=subnet.cidr,
                                  ip_version=subnet.ip_version,
                                  gateway_ip=subnet.gateway_ip,
                                  enable_dhcp=subnet.enable_dhcp,
                                  allocation_pools=subnet.allocation_pools)\
            .AndReturn(subnet)
        self.mox.ReplayAll()

        form_data = form_data_subnet(subnet)
        url = reverse('horizon:project:networks:addsubnet',
                      args=[subnet.network_id])
        res = self.client.post(url, form_data)

        self.assertNoFormErrors(res)
        redir_url = reverse('horizon:project:networks:detail',
                            args=[subnet.network_id])
        self.assertRedirectsNoFollow(res, redir_url)

    @test.create_stubs({api.neutron: ('network_get',
                                      'subnet_create',)})
    def test_subnet_create_post_with_additional_attributes(self):
        network = self.networks.list()[1]
        subnet = self.subnets.list()[1]
        api.neutron.network_get(IsA(http.HttpRequest),
                                network.id)\
            .AndReturn(self.networks.first())
        api.neutron.subnet_create(IsA(http.HttpRequest),
                                  network_id=network.id,
                                  name=subnet.name,
                                  cidr=subnet.cidr,
                                  ip_version=subnet.ip_version,
                                  gateway_ip=subnet.gateway_ip,
                                  enable_dhcp=subnet.enable_dhcp,
                                  allocation_pools=subnet.allocation_pools,
                                  dns_nameservers=subnet.dns_nameservers,
                                  host_routes=subnet.host_routes)\
            .AndReturn(subnet)
        self.mox.ReplayAll()

        form_data = form_data_subnet(subnet)
        url = reverse('horizon:project:networks:addsubnet',
                      args=[subnet.network_id])
        res = self.client.post(url, form_data)

        self.assertNoFormErrors(res)
        redir_url = reverse('horizon:project:networks:detail',
                            args=[subnet.network_id])
        self.assertRedirectsNoFollow(res, redir_url)

    @test.create_stubs({api.neutron: ('network_get',
                                      'subnet_create',)})
    def test_subnet_create_post_with_additional_attributes_no_gateway(self):
        network = self.networks.first()
        subnet = self.subnets.first()
        api.neutron.network_get(IsA(http.HttpRequest),
                                network.id)\
            .AndReturn(self.networks.first())
        api.neutron.subnet_create(IsA(http.HttpRequest),
                                  network_id=network.id,
                                  name=subnet.name,
                                  cidr=subnet.cidr,
                                  ip_version=subnet.ip_version,
                                  gateway_ip=None,
                                  enable_dhcp=subnet.enable_dhcp,
                                  allocation_pools=subnet.allocation_pools)\
            .AndReturn(subnet)
        self.mox.ReplayAll()

        form_data = form_data_subnet(subnet, gateway_ip=None)
        url = reverse('horizon:project:networks:addsubnet',
                      args=[subnet.network_id])
        res = self.client.post(url, form_data)

        self.assertNoFormErrors(res)
        redir_url = reverse('horizon:project:networks:detail',
                            args=[subnet.network_id])
        self.assertRedirectsNoFollow(res, redir_url)

    @test.create_stubs({api.neutron: ('network_get',
                                      'subnet_create',)})
    def test_subnet_create_post_network_exception(self):
        network = self.networks.first()
        subnet = self.subnets.first()
        api.neutron.network_get(IsA(http.HttpRequest),
                                network.id)\
            .AndRaise(self.exceptions.neutron)
        self.mox.ReplayAll()

        form_data = form_data_subnet(subnet,
                                     allocation_pools=[])
        url = reverse('horizon:project:networks:addsubnet',
                      args=[subnet.network_id])
        res = self.client.post(url, form_data)

        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, INDEX_URL)

    @test.create_stubs({api.neutron: ('network_get',
                                      'subnet_create',)})
    def test_subnet_create_post_subnet_exception(self):
        network = self.networks.first()
        subnet = self.subnets.first()
        api.neutron.network_get(IsA(http.HttpRequest),
                                network.id)\
            .AndReturn(self.networks.first())
        api.neutron.subnet_create(IsA(http.HttpRequest),
                                  network_id=network.id,
                                  name=subnet.name,
                                  cidr=subnet.cidr,
                                  ip_version=subnet.ip_version,
                                  gateway_ip=subnet.gateway_ip,
                                  enable_dhcp=subnet.enable_dhcp)\
            .AndRaise(self.exceptions.neutron)
        self.mox.ReplayAll()

        form_data = form_data_subnet(subnet,
                                     allocation_pools=[])
        url = reverse('horizon:project:networks:addsubnet',
                      args=[subnet.network_id])
        res = self.client.post(url, form_data)

        redir_url = reverse('horizon:project:networks:detail',
                            args=[subnet.network_id])
        self.assertRedirectsNoFollow(res, redir_url)

    @test.create_stubs({api.neutron: ('network_get',)})
    def test_subnet_create_post_cidr_inconsistent(self):
        network = self.networks.first()
        subnet = self.subnets.first()
        api.neutron.network_get(IsA(http.HttpRequest),
                                network.id)\
            .AndReturn(self.networks.first())
        self.mox.ReplayAll()

        # dummy IPv6 address
        cidr = '2001:0DB8:0:CD30:123:4567:89AB:CDEF/60'
        form_data = form_data_subnet(subnet, cidr=cidr,
                                     allocation_pools=[])
        url = reverse('horizon:project:networks:addsubnet',
                      args=[subnet.network_id])
        res = self.client.post(url, form_data)

        expected_msg = 'Network Address and IP version are inconsistent.'
        self.assertFormErrors(res, 1, expected_msg)
        self.assertTemplateUsed(res, views.WorkflowView.template_name)

    @test.create_stubs({api.neutron: ('network_get',)})
    def test_subnet_create_post_gw_inconsistent(self):
        network = self.networks.first()
        subnet = self.subnets.first()
        api.neutron.network_get(IsA(http.HttpRequest),
                                network.id)\
            .AndReturn(self.networks.first())
        self.mox.ReplayAll()

        # dummy IPv6 address
        gateway_ip = '2001:0DB8:0:CD30:123:4567:89AB:CDEF'
        form_data = form_data_subnet(subnet, gateway_ip=gateway_ip,
                                     allocation_pools=[])
        url = reverse('horizon:project:networks:addsubnet',
                      args=[subnet.network_id])
        res = self.client.post(url, form_data)

        self.assertContains(res, 'Gateway IP and IP version are inconsistent.')

    @test.create_stubs({api.neutron: ('network_get',)})
    def test_subnet_create_post_invalid_pools_start_only(self):
        network = self.networks.first()
        subnet = self.subnets.first()
        api.neutron.network_get(IsA(http.HttpRequest),
                                network.id).AndReturn(network)
        self.mox.ReplayAll()

        # Start only allocation_pools
        allocation_pools = '10.0.0.2'
        form_data = form_data_subnet(subnet,
                                     allocation_pools=allocation_pools)
        url = reverse('horizon:project:networks:addsubnet',
                      args=[subnet.network_id])
        res = self.client.post(url, form_data)

        self.assertContains(res,
                            'Start and end addresses must be specified '
                            '(value=%s)' % allocation_pools)

    @test.create_stubs({api.neutron: ('network_get',)})
    def test_subnet_create_post_invalid_pools_three_entries(self):
        network = self.networks.first()
        subnet = self.subnets.first()
        api.neutron.network_get(IsA(http.HttpRequest),
                                network.id).AndReturn(network)
        self.mox.ReplayAll()

        # pool with three entries
        allocation_pools = '10.0.0.2,10.0.0.3,10.0.0.4'
        form_data = form_data_subnet(subnet,
                                     allocation_pools=allocation_pools)
        url = reverse('horizon:project:networks:addsubnet',
                      args=[subnet.network_id])
        res = self.client.post(url, form_data)

        self.assertContains(res,
                            'Start and end addresses must be specified '
                            '(value=%s)' % allocation_pools)

    @test.create_stubs({api.neutron: ('network_get',)})
    def test_subnet_create_post_invalid_pools_invalid_address(self):
        network = self.networks.first()
        subnet = self.subnets.first()
        api.neutron.network_get(IsA(http.HttpRequest),
                                network.id).AndReturn(network)
        self.mox.ReplayAll()

        # end address is not a valid IP address
        allocation_pools = '10.0.0.2,invalid_address'
        form_data = form_data_subnet(subnet,
                                     allocation_pools=allocation_pools)
        url = reverse('horizon:project:networks:addsubnet',
                      args=[subnet.network_id])
        res = self.client.post(url, form_data)

        self.assertContains(res,
                            'allocation_pools: Invalid IP address '
                            '(value=%s)' % allocation_pools.split(',')[1])

    @test.create_stubs({api.neutron: ('network_get',)})
    def test_subnet_create_post_invalid_pools_ip_network(self):
        network = self.networks.first()
        subnet = self.subnets.first()
        api.neutron.network_get(IsA(http.HttpRequest),
                                network.id).AndReturn(network)
        self.mox.ReplayAll()

        # start address is CIDR
        allocation_pools = '10.0.0.2/24,10.0.0.5'
        form_data = form_data_subnet(subnet,
                                     allocation_pools=allocation_pools)
        url = reverse('horizon:project:networks:addsubnet',
                      args=[subnet.network_id])
        res = self.client.post(url, form_data)

        self.assertContains(res,
                            'allocation_pools: Invalid IP address '
                            '(value=%s)' % allocation_pools.split(',')[0])

    @test.create_stubs({api.neutron: ('network_get',)})
    def test_subnet_create_post_invalid_pools_start_larger_than_end(self):
        network = self.networks.first()
        subnet = self.subnets.first()
        api.neutron.network_get(IsA(http.HttpRequest),
                                network.id).AndReturn(network)
        self.mox.ReplayAll()

        # start address is larger than end address
        allocation_pools = '10.0.0.254,10.0.0.2'
        form_data = form_data_subnet(subnet,
                                     allocation_pools=allocation_pools)
        url = reverse('horizon:project:networks:addsubnet',
                      args=[subnet.network_id])
        res = self.client.post(url, form_data)

        self.assertContains(res,
                            'Start address is larger than end address '
                            '(value=%s)' % allocation_pools)

    @test.create_stubs({api.neutron: ('network_get',)})
    def test_subnet_create_post_invalid_nameservers(self):
        network = self.networks.first()
        subnet = self.subnets.first()
        api.neutron.network_get(IsA(http.HttpRequest),
                                network.id).AndReturn(network)
        self.mox.ReplayAll()

        # invalid DNS server address
        dns_nameservers = ['192.168.0.2', 'invalid_address']
        form_data = form_data_subnet(subnet, dns_nameservers=dns_nameservers,
                                     allocation_pools=[])
        url = reverse('horizon:project:networks:addsubnet',
                      args=[subnet.network_id])
        res = self.client.post(url, form_data)

        self.assertContains(res,
                            'dns_nameservers: Invalid IP address '
                            '(value=%s)' % dns_nameservers[1])

    @test.create_stubs({api.neutron: ('network_get',)})
    def test_subnet_create_post_invalid_routes_destination_only(self):
        network = self.networks.first()
        subnet = self.subnets.first()
        api.neutron.network_get(IsA(http.HttpRequest),
                                network.id).AndReturn(network)
        self.mox.ReplayAll()

        # Start only host_route
        host_routes = '192.168.0.0/24'
        form_data = form_data_subnet(subnet,
                                     allocation_pools=[],
                                     host_routes=host_routes)
        url = reverse('horizon:project:networks:addsubnet',
                      args=[subnet.network_id])
        res = self.client.post(url, form_data)

        self.assertContains(res,
                            'Host Routes format error: '
                            'Destination CIDR and nexthop must be specified '
                            '(value=%s)' % host_routes)

    @test.create_stubs({api.neutron: ('network_get',)})
    def test_subnet_create_post_invalid_routes_three_entries(self):
        network = self.networks.first()
        subnet = self.subnets.first()
        api.neutron.network_get(IsA(http.HttpRequest),
                                network.id).AndReturn(network)
        self.mox.ReplayAll()

        # host_route with three entries
        host_routes = 'aaaa,bbbb,cccc'
        form_data = form_data_subnet(subnet,
                                     allocation_pools=[],
                                     host_routes=host_routes)
        url = reverse('horizon:project:networks:addsubnet',
                      args=[subnet.network_id])
        res = self.client.post(url, form_data)

        self.assertContains(res,
                            'Host Routes format error: '
                            'Destination CIDR and nexthop must be specified '
                            '(value=%s)' % host_routes)

    @test.create_stubs({api.neutron: ('network_get',)})
    def test_subnet_create_post_invalid_routes_invalid_destination(self):
        network = self.networks.first()
        subnet = self.subnets.first()
        api.neutron.network_get(IsA(http.HttpRequest),
                                network.id).AndReturn(network)
        self.mox.ReplayAll()

        # invalid destination network
        host_routes = '172.16.0.0/64,10.0.0.253'
        form_data = form_data_subnet(subnet,
                                     host_routes=host_routes,
                                     allocation_pools=[])
        url = reverse('horizon:project:networks:addsubnet',
                      args=[subnet.network_id])
        res = self.client.post(url, form_data)

        self.assertContains(res,
                            'host_routes: Invalid IP address '
                            '(value=%s)' % host_routes.split(',')[0])

    @test.create_stubs({api.neutron: ('network_get',)})
    def test_subnet_create_post_invalid_routes_nexthop_ip_network(self):
        network = self.networks.first()
        subnet = self.subnets.first()
        api.neutron.network_get(IsA(http.HttpRequest),
                                network.id).AndReturn(network)
        self.mox.ReplayAll()

        # nexthop is not an IP address
        host_routes = '172.16.0.0/24,10.0.0.253/24'
        form_data = form_data_subnet(subnet,
                                     host_routes=host_routes,
                                     allocation_pools=[])
        url = reverse('horizon:project:networks:addsubnet',
                      args=[subnet.network_id])
        res = self.client.post(url, form_data)

        self.assertContains(res,
                            'host_routes: Invalid IP address '
                            '(value=%s)' % host_routes.split(',')[1])

    @test.create_stubs({api.neutron: ('network_get',
                                      'subnet_create',)})
    def test_v6subnet_create_post(self):
        network = self.networks.get(name="v6_net1")
        subnet = self.subnets.get(name="v6_subnet1")
        api.neutron.network_get(IsA(http.HttpRequest),
                                network.id)\
            .AndReturn(network)
        api.neutron.subnet_create(IsA(http.HttpRequest),
                                  network_id=network.id,
                                  name=subnet.name,
                                  cidr=subnet.cidr,
                                  ip_version=subnet.ip_version,
                                  gateway_ip=subnet.gateway_ip,
                                  enable_dhcp=subnet.enable_dhcp,
                                  allocation_pools=subnet.allocation_pools)\
            .AndReturn(subnet)
        self.mox.ReplayAll()

        form_data = form_data_subnet(subnet)
        url = reverse('horizon:project:networks:addsubnet',
                      args=[subnet.network_id])
        res = self.client.post(url, form_data)

        self.assertNoFormErrors(res)
        redir_url = reverse('horizon:project:networks:detail',
                            args=[subnet.network_id])
        self.assertRedirectsNoFollow(res, redir_url)

    @test.create_stubs({api.neutron: ('network_get',
                                      'subnet_create',)})
    def test_v6subnet_create_post_with_slaac_attributes(self):
        network = self.networks.get(name="v6_net2")
        subnet = self.subnets.get(name="v6_subnet2")
        api.neutron.network_get(IsA(http.HttpRequest),
                                network.id)\
            .AndReturn(network)
        api.neutron.subnet_create(IsA(http.HttpRequest),
                                  network_id=network.id,
                                  name=subnet.name,
                                  cidr=subnet.cidr,
                                  ip_version=subnet.ip_version,
                                  gateway_ip=subnet.gateway_ip,
                                  enable_dhcp=subnet.enable_dhcp,
                                  allocation_pools=subnet.allocation_pools,
                                  ipv6_address_mode='slaac',
                                  ipv6_ra_mode='slaac')\
            .AndReturn(subnet)
        self.mox.ReplayAll()

        form_data = form_data_subnet(subnet)
        url = reverse('horizon:project:networks:addsubnet',
                      args=[subnet.network_id])
        res = self.client.post(url, form_data)

        self.assertNoFormErrors(res)
        redir_url = reverse('horizon:project:networks:detail',
                            args=[subnet.network_id])
        self.assertRedirectsNoFollow(res, redir_url)

    @test.create_stubs({api.neutron: ('subnet_update',
                                      'subnet_get',)})
    def test_subnet_update_post(self):
        subnet = self.subnets.first()
        api.neutron.subnet_get(IsA(http.HttpRequest), subnet.id)\
            .AndReturn(subnet)
        api.neutron.subnet_get(IsA(http.HttpRequest), subnet.id)\
            .AndReturn(subnet)
        api.neutron.subnet_update(IsA(http.HttpRequest), subnet.id,
                                  name=subnet.name,
                                  enable_dhcp=subnet.enable_dhcp,
                                  dns_nameservers=[],
                                  host_routes=[])\
            .AndReturn(subnet)
        self.mox.ReplayAll()

        form_data = form_data_subnet(subnet,
                                     allocation_pools=[])
        url = reverse('horizon:project:networks:editsubnet',
                      args=[subnet.network_id, subnet.id])
        res = self.client.post(url, form_data)

        redir_url = reverse('horizon:project:networks:detail',
                            args=[subnet.network_id])
        self.assertRedirectsNoFollow(res, redir_url)

    @test.create_stubs({api.neutron: ('subnet_update',
                                      'subnet_get',)})
    def test_subnet_update_post_with_gateway_ip(self):
        subnet = self.subnets.first()
        api.neutron.subnet_get(IsA(http.HttpRequest), subnet.id)\
            .AndReturn(subnet)
        api.neutron.subnet_get(IsA(http.HttpRequest), subnet.id)\
            .AndReturn(subnet)
        gateway_ip = '10.0.0.100'
        api.neutron.subnet_update(IsA(http.HttpRequest), subnet.id,
                                  name=subnet.name,
                                  gateway_ip=gateway_ip,
                                  enable_dhcp=subnet.enable_dhcp,
                                  dns_nameservers=[],
                                  host_routes=[])\
            .AndReturn(subnet)
        self.mox.ReplayAll()

        form_data = form_data_subnet(subnet,
                                     gateway_ip=gateway_ip,
                                     allocation_pools=[])
        url = reverse('horizon:project:networks:editsubnet',
                      args=[subnet.network_id, subnet.id])
        res = self.client.post(url, form_data)

        redir_url = reverse('horizon:project:networks:detail',
                            args=[subnet.network_id])
        self.assertRedirectsNoFollow(res, redir_url)

    @test.create_stubs({api.neutron: ('subnet_update',
                                      'subnet_get',)})
    def test_subnet_update_post_no_gateway(self):
        subnet = self.subnets.first()
        api.neutron.subnet_get(IsA(http.HttpRequest), subnet.id)\
            .AndReturn(subnet)
        api.neutron.subnet_get(IsA(http.HttpRequest), subnet.id)\
            .AndReturn(subnet)
        api.neutron.subnet_update(IsA(http.HttpRequest), subnet.id,
                                  name=subnet.name,
                                  gateway_ip=None,
                                  enable_dhcp=subnet.enable_dhcp,
                                  dns_nameservers=[],
                                  host_routes=[])\
            .AndReturn(subnet)
        self.mox.ReplayAll()

        form_data = form_data_subnet(subnet,
                                     gateway_ip=None,
                                     allocation_pools=[])
        url = reverse('horizon:project:networks:editsubnet',
                      args=[subnet.network_id, subnet.id])
        res = self.client.post(url, form_data)

        redir_url = reverse('horizon:project:networks:detail',
                            args=[subnet.network_id])
        self.assertRedirectsNoFollow(res, redir_url)

    @test.create_stubs({api.neutron: ('subnet_update',
                                      'subnet_get',)})
    def test_subnet_update_post_with_additional_attributes(self):
        subnet = self.subnets.list()[1]
        api.neutron.subnet_get(IsA(http.HttpRequest), subnet.id)\
            .AndReturn(subnet)
        api.neutron.subnet_get(IsA(http.HttpRequest), subnet.id)\
            .AndReturn(subnet)
        start = subnet.allocation_pools[0]['start']
        end = subnet.allocation_pools[0]['end']
        api.neutron.subnet_update(IsA(http.HttpRequest), subnet.id,
                                  name=subnet.name,
                                  enable_dhcp=False,
                                  dns_nameservers=subnet.dns_nameservers,
                                  host_routes=subnet.host_routes,
                                  allocation_pools=[{'start': start,
                                                     'end': end}])\
            .AndReturn(subnet)
        self.mox.ReplayAll()

        form_data = form_data_subnet(subnet,
                                     enable_dhcp=False)
        url = reverse('horizon:project:networks:editsubnet',
                      args=[subnet.network_id, subnet.id])
        res = self.client.post(url, form_data)

        redir_url = reverse('horizon:project:networks:detail',
                            args=[subnet.network_id])
        self.assertRedirectsNoFollow(res, redir_url)

    @test.create_stubs({api.neutron: ('subnet_update',
                                      'subnet_get',)})
    def test_subnet_update_post_gw_inconsistent(self):
        subnet = self.subnets.first()
        api.neutron.subnet_get(IsA(http.HttpRequest), subnet.id)\
            .AndReturn(subnet)
        self.mox.ReplayAll()

        # dummy IPv6 address
        gateway_ip = '2001:0DB8:0:CD30:123:4567:89AB:CDEF'
        form_data = form_data_subnet(subnet, gateway_ip=gateway_ip,
                                     allocation_pools=[])
        url = reverse('horizon:project:networks:editsubnet',
                      args=[subnet.network_id, subnet.id])
        res = self.client.post(url, form_data)

        self.assertContains(res, 'Gateway IP and IP version are inconsistent.')

    @test.create_stubs({api.neutron: ('subnet_update',
                                      'subnet_get',)})
    def test_subnet_update_post_invalid_nameservers(self):
        subnet = self.subnets.first()
        api.neutron.subnet_get(IsA(http.HttpRequest), subnet.id)\
            .AndReturn(subnet)
        self.mox.ReplayAll()

        # invalid DNS server address
        dns_nameservers = ['192.168.0.2', 'invalid_address']
        form_data = form_data_subnet(subnet, dns_nameservers=dns_nameservers,
                                     allocation_pools=[])
        url = reverse('horizon:project:networks:editsubnet',
                      args=[subnet.network_id, subnet.id])
        res = self.client.post(url, form_data)

        self.assertContains(res,
                            'dns_nameservers: Invalid IP address '
                            '(value=%s)' % dns_nameservers[1])

    @test.create_stubs({api.neutron: ('subnet_update',
                                      'subnet_get',)})
    def test_subnet_update_post_invalid_routes_destination_only(self):
        subnet = self.subnets.first()
        api.neutron.subnet_get(IsA(http.HttpRequest), subnet.id)\
            .AndReturn(subnet)
        self.mox.ReplayAll()

        # Start only host_route
        host_routes = '192.168.0.0/24'
        form_data = form_data_subnet(subnet,
                                     allocation_pools=[],
                                     host_routes=host_routes)
        url = reverse('horizon:project:networks:editsubnet',
                      args=[subnet.network_id, subnet.id])
        res = self.client.post(url, form_data)

        self.assertContains(res,
                            'Host Routes format error: '
                            'Destination CIDR and nexthop must be specified '
                            '(value=%s)' % host_routes)

    @test.create_stubs({api.neutron: ('subnet_update',
                                      'subnet_get',)})
    def test_subnet_update_post_invalid_routes_three_entries(self):
        subnet = self.subnets.first()
        api.neutron.subnet_get(IsA(http.HttpRequest), subnet.id)\
            .AndReturn(subnet)
        self.mox.ReplayAll()

        # host_route with three entries
        host_routes = 'aaaa,bbbb,cccc'
        form_data = form_data_subnet(subnet,
                                     allocation_pools=[],
                                     host_routes=host_routes)
        url = reverse('horizon:project:networks:editsubnet',
                      args=[subnet.network_id, subnet.id])
        res = self.client.post(url, form_data)

        self.assertContains(res,
                            'Host Routes format error: '
                            'Destination CIDR and nexthop must be specified '
                            '(value=%s)' % host_routes)

    @test.create_stubs({api.neutron: ('subnet_update',
                                      'subnet_get',)})
    def test_subnet_update_post_invalid_routes_invalid_destination(self):
        subnet = self.subnets.first()
        api.neutron.subnet_get(IsA(http.HttpRequest), subnet.id)\
            .AndReturn(subnet)
        self.mox.ReplayAll()

        # invalid destination network
        host_routes = '172.16.0.0/64,10.0.0.253'
        form_data = form_data_subnet(subnet,
                                     host_routes=host_routes,
                                     allocation_pools=[])
        url = reverse('horizon:project:networks:editsubnet',
                      args=[subnet.network_id, subnet.id])
        res = self.client.post(url, form_data)

        self.assertContains(res,
                            'host_routes: Invalid IP address '
                            '(value=%s)' % host_routes.split(',')[0])

    @test.create_stubs({api.neutron: ('subnet_update',
                                      'subnet_get',)})
    def test_subnet_update_post_invalid_routes_nexthop_ip_network(self):
        subnet = self.subnets.first()
        api.neutron.subnet_get(IsA(http.HttpRequest), subnet.id)\
            .AndReturn(subnet)
        self.mox.ReplayAll()

        # nexthop is not an IP address
        host_routes = '172.16.0.0/24,10.0.0.253/24'
        form_data = form_data_subnet(subnet,
                                     host_routes=host_routes,
                                     allocation_pools=[])
        url = reverse('horizon:project:networks:editsubnet',
                      args=[subnet.network_id, subnet.id])
        res = self.client.post(url, form_data)

        self.assertContains(res,
                            'host_routes: Invalid IP address '
                            '(value=%s)' % host_routes.split(',')[1])

    @test.create_stubs({api.neutron: ('subnet_delete',
                                      'subnet_list',
                                      'network_get',
                                      'port_list',
                                      'is_extension_supported',)})
    def test_subnet_delete(self):
        self._test_subnet_delete()

    @test.create_stubs({api.neutron: ('subnet_delete',
                                      'subnet_list',
                                      'network_get',
                                      'port_list',
                                      'is_extension_supported',)})
    def test_subnet_delete_with_mac_learning(self):
        self._test_subnet_delete(mac_learning=True)

    def _test_subnet_delete(self, mac_learning=False):
        subnet = self.subnets.first()
        network_id = subnet.network_id
        api.neutron.subnet_delete(IsA(http.HttpRequest), subnet.id)
        api.neutron.subnet_list(IsA(http.HttpRequest), network_id=network_id)\
            .AndReturn([self.subnets.first()])
        api.neutron.network_get(IsA(http.HttpRequest), network_id)\
            .AndReturn(self.networks.first())
        api.neutron.port_list(IsA(http.HttpRequest), network_id=network_id)\
            .AndReturn([self.ports.first()])
        # Called from SubnetTable
        api.neutron.network_get(IsA(http.HttpRequest), network_id)\
            .AndReturn(self.networks.first())
        api.neutron.is_extension_supported(IsA(http.HttpRequest),
                                           'mac-learning')\
            .AndReturn(mac_learning)
        self.mox.ReplayAll()

        form_data = {'action': 'subnets__delete__%s' % subnet.id}
        url = reverse('horizon:project:networks:detail',
                      args=[network_id])
        res = self.client.post(url, form_data)

        self.assertRedirectsNoFollow(res, url)

    @test.create_stubs({api.neutron: ('subnet_delete',
                                      'subnet_list',
                                      'network_get',
                                      'port_list',
                                      'is_extension_supported',)})
    def test_subnet_delete_exception(self):
        self._test_subnet_delete_exception()

    @test.create_stubs({api.neutron: ('subnet_delete',
                                      'subnet_list',
                                      'network_get',
                                      'port_list',
                                      'is_extension_supported',)})
    def test_subnet_delete_exception_with_mac_learning(self):
        self._test_subnet_delete_exception(mac_learning=True)

    def _test_subnet_delete_exception(self, mac_learning=False):
        subnet = self.subnets.first()
        network_id = subnet.network_id
        api.neutron.subnet_delete(IsA(http.HttpRequest), subnet.id)\
            .AndRaise(self.exceptions.neutron)
        api.neutron.subnet_list(IsA(http.HttpRequest), network_id=network_id)\
            .AndReturn([self.subnets.first()])
        api.neutron.network_get(IsA(http.HttpRequest), network_id)\
            .AndReturn(self.networks.first())
        api.neutron.port_list(IsA(http.HttpRequest), network_id=network_id)\
            .AndReturn([self.ports.first()])
        # Called from SubnetTable
        api.neutron.network_get(IsA(http.HttpRequest), network_id)\
            .AndReturn(self.networks.first())
        api.neutron.is_extension_supported(IsA(http.HttpRequest),
                                           'mac-learning')\
            .AndReturn(mac_learning)
        self.mox.ReplayAll()

        form_data = {'action': 'subnets__delete__%s' % subnet.id}
        url = reverse('horizon:project:networks:detail',
                      args=[network_id])
        res = self.client.post(url, form_data)

        self.assertRedirectsNoFollow(res, url)


class NetworkPortTests(test.TestCase):

    @test.create_stubs({api.neutron: ('port_get',
                                      'is_extension_supported',)})
    def test_port_detail(self):
        self._test_port_detail()

    @test.create_stubs({api.neutron: ('port_get',
                                      'is_extension_supported',)})
    def test_port_detail_with_mac_learning(self):
        self._test_port_detail(mac_learning=True)

    def _test_port_detail(self, mac_learning=False):
        port = self.ports.first()
        api.neutron.port_get(IsA(http.HttpRequest), port.id)\
            .AndReturn(self.ports.first())
        api.neutron.is_extension_supported(IsA(http.HttpRequest),
                                           'mac-learning')\
            .AndReturn(mac_learning)
        api.neutron.is_extension_supported(IsA(http.HttpRequest),
                                           'mac-learning')\
            .AndReturn(mac_learning)
        self.mox.ReplayAll()

        res = self.client.get(reverse('horizon:project:networks:ports:detail',
                                      args=[port.id]))

        self.assertTemplateUsed(res, 'project/networks/ports/detail.html')
        self.assertEqual(res.context['port'].id, port.id)

    @test.create_stubs({api.neutron: ('port_get',)})
    def test_port_detail_exception(self):
        port = self.ports.first()
        api.neutron.port_get(IsA(http.HttpRequest), port.id)\
            .AndRaise(self.exceptions.neutron)

        self.mox.ReplayAll()

        res = self.client.get(reverse('horizon:project:networks:ports:detail',
                                      args=[port.id]))

        self.assertRedirectsNoFollow(res, INDEX_URL)

    @test.create_stubs({api.neutron: ('port_get',
                                      'is_extension_supported',)})
    def test_port_update_get(self):
        self._test_port_update_get()

    @test.create_stubs({api.neutron: ('port_get',
                                      'is_extension_supported',)})
    def test_port_update_get_with_mac_learning(self):
        self._test_port_update_get(mac_learning=True)

    def _test_port_update_get(self, mac_learning=False, binding=False):
        port = self.ports.first()
        api.neutron.port_get(IsA(http.HttpRequest),
                             port.id)\
            .AndReturn(port)
        api.neutron.is_extension_supported(IsA(http.HttpRequest),
                                           'binding')\
            .AndReturn(binding)
        api.neutron.is_extension_supported(IsA(http.HttpRequest),
                                           'mac-learning')\
            .AndReturn(mac_learning)
        self.mox.ReplayAll()

        url = reverse('horizon:project:networks:editport',
                      args=[port.network_id, port.id])
        res = self.client.get(url)

        self.assertTemplateUsed(res, 'project/networks/ports/update.html')

    @test.create_stubs({api.neutron: ('port_get',
                                      'is_extension_supported',
                                      'port_update')})
    def test_port_update_post(self):
        self._test_port_update_post()

    @test.create_stubs({api.neutron: ('port_get',
                                      'is_extension_supported',
                                      'port_update')})
    def test_port_update_post_with_mac_learning(self):
        self._test_port_update_post(mac_learning=True)

    def _test_port_update_post(self, mac_learning=False, binding=False):
        port = self.ports.first()
        api.neutron.port_get(IsA(http.HttpRequest), port.id)\
            .AndReturn(port)
        api.neutron.is_extension_supported(IsA(http.HttpRequest),
                                           'binding')\
            .AndReturn(binding)
        api.neutron.is_extension_supported(IsA(http.HttpRequest),
                                           'mac-learning')\
            .AndReturn(mac_learning)
        extension_kwargs = {}
        if binding:
            extension_kwargs['binding__vnic_type'] = port.binding__vnic_type
        if mac_learning:
            extension_kwargs['mac_learning_enabled'] = True
        api.neutron.port_update(IsA(http.HttpRequest), port.id,
                                name=port.name,
                                admin_state_up=port.admin_state_up,
                                **extension_kwargs)\
            .AndReturn(port)
        self.mox.ReplayAll()

        form_data = {'network_id': port.network_id,
                     'port_id': port.id,
                     'name': port.name,
                     'admin_state': port.admin_state_up}
        if binding:
            form_data['binding__vnic_type'] = port.binding__vnic_type
        if mac_learning:
            form_data['mac_state'] = True
        url = reverse('horizon:project:networks:editport',
                      args=[port.network_id, port.id])
        res = self.client.post(url, form_data)

        redir_url = reverse('horizon:project:networks:detail',
                            args=[port.network_id])
        self.assertRedirectsNoFollow(res, redir_url)

    @test.create_stubs({api.neutron: ('port_get',
                                      'is_extension_supported',
                                      'port_update')})
    def test_port_update_post_exception(self):
        self._test_port_update_post_exception()

    @test.create_stubs({api.neutron: ('port_get',
                                      'is_extension_supported',
                                      'port_update')})
    def test_port_update_post_exception_with_mac_learning(self):
        self._test_port_update_post_exception(mac_learning=True)

    def _test_port_update_post_exception(self, mac_learning=False,
                                         binding=False):

        port = self.ports.first()
        api.neutron.port_get(IsA(http.HttpRequest), port.id)\
            .AndReturn(port)
        api.neutron.is_extension_supported(IsA(http.HttpRequest),
                                           'binding')\
            .AndReturn(binding)
        api.neutron.is_extension_supported(IsA(http.HttpRequest),
                                           'mac-learning')\
            .AndReturn(mac_learning)
        extension_kwargs = {}
        if binding:
            extension_kwargs['binding__vnic_type'] = port.binding__vnic_type
        if mac_learning:
            extension_kwargs['mac_learning_enabled'] = True
        api.neutron.port_update(IsA(http.HttpRequest), port.id,
                                name=port.name,
                                admin_state_up=port.admin_state_up,
                                **extension_kwargs)\
            .AndRaise(self.exceptions.neutron)
        self.mox.ReplayAll()

        form_data = {'network_id': port.network_id,
                     'port_id': port.id,
                     'name': port.name,
                     'admin_state': port.admin_state_up}
        if binding:
            form_data['binding__vnic_type'] = port.binding__vnic_type
        if mac_learning:
            form_data['mac_state'] = True
        url = reverse('horizon:project:networks:editport',
                      args=[port.network_id, port.id])
        res = self.client.post(url, form_data)

        redir_url = reverse('horizon:project:networks:detail',
                            args=[port.network_id])
        self.assertRedirectsNoFollow(res, redir_url)


class NetworkViewTests(test.TestCase):

    def _test_create_button_shown_when_quota_disabled(
            self, expected_string):
        # if quota_data doesnt contain a networks|subnets|routers key or
        # these keys are empty dicts, its disabled
        quota_data = self.neutron_quota_usages.first()

        quota_data['networks'].pop('available')
        quota_data['subnets'].pop('available')

        api.neutron.network_list(
            IsA(http.HttpRequest),
            tenant_id=self.tenant.id,
            shared=False).AndReturn(self.networks.list())
        api.neutron.network_list(
            IsA(http.HttpRequest),
            shared=True).AndReturn([])
        quotas.tenant_quota_usages(
            IsA(http.HttpRequest)) \
            .MultipleTimes().AndReturn(quota_data)

        self.mox.ReplayAll()

        res = self.client.get(INDEX_URL)
        self.assertTemplateUsed(res, 'project/networks/index.html')

        networks = res.context['networks_table'].data
        self.assertItemsEqual(networks, self.networks.list())
        self.assertContains(res, expected_string, True, html=True,
                            msg_prefix="The enabled create button not shown")

    def _test_create_button_disabled_when_quota_exceeded(
            self, expected_string, network_quota=5, subnet_quota=5):

        quota_data = self.neutron_quota_usages.first()

        quota_data['networks']['available'] = network_quota
        quota_data['subnets']['available'] = subnet_quota

        api.neutron.network_list(
            IsA(http.HttpRequest),
            tenant_id=self.tenant.id,
            shared=False).AndReturn(self.networks.list())
        api.neutron.network_list(
            IsA(http.HttpRequest),
            shared=True).AndReturn([])
        quotas.tenant_quota_usages(
            IsA(http.HttpRequest)) \
            .MultipleTimes().AndReturn(quota_data)

        self.mox.ReplayAll()

        res = self.client.get(INDEX_URL)
        self.assertTemplateUsed(res, 'project/networks/index.html')

        networks = res.context['networks_table'].data
        self.assertItemsEqual(networks, self.networks.list())
        self.assertContains(res, expected_string, True, html=True,
                            msg_prefix="The create button is not disabled")

    @test.create_stubs({api.neutron: ('network_list',),
                        quotas: ('tenant_quota_usages',)})
    def test_network_create_button_disabled_when_quota_exceeded_index(self):
        create_link = networks_tables.CreateNetwork()
        url = create_link.get_link_url()
        classes = (list(create_link.get_default_classes())
                   + list(create_link.classes))
        link_name = "%s (%s)" % (unicode(create_link.verbose_name),
                                 "Quota exceeded")
        expected_string = "<a href='%s' title='%s'  class='%s disabled' "\
            "id='networks__action_create'>" \
            "<span class='fa fa-plus'></span>%s</a>" \
            % (url, link_name, " ".join(classes), link_name)
        self._test_create_button_disabled_when_quota_exceeded(expected_string,
                                                              network_quota=0
                                                              )

    @test.create_stubs({api.neutron: ('network_list',),
                        quotas: ('tenant_quota_usages',)})
    def test_subnet_create_button_disabled_when_quota_exceeded_index(self):
        network_id = self.networks.first().id
        create_link = networks_tables.CreateSubnet()
        url = reverse(create_link.get_link_url(), args=[network_id])
        classes = (list(create_link.get_default_classes())
                   + list(create_link.classes))
        link_name = "%s (%s)" % (unicode(create_link.verbose_name),
                                 "Quota exceeded")
        expected_string = "<a href='%s' class='%s disabled' " \
                          "id='networks__row_%s__action_subnet'>%s</a>" \
                          % (url, " ".join(classes), network_id, link_name)
        self._test_create_button_disabled_when_quota_exceeded(expected_string,
                                                              subnet_quota=0
                                                              )

    @test.create_stubs({api.neutron: ('network_list',),
                        quotas: ('tenant_quota_usages',)})
    def test_network_create_button_shown_when_quota_disabled_index(self):
        # if quota_data doesnt contain a networks["available"] key its disabled
        create_link = networks_tables.CreateNetwork()
        url = create_link.get_link_url()
        classes = (list(create_link.get_default_classes())
                   + list(create_link.classes))
        link_name = "%s" % (unicode(create_link.verbose_name),)
        expected_string = "<a href='%s' title='%s'  class='%s' "\
            "id='networks__action_create'>" \
            "<span class='fa fa-plus'></span>%s</a>" \
            % (url, link_name, " ".join(classes), link_name)
        self._test_create_button_shown_when_quota_disabled(expected_string)

    @test.create_stubs({api.neutron: ('network_list',),
                        quotas: ('tenant_quota_usages',)})
    def test_subnet_create_button_shown_when_quota_disabled_index(self):
        # if quota_data doesnt contain a subnets["available"] key, its disabled
        network_id = self.networks.first().id
        create_link = networks_tables.CreateSubnet()
        url = reverse(create_link.get_link_url(), args=[network_id])
        classes = (list(create_link.get_default_classes())
                   + list(create_link.classes))
        link_name = "%s" % (unicode(create_link.verbose_name),)
        expected_string = "<a href='%s' class='%s' "\
            "id='networks__row_%s__action_subnet'>%s</a>" \
            % (url, " ".join(classes), network_id, link_name)
        self._test_create_button_shown_when_quota_disabled(expected_string)

    @test.create_stubs({api.neutron: ('network_get',
                                      'subnet_list',
                                      'port_list',
                                      'is_extension_supported',),
                        quotas: ('tenant_quota_usages',)})
    def test_subnet_create_button_disabled_when_quota_exceeded_detail(self):
        network_id = self.networks.first().id
        quota_data = self.neutron_quota_usages.first()
        quota_data['subnets']['available'] = 0

        api.neutron.network_get(
            IsA(http.HttpRequest), network_id)\
            .MultipleTimes().AndReturn(self.networks.first())
        api.neutron.subnet_list(
            IsA(http.HttpRequest), network_id=network_id)\
            .AndReturn(self.subnets.list())
        api.neutron.port_list(
            IsA(http.HttpRequest), network_id=network_id)\
            .AndReturn([self.ports.first()])
        api.neutron.is_extension_supported(
            IsA(http.HttpRequest), 'mac-learning')\
            .AndReturn(False)
        quotas.tenant_quota_usages(
            IsA(http.HttpRequest)) \
            .MultipleTimes().AndReturn(quota_data)

        self.mox.ReplayAll()

        res = self.client.get(reverse('horizon:project:networks:detail',
                                      args=[network_id]))
        self.assertTemplateUsed(res, 'project/networks/detail.html')

        subnets = res.context['subnets_table'].data
        self.assertItemsEqual(subnets, self.subnets.list())

        class FakeTable(object):
            kwargs = {'network_id': network_id}
        create_link = subnets_tables.CreateSubnet()
        create_link.table = FakeTable()
        url = create_link.get_link_url()
        classes = (list(create_link.get_default_classes())
                   + list(create_link.classes))
        link_name = "%s (%s)" % (unicode(create_link.verbose_name),
                                 "Quota exceeded")
        expected_string = "<a href='%s' title='%s'  class='%s disabled' "\
            "id='subnets__action_create'>" \
            "<span class='fa fa-plus'></span>%s</a>" \
            % (url, link_name, " ".join(classes), link_name)
        self.assertContains(res, expected_string, html=True,
                            msg_prefix="The create button is not disabled")
