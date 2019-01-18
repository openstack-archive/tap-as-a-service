# Copyright (c) 2016 Midokura SARL
# All Rights Reserved.
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

"""Remove network-id from tap-service

Revision ID: 1817af933379
Revises: 80c85b675b6e
Create Date: 2016-04-05 21:59:28.829793

"""

# revision identifiers, used by Alembic.
revision = '1817af933379'
down_revision = '80c85b675b6e'

from alembic import op


def upgrade():
    op.drop_column('tap_services', 'network_id')
