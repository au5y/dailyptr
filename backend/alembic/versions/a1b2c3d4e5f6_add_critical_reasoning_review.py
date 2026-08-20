"""add critical reasoning review (system_design's new required review step)

Revision ID: a1b2c3d4e5f6
Revises: c3f7a1d6e9b2
Create Date: 2026-08-20 06:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = 'c3f7a1d6e9b2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('critical_reasoning_challenges',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('track', sa.String(length=32), nullable=False),
        sa.Column('difficulty', sa.String(length=16), nullable=False),
        sa.Column('topic', sa.String(length=64), nullable=False),
        sa.Column('title', sa.String(length=128), nullable=False),
        sa.Column('passage', sa.Text(), nullable=False),
        sa.Column('issues', sa.JSON(), nullable=False),
        sa.Column('distractor_reasons', sa.JSON(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_critical_reasoning_challenges_difficulty'), 'critical_reasoning_challenges', ['difficulty'], unique=False)
    op.create_index(op.f('ix_critical_reasoning_challenges_track'), 'critical_reasoning_challenges', ['track'], unique=False)

    # batch_alter_table so this also works on SQLite (used by tests/local dev
    # without DATABASE_URL set) - see 8f1c2a4b9d3e for the same rationale.
    with op.batch_alter_table('days') as batch_op:
        batch_op.add_column(sa.Column('critical_reasoning_challenge_id', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('critical_reasoning_completed', sa.Boolean(), nullable=False, server_default=sa.false()))
        batch_op.add_column(sa.Column('critical_reasoning_correct', sa.Integer(), nullable=False, server_default='0'))
        batch_op.add_column(sa.Column('critical_reasoning_total', sa.Integer(), nullable=False, server_default='0'))
        batch_op.create_foreign_key(
            'days_critical_reasoning_challenge_id_fkey', 'critical_reasoning_challenges',
            ['critical_reasoning_challenge_id'], ['id'],
        )
        # system_design days will never populate code_review_challenge_id
        # going forward (its review_kind switches to "reasoning" - see
        # config.TRACKS), so this column can no longer be NOT NULL for every
        # track's rows.
        batch_op.alter_column('code_review_challenge_id', nullable=True)

    # system_design's existing Day rows point at a code_review_challenge_id
    # from the now-deleted system_design entries in code_review_bank.py, and
    # this app has no real deployed user data yet (pre-launch, self-hosted -
    # same situation 8f1c2a4b9d3e was in) - wipe and let get_or_create_day /
    # backfill_history regenerate them deterministically with a critical
    # reasoning challenge instead, the next time they're opened.
    op.execute("DELETE FROM days WHERE track = 'system_design'")


def downgrade() -> None:
    raise NotImplementedError("no downgrade path - same policy as 8f1c2a4b9d3e")
