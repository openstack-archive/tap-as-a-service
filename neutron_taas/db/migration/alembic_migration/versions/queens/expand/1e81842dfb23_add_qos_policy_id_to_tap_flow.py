# Copyright 2018 FUJITSU LABORATORIES LTD.
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

"""add_qos_policy_id_to_tap_flow

Revision ID: 1e81842dfb23
Revises: fddbdec8711a
Create Date: 2017-12-04 15:26:35.507290

"""

# revision identifiers, used by Alembic.
revision = '1e81842dfb23'
down_revision = 'fddbdec8711a'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('tap_flows', sa.Column('qos_policy_id', sa.String(36),
                                         nullable=True))
