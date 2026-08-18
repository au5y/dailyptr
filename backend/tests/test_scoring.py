from datetime import date, timedelta

import pytest

from app import models, scoring


@pytest.fixture(autouse=True)
def clean_days(db_session):
    """These tests need full control over the Day table to compute streaks
    deterministically, independent of whatever test_api.py has inserted
    (which shares the same DB file within a test run). Reset around each test."""
    db_session.query(models.Day).delete()
    db_session.commit()
    yield
    db_session.query(models.Day).delete()
    db_session.commit()


def _make_day(d, fully_completed=True, points=10.0):
    day = models.Day(
        date=d,
        weekday=d.weekday(),
        difficulty="easy",
        quiz_question_ids=[1, 2, 3],
        coding_problem_id=1,
        concept_check_id=1,
        quiz_completed=fully_completed,
        coding_completed=fully_completed,
        concept_completed=fully_completed,
        points_earned=points,
    )
    return day


def test_points_scale_with_difficulty():
    easy = scoring.points_for_coding("easy")
    hard = scoring.points_for_coding("hard")
    expert = scoring.points_for_coding("expert")
    assert easy < hard < expert


def test_compute_stats_current_streak(db_session):
    today = date.today()
    # 3-day streak ending today, plus a gap, plus one older completed day
    for offset in [0, 1, 2, 5]:
        db_session.add(_make_day(today - timedelta(days=offset)))
    db_session.commit()

    stats = scoring.compute_stats(db_session)
    assert stats["current_streak"] == 3
    assert stats["days_completed"] == 4
    assert stats["longest_streak"] == 3


def test_compute_stats_missed_open_days(db_session):
    today = date.today()
    db_session.add(_make_day(today - timedelta(days=1), fully_completed=False, points=0.0))
    db_session.commit()

    stats = scoring.compute_stats(db_session)
    assert stats["days_missed_open"] == 1
    assert stats["current_streak"] == 0
