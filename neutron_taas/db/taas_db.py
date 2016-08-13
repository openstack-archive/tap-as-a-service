# Copyright (C) 2015 Ericsson AB
# Copyright (c) 2015 Gigamon
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.


from neutron.api.v2 import attributes as attr
from neutron.db import common_db_mixin as base_db
from neutron.db import model_base
from neutron.db import models_v2
from neutron import manager
from neutron_taas.extensions import taas
from oslo_config import cfg
from oslo_log import log as logging
from oslo_utils import uuidutils
import sqlalchemy as sa
from sqlalchemy import orm
from sqlalchemy.orm import exc

LOG = logging.getLogger(__name__)


class TapService(model_base.BASEV2, models_v2.HasId):

    # Represents a V2 TapService Object
    __tablename__ = 'tap_services'
    tenant_id = sa.Column(sa.String(attr.TENANT_ID_MAX_LEN))
    name = sa.Column(sa.String(255), nullable=True)
    description = sa.Column(sa.String(1024), nullable=True)
    port_id = sa.Column(sa.String(36), nullable=False)


class TapFlow(model_base.BASEV2, models_v2.HasId):

    # Represents a V2 TapFlow Object
    __tablename__ = 'tap_flows'
    tenant_id = sa.Column(sa.String(attr.TENANT_ID_MAX_LEN))
    name = sa.Column(sa.String(255), nullable=True)
    description = sa.Column(sa.String(1024), nullable=True)
    tap_service_id = sa.Column(sa.String(36),
                               sa.ForeignKey("tap_services.id",
                                             ondelete="CASCADE"),
                               nullable=False)
    source_port = sa.Column(sa.String(36), nullable=False)
    direction = sa.Column(sa.Enum('IN', 'OUT', 'BOTH',
                                  name='tapflows_direction'),
                          nullable=False)


class TapIdAssociation(model_base.BASEV2):

    # Internal mapping between a TAP Service and
    # id to be used by the Agents
    __tablename__ = 'tap_id_associations'
    tap_service_id = sa.Column(sa.String(36),
                               sa.ForeignKey("tap_services.id",
                                             ondelete='CASCADE'))
    taas_id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
    tap_service = orm.relationship(
        TapService,
        backref=orm.backref("tap_service_id",
                            lazy="joined", cascade="delete"),
        primaryjoin='TapService.id==TapIdAssociation.tap_service_id')


class TaasIdAllocationPool(model_base.BASEV2):

    # Used to record could allocation Taas Id ranges
    # First entry from the range will be allocated
    # If first_taas_id large than last_taas_id will be deleted
    first_taas_id = sa.Column(sa.Integer, primary_key=True)
    last_taas_id = sa.Column(sa.Integer, primary_key=True)


