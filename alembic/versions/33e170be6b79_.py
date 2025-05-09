"""empty message

Revision ID: 33e170be6b79
Revises: 2680b22e54a4
Create Date: 2023-05-30 20:23:34.093012

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '33e170be6b79'
down_revision = '2680b22e54a4'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('organizations', sa.Column('item_counter', sa.Integer(), nullable=True))
    op.drop_column('organizations', 'wi_counter')
    op.drop_column('organizations', 'sop_counter')
    op.drop_column('organizations', 'part_counter')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('organizations', sa.Column('part_counter', sa.INTEGER(), autoincrement=False, nullable=True))
    op.add_column('organizations', sa.Column('sop_counter', sa.INTEGER(), autoincrement=False, nullable=True))
    op.add_column('organizations', sa.Column('wi_counter', sa.INTEGER(), autoincrement=False, nullable=True))
    op.drop_column('organizations', 'item_counter')
    # ### end Alembic commands ###
