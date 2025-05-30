"""empty message

Revision ID: d82f4e11c063
Revises: 07004720c8a1
Create Date: 2023-05-24 19:11:59.202888

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd82f4e11c063'
down_revision = '07004720c8a1'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('dvtn', sa.Column('approve_to', sa.Integer(), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('dvtn', 'approve_to')
    # ### end Alembic commands ###
