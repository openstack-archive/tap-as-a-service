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
import sqlalchemy as sa


def upgrade():
    op.alter_column('tap_id_associations', 'taas_id', autoincrement=False,
                    existing_type=sa.INTEGER, nullable=False)
    op.alter_column('tap_id_associations', 'tap_service_id',
                    existing_type=sa.String(36), nullable=True)
    op.create_unique_constraint('unique_taas_id', 'tap_id_associations',
                                ['taas_id'])
