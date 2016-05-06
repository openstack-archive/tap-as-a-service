# Copyright 2016 VMware, Inc.
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

"""initial Newton no op expand script

Revision ID: 04625466c6fa
Revises: start_neutron_taas
Create Date: 2016-05-06 05:17:30.172181

"""

from neutron.db.migration import cli

# revision identifiers, used by Alembic.
revision = '04625466c6fa'
down_revision = 'start_neutron_taas'
branch_labels = (cli.EXPAND_BRANCH,)


def upgrade():
    pass
