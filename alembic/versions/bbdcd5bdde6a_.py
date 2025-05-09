"""empty message

Revision ID: bbdcd5bdde6a
Revises: c44ff0b57972
Create Date: 2023-05-13 18:47:58.982158

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'bbdcd5bdde6a'
down_revision = 'c44ff0b57972'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('ncmr', sa.Column('quantity', sa.String(), nullable=True))
    op.drop_column('ncmr', 'qty')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('ncmr', sa.Column('qty', postgresql.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=True))
    op.drop_column('ncmr', 'quantity')
    # ### end Alembic commands ###
