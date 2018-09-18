"""add_vlan_mirror_to_tap_flow

Revision ID: ccbcc559d175
Revises: fddbdec8711a
Create Date: 2018-09-18 19:33:32.119458

"""

# revision identifiers, used by Alembic.
revision = 'ccbcc559d175'
down_revision = 'fddbdec8711a'

from alembic import op
import sqlalchemy as sa


# milestone identifier, used by neutron-db-manage
neutron_milestone = [migration.ROCKY, migration.STEIN]

TABLE_NAME = 'tap_flows'


def upgrade():
    op.add_column(TABLE_NAME, sa.Column('vlan_mirror', sa.String(1024),
                                          nullable=True))
