# Copyright 2016-17
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Alter TapIdAssociations to support tap id reuse

Revision ID: bac61f603e39
Revises: 4086b3cffc01
Create Date: 2016-07-27 09:31:54.200165

"""

# revision identifiers, used by Alembic.
revision = 'bac61f603e39'
down_revision = '4086b3cffc01'

from alembic import op
from sqlalchemy.engine import reflection

import sqlalchemy as sa

from neutron.db import migration


# milestone identifier, used by neutron-db-manage
neutron_milestone = [migration.PIKE]

TABLE_NAME = 'tap_id_associations'


def upgrade():
    inspector = reflection.Inspector.from_engine(op.get_bind())
    fk_constraints = inspector.get_foreign_keys(TABLE_NAME)
    for fk in fk_constraints:
        op.drop_constraint(fk['name'], TABLE_NAME, type_='foreignkey')

    op.create_foreign_key('fk_tap_id_assoc_tap_service', TABLE_NAME,
                          'tap_services', ['tap_service_id'], ['id'],
                          ondelete='SET NULL')

    op.alter_column(TABLE_NAME, 'taas_id', autoincrement=False,
                    existing_type=sa.INTEGER, nullable=False)
    op.alter_column(TABLE_NAME, 'tap_service_id',
                    existing_type=sa.String(36), nullable=True)
    op.create_unique_constraint('unique_taas_id', TABLE_NAME,
                                ['taas_id'])
