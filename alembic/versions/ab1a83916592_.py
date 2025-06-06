"""empty message

Revision ID: ab1a83916592
Revises: 4754c786b5d5
Create Date: 2023-05-31 20:24:35.084690

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ab1a83916592'
down_revision = '4754c786b5d5'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('item', sa.Column('number', sa.Integer(), nullable=True))
    op.create_unique_constraint('item_org_number_unique', 'item', ['_kind_id', 'number', 'organization_id'])
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint('item_org_number_unique', 'item', type_='unique')
    op.drop_column('item', 'number')
    # ### end Alembic commands ###
