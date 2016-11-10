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

from neutron_taas_dashboard.dashboards.project.network_topology import views \
    as nt_views

from openstack_dashboard.dashboards.project.network_topology import urls \
    as i_url

i_url.urlpatterns = [
    url(r'^createtapservice$', nt_views.NTCreateTapServiceView.as_view(),
        name='createtapservice'),
    url(r'^deletetapservice$', nt_views.TapServiceView.as_view(),
        name='deletetapservice'),
    url(r'^tapservice/(?P<tap_service_id>[^/]+)/$',
        nt_views.TapFlowView.as_view(),
        name='tapservicedetail'),
] + i_url.urlpatterns
