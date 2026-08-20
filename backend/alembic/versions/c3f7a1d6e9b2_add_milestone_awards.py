"""add milestone_awards (streak badges)

Revision ID: c3f7a1d6e9b2
Revises: 8f1c2a4b9d3e
Create Date: 2026-08-20 05:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c3f7a1d6e9b2'
down_revision: Union[str, None] = '8f1c2a4b9d3e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('milestone_awards',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('track', sa.String(length=32), nullable=False),
        sa.Column('milestone', sa.Integer(), nullable=False),
        sa.Column('points_awarded', sa.Float(), nullable=False),
        sa.Column('awarded_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'track', 'milestone', name='uq_milestone_awards_user_track_milestone'),
    )
    op.create_index(op.f('ix_milestone_awards_user_id'), 'milestone_awards', ['user_id'], unique=False)
    op.create_index(op.f('ix_milestone_awards_track'), 'milestone_awards', ['track'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_milestone_awards_track'), table_name='milestone_awards')
    op.drop_index(op.f('ix_milestone_awards_user_id'), table_name='milestone_awards')
    op.drop_table('milestone_awards')
