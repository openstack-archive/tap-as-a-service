# Copyright 2016 OpenStack Foundation
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

"""rename tenant to project

Revision ID: 4086b3cffc01
Revises: 2ecce0368a62
Create Date: 2016-07-30 22:09:16.372917

"""

# revision identifiers, used by Alembic.
revision = '4086b3cffc01'
down_revision = '2ecce0368a62'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine import reflection

from neutron.db import migration


_INSPECTOR = None

# milestone identifier, used by neutron-db-manage
neutron_milestone = [migration.NEWTON]


def get_inspector():
    """Reuse inspector."""

    global _INSPECTOR

    if _INSPECTOR:
        return _INSPECTOR

    else:
        bind = op.get_bind()
        _INSPECTOR = reflection.Inspector.from_engine(bind)

    return _INSPECTOR


def get_tables():
    """Returns hardcoded list of tables which have ``tenant_id`` column.

    The list is hard-coded to match the state of the schema when this upgrade
    script is run.
    """

    tables = [
        'tap_services',
        'tap_flows',
    ]

    return tables


def get_columns(table):
    """Returns list of columns for given table."""
    inspector = get_inspector()
    return inspector.get_columns(table)


def get_data():
    """Returns combined list of tuples: [(table, column)].

    The list is built from tables with a tenant_id column.
    """

    output = []
    tables = get_tables()
    for table in tables:
        columns = get_columns(table)

        for column in columns:
            if column['name'] == 'tenant_id':
                output.append((table, column))

    return output


def alter_column(table, column):
    old_name = 'tenant_id'
    new_name = 'project_id'

    op.alter_column(
        table_name=table,
        column_name=old_name,
        new_column_name=new_name,
        existing_type=column['type'],
        existing_nullable=column['nullable']
    )


def upgrade():
    data = get_data()
    for table, column in data:
        alter_column(table, column)


def contract_creation_exceptions():
    """Special migration for the blueprint to support Keystone V3.

    We drop all tenant_id columns and create project_id columns instead.
    """

    return {
        sa.Column: ['.'.join([table, 'project_id']) for table in get_tables()],
        sa.Index: get_tables()
    }
