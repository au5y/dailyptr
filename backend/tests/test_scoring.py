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


def _make_day(d, user_id, fully_completed=True, points=10.0):
    day = models.Day(
        user_id=user_id,
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


def test_compute_stats_current_streak(db_session, test_user):
    today = date.today()
    # 3-day streak ending today, plus a gap, plus one older completed day
    for offset in [0, 1, 2, 5]:
        db_session.add(_make_day(today - timedelta(days=offset), test_user.id))
    db_session.commit()

    stats = scoring.compute_stats(db_session, test_user)
    assert stats["current_streak"] == 3
    assert stats["days_completed"] == 4
    assert stats["longest_streak"] == 3


def test_compute_stats_missed_open_days(db_session, test_user):
    today = date.today()
    db_session.add(_make_day(today - timedelta(days=1), test_user.id, fully_completed=False, points=0.0))
    db_session.commit()

    # A start_date on/before the missed day is required for it to count -
    # otherwise it predates the user's own start and is a "bonus" day instead.
    stats = scoring.compute_stats(db_session, test_user, start_date=today - timedelta(days=5))
    assert stats["days_missed_open"] == 1
    assert stats["current_streak"] == 0


def test_compute_stats_excludes_days_before_start_date(db_session, test_user):
    today = date.today()
    db_session.add(_make_day(today - timedelta(days=1), test_user.id, fully_completed=False, points=0.0))
    db_session.commit()

    # Same incomplete day as above, but now it's before start_date - a bonus
    # day, not a missed one, so it shouldn't count.
    stats = scoring.compute_stats(db_session, test_user, start_date=today)
    assert stats["days_missed_open"] == 0
