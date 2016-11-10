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

from django.conf.urls import include
from django.conf.urls import patterns
from django.conf.urls import url

from neutron_taas_dashboard.dashboards.project.instances \
    import views as i_views
from neutron_taas_dashboard.dashboards.project.network_topology \
    import views as nt_views
from neutron_taas_dashboard.dashboards.project.tapservices.tapflows \
    import urls as tapflow_urls
from neutron_taas_dashboard.dashboards.project.tapservices.tapflows \
    import views as tf_views
from neutron_taas_dashboard.dashboards.project.tapservices \
    import views

from openstack_dashboard.dashboards.project.instances import urls \
    as i_urls
from openstack_dashboard.dashboards.project.network_topology import urls \
    as nt_urls

import logging

LOG = logging.getLogger(__name__)

TAP_SERVICES = r'^(?P<tap_service_id>[^/]+)/%s$'

urlpatterns = patterns(
    '',
    url(r'^$', views.IndexView.as_view(), name='index'),
    url(r'^create/$', views.CreateView.as_view(), name='create'),
    url(TAP_SERVICES % 'detail', views.DetailView.as_view(), name='detail'),
    url(TAP_SERVICES % 'tapflows/create', tf_views.CreateView.as_view(),
        name='createtapflow'),
    url(r'^tapflows/', include(tapflow_urls, namespace='tapflows')),
)

INSTANCES = r'^(?P<instance_id>[^/]+)/%s$'

i_urls.urlpatterns += \
    patterns(
        'openstack_dashboard.dashboards.project.instances.views',
        url(INSTANCES % 'createtapflow',
            i_views.CreateTapFlowView.as_view(),
            name='createtapflow'),
        url(INSTANCES % 'deletetapflow',
            i_views.DeleteTapFlowView.as_view(),
            name='deletetapflow'),
    )

nt_urls.urlpatterns += [
    url(r'^createtapservice$', nt_views.NTCreateTapServiceView.as_view(),
        name='createtapservice'),
    url(r'^deletetapservice$', nt_views.TapServiceView.as_view(),
        name='deletetapservice'),
    url(r'^tapservices/(?P<tap_service_id>[^/]+)/$',
        nt_views.TapFlowView.as_view(),
        name='tapservicedetail'),
]

LOG.debug("NT_URLPATTERNS")
LOG.debug(nt_urls.urlpatterns)
