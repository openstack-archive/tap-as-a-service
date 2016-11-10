#    Copyright 2016, FUJITSU LABORATORIES LTD.
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


from django.conf.urls import url
from django.http import HttpResponse  # noqa

from neutron_taas_dashboard.api import taas
from neutron_taas_dashboard.dashboards.project.instances import tables
from neutron_taas_dashboard.dashboards.project.instances import views \
    as nt_ins_views
from neutron_taas_dashboard.dashboards.project.network_topology import views \
    as nt_views

from openstack_dashboard.dashboards.project.instances import \
    tables as i_tables
from openstack_dashboard.dashboards.project.instances import urls \
    as nt_ins_urls
from openstack_dashboard.dashboards.project.instances import \
    views as i_views
from openstack_dashboard.dashboards.project.network_topology import urls \
    as nt_urls

import codecs
import json
import logging
import os

LOG = logging.getLogger(__name__)


class MyInstancesTable(i_tables.InstancesTable):
    class Meta(i_tables.InstancesTable.Meta):
        table_actions = i_tables.InstancesTable.Meta.launch_actions + \
            (tables.DeleteInstance, i_tables.InstancesFilterAction)

        row_actions = (tables.CreateVirtualTap, tables.DeleteVirtualTap) + \
            i_tables.InstancesTable.Meta.row_actions

        list_row_actions = list(row_actions)
        tmp = i_tables.DeleteInstance()
        for i, x in enumerate(row_actions):
            if(isinstance(tmp, x)):
                list_row_actions[i] = tables.DeleteInstance
        row_actions = list_row_actions

i_views.IndexView.table_class = MyInstancesTable

nt_urls.urlpatterns = [
    url(r'^$', nt_views.MyNetworkTopologyView.as_view(), name='index'),
    url(r'^json$', nt_views.MyJSONView.as_view(), name='json'),
] + nt_urls.urlpatterns


nt_ins_urls.urlpatterns = [
    url(r'^(?P<instance_id>[^/]+)/$',
        nt_ins_views.DetailView.as_view(), name='detail'),
] + nt_ins_urls.urlpatterns

taas.add_taas_enable()

json_path = 'openstack_dashboard/conf/neutron_policy.json'
if(os.path.exists(json_path)):
    f = codecs.open(json_path, 'r', 'utf8')
    jsonData = json.load(f)
    Policy = False

    if not ('admin_or_user' in jsonData):
        jsonData['admin_or_user'] = "is_admin:True or user_id:%(user_id)s"

    if not ('create_tap_service' in jsonData):
        jsonData['create_tap_service'] = "rule:admin_or_user"
        Policy = True
    if not ('delete_tap_service' in jsonData):
        jsonData['delete_tap_service'] = "rule:admin_or_user"
        Policy = True
    if not ('create_tap_flow' in jsonData):
        jsonData['create_tap_flow'] = "rule:admin_or_user"
        Policy = True
    if not ('delete_tap_flow' in jsonData):
        jsonData['delete_tap_flow'] = "rule:admin_or_user"
        Policy = True

    if(Policy):
        with codecs.open(json_path, 'w', 'utf8') as f:
            json.dump(jsonData, f, sort_keys=True, indent=4)
