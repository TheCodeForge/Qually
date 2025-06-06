"""empty message

Revision ID: 254ed84e745a
Revises: 6cc9540b9ec0
Create Date: 2023-05-23 21:21:55.501428

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '254ed84e745a'
down_revision = '6cc9540b9ec0'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('files',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('created_utc', sa.Integer(), nullable=True),
    sa.Column('organization_id', sa.Integer(), nullable=True),
    sa.Column('created_by', sa.Integer(), nullable=True),
    sa.Column('sha_256', sa.String(length=512), nullable=True),
    sa.Column('ncmr_id', sa.Integer(), nullable=True),
    sa.Column('capa_id', sa.Integer(), nullable=True),
    sa.Column('stage_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['capa_id'], ['capa.id'], ),
    sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
    sa.ForeignKeyConstraint(['ncmr_id'], ['ncmr.id'], ),
    sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('files')
    # ### end Alembic commands ###
