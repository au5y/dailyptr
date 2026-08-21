"""add per-user daily quota counters for AI concept-check grading

Revision ID: f4e9b7c1d2a3
Revises: a1b2c3d4e5f6
Create Date: 2026-08-20 07:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f4e9b7c1d2a3'
down_revision: Union[str, None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('users') as batch_op:
        batch_op.add_column(sa.Column('ai_grade_count', sa.Integer(), nullable=False, server_default='0'))
        batch_op.add_column(sa.Column('ai_grade_count_date', sa.Date(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table('users') as batch_op:
        batch_op.drop_column('ai_grade_count_date')
        batch_op.drop_column('ai_grade_count')
