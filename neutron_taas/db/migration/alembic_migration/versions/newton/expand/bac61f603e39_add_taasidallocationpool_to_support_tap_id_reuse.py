"""add TaasIdAllocationPool to support tap id reuse

Revision ID: bac61f603e39
Revises: 04625466c6fa
Create Date: 2016-07-27 09:31:54.200165

"""

# revision identifiers, used by Alembic.
revision = 'bac61f603e39'
down_revision = '04625466c6fa'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_table(
        'taas_id_allocation_pools',
        sa.Column('id', sa.String(length=36), primary_key=True,
                  nullable=False),
        sa.Column('first_taas_id', sa.INTEGER),
        sa.Column('last_taas_id', sa.INTEGER))
