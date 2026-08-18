from datetime import date as date_type, datetime, timedelta

from sqlalchemy.orm import Session

from . import config, models


def multiplier(difficulty: str) -> float:
    return config.DIFFICULTY_POINT_MULTIPLIER[config.Difficulty(difficulty)]


def points_for_quiz(correct_count: int, difficulty: str) -> float:
    return round(correct_count * config.BASE_POINTS_PER_QUIZ_QUESTION * multiplier(difficulty), 1)


def points_for_coding(difficulty: str) -> float:
    return round(config.BASE_POINTS_PER_CODING_PROBLEM * multiplier(difficulty), 1)


def points_for_concept(difficulty: str) -> float:
    return round(config.BASE_POINTS_PER_CONCEPT_CHECK * multiplier(difficulty), 1)


def on_time_bonus(difficulty: str) -> float:
    return round(config.ON_TIME_STREAK_BONUS * multiplier(difficulty), 1)


def is_late(day: models.Day) -> bool:
    """True if the day wasn't (yet, or wasn't) completed on its own calendar date."""
    if day.completed_at is None:
        return day.date < date_type.today() and not day.fully_completed
    return day.completed_at.date() > day.date


def maybe_award_completion_bonus(day: models.Day) -> float:
    """Call right after a component completes. If this finishes the day AND it's
    still that day's date, award the on-time bonus and stamp completed_at."""
    bonus = 0.0
    if day.fully_completed and day.completed_at is None:
        day.completed_at = datetime.utcnow()
        if day.date == date_type.today():
            bonus = on_time_bonus(day.difficulty)
            day.points_earned += bonus
    return bonus


def compute_stats(db: Session, track: str = config.DEFAULT_TRACK) -> dict:
    days = db.query(models.Day).filter(models.Day.track == track).order_by(models.Day.date).all()
    completed_dates = {d.date for d in days if d.fully_completed}
    total_points = sum(d.points_earned for d in days)
    days_completed = len(completed_dates)
    today = date_type.today()
    days_missed_open = sum(1 for d in days if d.date < today and not d.fully_completed)

    # current streak: walk backward from today (or yesterday if today isn't done
    # yet, so still-in-progress "today" doesn't zero out an active streak)
    current_streak = 0
    cursor = today if today in completed_dates else today - timedelta(days=1)
    while cursor in completed_dates:
        current_streak += 1
        cursor -= timedelta(days=1)

    # longest streak: longest run of consecutive calendar dates in completed_dates
    longest_streak = 0
    run = 0
    prev = None
    for d in sorted(completed_dates):
        if prev is not None and d == prev + timedelta(days=1):
            run += 1
        else:
            run = 1
        longest_streak = max(longest_streak, run)
        prev = d

    return {
        "total_points": round(total_points, 1),
        "current_streak": current_streak,
        "longest_streak": longest_streak,
        "days_completed": days_completed,
        "days_missed_open": days_missed_open,
    }
