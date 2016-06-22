# Copyright 2016 FUJITSU LABORATORIES LTD.
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

"""add status

Revision ID: fddbdec8711a
Revises: 04625466c6fa
Create Date: 2016-06-06 10:54:42.252898

"""

# revision identifiers, used by Alembic.
revision = 'fddbdec8711a'
down_revision = '04625466c6fa'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('tap_services', sa.Column('status', sa.String(16),
                                            server_default='', nullable=False))
    op.add_column('tap_flows', sa.Column('status', sa.String(16),
                                         server_default='', nullable=False))
