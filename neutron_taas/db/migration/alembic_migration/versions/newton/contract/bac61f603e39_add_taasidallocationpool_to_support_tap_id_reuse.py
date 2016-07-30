# Copyright 2016
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

"""add TaasIdAllocationPool to support tap id reuse

Revision ID: bac61f603e39
Revises: 04625466c6fa
Create Date: 2016-07-27 09:31:54.200165

"""

# revision identifiers, used by Alembic.
revision = 'bac61f603e39'
down_revision = 'fddbdec8711a'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_table(
        'taas_id_allocation_pools',
        sa.Column('first_taas_id', sa.INTEGER, primary_key=True),
        sa.Column('last_taas_id', sa.INTEGER, primary_key=True))
    op.alter_column('tap_id_associations', 'taas_id', autoincrement=False,
                    existing_type=sa.INTEGER, nullable=False)
