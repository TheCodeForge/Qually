"""empty message

Revision ID: a91e36d337b9
Revises: e1fb906f0441
Create Date: 2023-04-29 11:14:02.482475

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a91e36d337b9'
down_revision = 'e1fb906f0441'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('users', sa.Column('is_org_admin', sa.Boolean(), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('users', 'is_org_admin')
    # ### end Alembic commands ###
