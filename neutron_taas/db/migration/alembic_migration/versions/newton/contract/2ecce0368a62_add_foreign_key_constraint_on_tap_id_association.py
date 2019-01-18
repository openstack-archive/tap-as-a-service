# Copyright 2016 Midokura SARL
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

"""add foreign key constraint on tap id association

Revision ID: 2ecce0368a62
Revises: 1817af933379
Create Date: 2016-05-19 11:39:52.892610

"""

# revision identifiers, used by Alembic.
revision = '2ecce0368a62'
down_revision = '1817af933379'

from alembic import op


def upgrade():
    op.create_foreign_key(
        constraint_name=None,
        source_table='tap_id_associations',
        referent_table='tap_services',
        local_cols=['tap_service_id'],
        remote_cols=['id'],
        ondelete='CASCADE')
