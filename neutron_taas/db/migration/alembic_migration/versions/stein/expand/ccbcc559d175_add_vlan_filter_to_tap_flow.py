# Copyright (C) 2018 AT&T
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

"""add_vlan_filter_to_tap_flow

Revision ID: ccbcc559d175
Revises: fddbdec8711a
Create Date: 2018-09-18 19:33:32.119458

"""

# revision identifiers, used by Alembic.
revision = 'ccbcc559d175'
down_revision = 'fddbdec8711a'

from alembic import op
import sqlalchemy as sa

TABLE_NAME = 'tap_flows'


def upgrade():
    op.add_column(TABLE_NAME, sa.Column('vlan_filter', sa.String(1024),
                                        nullable=True))