class Taas_db_Mixin(taas.TaasPluginBase, base_db.CommonDbMixin):

    def _core_plugin(self):
        return manager.NeutronManager.get_plugin()

    def _get_tap_service(self, context, id):
        try:
            return self._get_by_id(context, TapService, id)
        except exc.NoResultFound:
            raise taas.TapServiceNotFound(tap_id=id)

    def _get_tap_id_association(self, context, tap_service_id):
        try:
            query = self._model_query(context, TapIdAssociation)
            return query.filter(TapIdAssociation.tap_service_id ==
                                tap_service_id).one()
        except exc.NoResultFound:
            raise taas.TapServiceNotFound(tap_id=tap_service_id)

    def _get_tap_flow(self, context, id):
        try:
            return self._get_by_id(context, TapFlow, id)
        except Exception:
            raise taas.TapFlowNotFound(flow_id=id)

    def _make_tap_service_dict(self, tap_service, fields=None):
        res = {'id': tap_service['id'],
               'tenant_id': tap_service['tenant_id'],
               'name': tap_service['name'],
               'description': tap_service['description'],
               'port_id': tap_service['port_id']}

        return self._fields(res, fields)

    def _make_tap_id_association_dict(self, tap_id_association):
        res = {'tap_service_id': tap_id_association['tap_service_id'],
               'taas_id': tap_id_association['taas_id']}

        return res

    def _make_tap_flow_dict(self, tap_flow, fields=None):
        res = {'id': tap_flow['id'],
               'tenant_id': tap_flow['tenant_id'],
               'tap_service_id': tap_flow['tap_service_id'],
               'name': tap_flow['name'],
               'description': tap_flow['description'],
               'source_port': tap_flow['source_port'],
               'direction': tap_flow['direction']}

        return self._fields(res, fields)

    def create_tap_service(self, context, tap_service):
        LOG.debug("create_tap_service() called")
        t_s = tap_service['tap_service']
        tenant_id = t_s['tenant_id']
        with context.session.begin(subtransactions=True):
            tap_service_db = TapService(
                id=uuidutils.generate_uuid(),
                tenant_id=tenant_id,
                name=t_s['name'],
                description=t_s['description'],
                port_id=t_s['port_id'],
            )
            context.session.add(tap_service_db)

        return self._make_tap_service_dict(tap_service_db)

    def _rebuild_taas_id_allocation_range(self, context):
        query = context.session.query(
            TapIdAssociation).all().with_lockmode('update')

        # Check if other api worker has rebuild the ranges
        query_range = context.session.query(TaasIdAllocationPool).first()
        if query_range:
            return

        allocate_taas_id_list = [_q.taas_id for _q in query]
        allocate_taas_id_list.sort()
        first_taas_id = cfg.CONF.taas.vlan_range_start
        last_taas_id = cfg.CONF.taas.vlan_range_end

        for _id in allocate_taas_id_list:
            if first_taas_id == _id:
                first_taas_id += 1
            else:
                # new taas id range
                context.session.add(TaasIdAllocationPool(
                    first_taas_id=first_taas_id,
                    last_taas_id=(_id - 1)))
                first_taas_id = _id + 1

        if first_taas_id <= last_taas_id:
            context.session.add(TaasIdAllocationPool(
                first_taas_id=first_taas_id,
                last_taas_id=last_taas_id))

    def _allocate_taas_id(self, context):
        query = context.session.query(TaasIdAllocationPool).first()
        if not query:
            self._rebuild_taas_id_allocation_range(context)
            # try again
            query = context.session.query(
                TaasIdAllocationPool).first()

        if query:
            taas_id_range = query[0]
            taas_id = taas_id_range.first_taas_id
            taas_id_range.first_taas_id += 1
            if taas_id_range.first_taas_id > taas_id_range.last_taas_id:
                context.session.delete(taas_id_range)
            return taas_id
        # not found
        raise taas.TapServiceLimitReached()

    def create_tap_id_association(self, context, tap_service_id):
        LOG.debug("create_tap_id_association() called")
        # create the TapIdAssociation object
        with context.session.begin(subtransactions=True):
            # allocate Taas id.
            # if conflict happened, it will raise db.DBDuplicateEntry.
            # this will be retry request again in neutron controller framework.
            # so we just make sure TapIdAssociation and TaasIdAllocationPool
            # db entry is unique
            taas_id = self._allocate_taas_id(context)
            tap_id_association_db = TapIdAssociation(
                tap_service_id=tap_service_id,
                taas_id=taas_id
            )
            context.session.add(tap_id_association_db)

        return self._make_tap_id_association_dict(tap_id_association_db)

    def create_tap_flow(self, context, tap_flow):
        LOG.debug("create_tap_flow() called")
        t_f = tap_flow['tap_flow']
        tenant_id = t_f['tenant_id']
        # TODO(Vinay): Check for the tenant_id validation
        # TODO(Vinay): Check for the source port validation
        with context.session.begin(subtransactions=True):
            tap_flow_db = TapFlow(
                id=uuidutils.generate_uuid(),
                tenant_id=tenant_id,
                name=t_f['name'],
                description=t_f['description'],
                tap_service_id=t_f['tap_service_id'],
                source_port=t_f['source_port'],
                direction=t_f['direction']
            )
            context.session.add(tap_flow_db)

        return self._make_tap_flow_dict(tap_flow_db)

    def delete_tap_service(self, context, id):
        LOG.debug("delete_tap_service() called")

        count = context.session.query(TapService).filter_by(id=id).delete()

        if not count:
            raise taas.TapServiceNotFound(tap_id=id)

    def delete_tap_flow(self, context, id):
        LOG.debug("delete_tap_flow() called")

        count = context.session.query(TapFlow).filter_by(id=id).delete()

        if not count:
            raise taas.TapFlowNotFound(flow_id=id)

    def get_tap_service(self, context, id, fields=None):
        LOG.debug("get_tap_service() called")

        t_s = self._get_tap_service(context, id)
        return self._make_tap_service_dict(t_s, fields)

    def get_tap_id_association(self, context, tap_service_id):
        LOG.debug("get_tap_id_association() called")

        t_a = self._get_tap_id_association(context, tap_service_id)
        return self._make_tap_id_association_dict(t_a)

    def get_tap_flow(self, context, id, fields=None):
        LOG.debug("get_tap_flow() called")

        t_f = self._get_tap_flow(context, id)
        return self._make_tap_flow_dict(t_f, fields)

    def get_tap_services(self, context, filters=None, fields=None,
                         sorts=None, limit=None, marker=None,
                         page_reverse=False):
        LOG.debug("get_tap_services() called")
        return self._get_collection(context, TapService,
                                    self._make_tap_service_dict,
                                    filters=filters, fields=fields)

    def get_tap_flows(self, context, filters=None, fields=None,
                      sorts=None, limit=None, marker=None,
                      page_reverse=False):
        LOG.debug("get_tap_flows() called")
        return self._get_collection(context, TapFlow,
                                    self._make_tap_flow_dict,
                                    filters=filters, fields=fields)

    def _get_port_details(self, context, port_id):
        with context.session.begin(subtransactions=True):
            port = self._core_plugin().get_port(context, port_id)

        return port

    def update_tap_service(self, context, id, tap_service):
        LOG.debug("update_tap_service() called")
        t_s = tap_service['tap_service']
        with context.session.begin(subtransactions=True):
            tap_service_db = self._get_tap_service(context, id)
            tap_service_db.update(t_s)
        return self._make_tap_service_dict(tap_service_db)

    def update_tap_flow(self, context, id, tap_flow):
        LOG.debug("update_tap_flow() called")
        t_f = tap_flow['tap_flow']
        with context.session.begin(subtransactions=True):
            tap_flow_db = self._get_tap_flow(context, id)
            tap_flow_db.update(t_f)
        return self._make_tap_flow_dict(tap_flow_db)
