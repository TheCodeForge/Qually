"""empty message

Revision ID: eac6ca127845
Revises: 8222ec0acf9f
Create Date: 2023-05-14 16:47:29.242346

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'eac6ca127845'
down_revision = '8222ec0acf9f'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('ncmr', sa.Column('nc_description', sa.String(), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('ncmr', 'nc_description')
    # ### end Alembic commands ###
