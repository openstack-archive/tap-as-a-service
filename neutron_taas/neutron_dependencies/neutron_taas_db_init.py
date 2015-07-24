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


from neutron.db import models_v2
import sqlalchemy as sa
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import sys

BASE = declarative_base()

_ENGINE = None
_MAKER = None

direction_types = sa.Enum('IN', 'OUT', 'BOTH', name='tapflows_direction')


class TapService(BASE, models_v2.HasId, models_v2.HasTenant):
    # Represents a V2 TapService Object

    __tablename__ = 'tap_services'
    name = sa.Column(sa.String(255), nullable=True)
    description = sa.Column(sa.String(1024), nullable=True)
    port_id = sa.Column(sa.String(36), nullable=False)
    network_id = sa.Column(sa.String(36), nullable=True)


class TapFlow(BASE, models_v2.HasId, models_v2.HasTenant):
    # Represents a V2 TapFlow Object

    __tablename__ = 'tap_flows'
    name = sa.Column(sa.String(255), nullable=True)
    description = sa.Column(sa.String(1024), nullable=True)
    tap_service_id = sa.Column(sa.String(36),
                               sa.ForeignKey("tap_services.id",
                                             ondelete="CASCADE"),
                               nullable=False)
    source_port = sa.Column(sa.String(36), nullable=False)
    direction = sa.Column(direction_types, nullable=False)


class TapIdAssociation(BASE):
    # Internal mapping between a TAP Service and id to be used
    # by the Agents

    __tablename__ = 'tap_id_associations'
    tap_service_id = sa.Column(sa.String(36))
    taas_id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)


def configure_db(options):
    # Establish the database, create an engine if needed, and
    # register the models.
    # param options: Mapping of configuration options

    global _ENGINE
    if not _ENGINE:
        _ENGINE = create_engine(options['sql_connection'],
                                echo=False,
                                echo_pool=True,
                                pool_recycle=3600)
        register_models()


def clear_db():
    global _ENGINE
    assert _ENGINE
    for table in reversed(BASE.metadata.sorted_tables):
        _ENGINE.execute(table.delete())


def get_session(autocommit=True, expire_on_commit=False):
    # Helper method to grab session
    global _MAKER, _ENGINE
    if not _MAKER:
        assert _ENGINE
        _MAKER = sessionmaker(bind=_ENGINE,
                              autocommit=autocommit,
                              expire_on_commit=expire_on_commit)
    return _MAKER()


def register_models():
    # Register Models and create properties
    global _ENGINE
    assert _ENGINE
    BASE.metadata.create_all(_ENGINE)


def unregister_mode():
    # Unregister Models, useful clearing out data before testing
    global _ENGINE
    assert _ENGINE
    BASE.metadata.drop_all(_ENGINE)


def main(argv):
    print'Configuring the Neutron TaaS database'
    configure_db({'sql_connection': ('mysql://root:%s@127.0.0.1/neutron' %
                                     argv[0])})
    print'Configured the Neutron TaaS database'
    return


if __name__ == "__main__":
    main(sys.argv[1:])
