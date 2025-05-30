"""empty message

Revision ID: 4777f1d3eb42
Revises: 0e5cd3f7a16f
Create Date: 2023-06-10 10:31:00.784247

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4777f1d3eb42'
down_revision = '0e5cd3f7a16f'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('chnge_approver_group_relationship', sa.Column('record_id', sa.Integer(), nullable=True))
    op.drop_constraint('chnge_approver_group_relationship_group_id_fkey', 'chnge_approver_group_relationship', type_='foreignkey')
    op.create_foreign_key(None, 'chnge_approver_group_relationship', 'chng_approver_group', ['record_id'], ['id'])
    op.drop_column('chnge_approver_group_relationship', 'group_id')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('chnge_approver_group_relationship', sa.Column('group_id', sa.INTEGER(), autoincrement=False, nullable=True))
    op.drop_constraint(None, 'chnge_approver_group_relationship', type_='foreignkey')
    op.create_foreign_key('chnge_approver_group_relationship_group_id_fkey', 'chnge_approver_group_relationship', 'chng_approver_group', ['group_id'], ['id'])
    op.drop_column('chnge_approver_group_relationship', 'record_id')
    # ### end Alembic commands ###
