"""empty message

Revision ID: c0666f2044ca
Revises: 141df2e9a22e
Create Date: 2023-05-15 20:39:47.603118

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c0666f2044ca'
down_revision = '141df2e9a22e'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('ncmr_approval',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('ncmr_id', sa.Integer(), nullable=True),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.Column('status_id', sa.Integer(), nullable=True),
    sa.Column('created_utc', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['ncmr_id'], ['ncmr.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('ncmr_approval')
    # ### end Alembic commands ###
