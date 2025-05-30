"""empty message

Revision ID: 0e5cd3f7a16f
Revises: a4a21c06adef
Create Date: 2023-06-10 07:19:43.732713

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0e5cd3f7a16f'
down_revision = 'a4a21c06adef'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('chng_approver_group',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('organization_id', sa.Integer(), nullable=True),
    sa.Column('name', sa.String(length=128), nullable=False),
    sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('chnge_approver_group_relationship',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('group_id', sa.Integer(), nullable=True),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['group_id'], ['chng_approver_group.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.add_column('chng', sa.Column('implementation_plan', sa.String(), nullable=True))
    op.add_column('chng', sa.Column('implementation_plan_raw', sa.String(), nullable=True))
    op.add_column('chng', sa.Column('training_impacts', sa.String(), nullable=True))
    op.add_column('chng', sa.Column('training_impacts_raw', sa.String(), nullable=True))
    op.add_column('chng', sa.Column('phase_98_due_utc', sa.BigInteger(), nullable=True))
    op.add_column('chng', sa.Column('implementation_tasks_done', sa.String(), nullable=True))
    op.add_column('chng', sa.Column('implementation_tasks_done_raw', sa.String(), nullable=True))
    op.drop_column('chng', 'phase_96_due_utc')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('chng', sa.Column('phase_96_due_utc', sa.BIGINT(), autoincrement=False, nullable=True))
    op.drop_column('chng', 'implementation_tasks_done_raw')
    op.drop_column('chng', 'implementation_tasks_done')
    op.drop_column('chng', 'phase_98_due_utc')
    op.drop_column('chng', 'training_impacts_raw')
    op.drop_column('chng', 'training_impacts')
    op.drop_column('chng', 'implementation_plan_raw')
    op.drop_column('chng', 'implementation_plan')
    op.drop_table('chnge_approver_group_relationship')
    op.drop_table('chng_approver_group')
    # ### end Alembic commands ###
