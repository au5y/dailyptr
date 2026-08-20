"""add quiz_answers to days

Revision ID: d878af90e263
Revises: 04bf9e46aa79
Create Date: 2026-08-19 23:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd878af90e263'
down_revision: Union[str, None] = '04bf9e46aa79'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('days', sa.Column('quiz_answers', sa.JSON(), nullable=False, server_default='{}'))


def downgrade() -> None:
    op.drop_column('days', 'quiz_answers')
