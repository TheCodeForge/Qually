"""empty message

Revision ID: c2c984067a84
Revises: 9aa70866fc8a
Create Date: 2023-05-30 19:20:38.481132

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c2c984067a84'
down_revision = '9aa70866fc8a'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('item_audit',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('record_id', sa.Integer(), nullable=True),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.Column('created_utc', sa.Integer(), nullable=True),
    sa.Column('created_ip', sa.String(length=64), nullable=True),
    sa.Column('key', sa.String(), nullable=True),
    sa.Column('value', sa.String(), nullable=True),
    sa.ForeignKeyConstraint(['record_id'], ['item.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.add_column('item', sa.Column('owner_id', sa.Integer(), nullable=True))
    op.create_foreign_key(None, 'item', 'users', ['owner_id'], ['id'])
    op.add_column('itemrevision', sa.Column('phase_0_due_utc', sa.BigInteger(), nullable=True))
    op.add_column('itemrevision', sa.Column('object_name', sa.String(), nullable=True))
    op.add_column('itemrevision', sa.Column('object_description', sa.String(), nullable=True))
    op.add_column('itemrevision', sa.Column('object_description_raw', sa.String(), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('itemrevision', 'object_description_raw')
    op.drop_column('itemrevision', 'object_description')
    op.drop_column('itemrevision', 'object_name')
    op.drop_column('itemrevision', 'phase_0_due_utc')
    op.drop_constraint(None, 'item', type_='foreignkey')
    op.drop_column('item', 'owner_id')
    op.drop_table('item_audit')
    # ### end Alembic commands ###
