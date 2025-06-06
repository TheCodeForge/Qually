"""empty message

Revision ID: b329656be69a
Revises: eac6ca127845
Create Date: 2023-05-14 17:18:05.782153

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b329656be69a'
down_revision = 'eac6ca127845'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('ncmr', sa.Column('nc_description_raw', sa.String(), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('ncmr', 'nc_description_raw')
    # ### end Alembic commands ###
