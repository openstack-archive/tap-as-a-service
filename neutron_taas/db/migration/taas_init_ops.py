# Copyright 2015 Ericsson AB
# Copyright (c) 2015 Gigamon
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
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

# Initial schema operations for Tap-as-a-Service service plugin


from alembic import op
import sqlalchemy as sa


direction_types = sa.Enum('IN', 'OUT', 'BOTH', name='tapflows_direction')


def upgrade():
    op.create_table(
        'tap_services',
        sa.Column('id', sa.String(length=36), primary_key=True,
                  nullable=False),
        sa.Column('tenant_id', sa.String(length=255), nullable=True),
        sa.Column('name', sa.String(length=255), nullable=True),
        sa.Column('description', sa.String(length=1024), nullable=True),
        sa.Column('port_id', sa.String(36), nullable=False),
        sa.Column('network_id', sa.String(36), nullable=True))

    op.create_table(
        'tap_flows',
        sa.Column('id', sa.String(length=36), primary_key=True,
                  nullable=False),
        sa.Column('tenant_id', sa.String(length=255), nullable=True),
        sa.Column('name', sa.String(length=255), nullable=True),
        sa.Column('description', sa.String(length=1024), nullable=True),
        sa.Column('tap_service_id', sa.String(length=36),
                  sa.ForeignKey("tap_services.id",
                                ondelete="CASCADE"), nullable=False),
        sa.Column('source_port', sa.String(length=36), nullable=False),
        sa.Column('direction', direction_types, nullable=False))

    op.create_table(
        'tap_id_associations',
        sa.Column('tap_service_id', sa.String(length=36)),
        sa.Column('taas_id', sa.INTEGER, primary_key=True, autoincrement=True))
