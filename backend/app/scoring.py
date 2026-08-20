from datetime import date as date_type, datetime, timedelta

from sqlalchemy.orm import Session

from . import config, models


def multiplier(difficulty: str) -> float:
    return config.DIFFICULTY_POINT_MULTIPLIER[config.Difficulty(difficulty)]


def points_for_quiz(correct_count: int, difficulty: str) -> float:
    return round(correct_count * config.BASE_POINTS_PER_QUIZ_QUESTION * multiplier(difficulty), 1)


def points_for_code_review(correct_count: int, total: int, difficulty: str) -> float:
    fraction = correct_count / total if total else 0.0
    return round(config.BASE_POINTS_PER_CODE_REVIEW * fraction * multiplier(difficulty), 1)


def grade_line_matches(issues: list[dict], matches: list) -> tuple[list[dict], int]:
    """The click-a-line/match-a-reason grading algorithm shared by Code
    Review and Critical Reasoning Review (and the stateless guest variants
    of both, routers/guest.py): for each real issue, was its line flagged at
    all, and if so, was it matched to the right reason. `matches` is a list
    of objects with `.line`/`.reason` attributes (schemas.CodeReviewMatchIn/
    CriticalReasoningMatchIn - the two are structurally identical). Returns
    (per-issue result dicts with keys line/reason/explanation/line_found/
    reason_correct, correct_count)."""
    # Last match submitted for a given line wins, mirroring how re-picking a
    # quiz choice overwrites the earlier one.
    submitted = {m.line: m.reason for m in matches}

    results = []
    correct_count = 0
    for issue in issues:
        line_found = issue["line"] in submitted
        reason_correct = line_found and submitted[issue["line"]] == issue["reason"]
        if line_found and reason_correct:
            correct_count += 1
        results.append({
            "line": issue["line"],
            "reason": issue["reason"],
            "explanation": issue["explanation"],
            "line_found": line_found,
            "reason_correct": reason_correct,
        })
    return results, correct_count


def points_for_concept(difficulty: str) -> float:
    return round(config.BASE_POINTS_PER_CONCEPT_CHECK * multiplier(difficulty), 1)


def on_time_bonus(difficulty: str) -> float:
    return round(config.ON_TIME_STREAK_BONUS * multiplier(difficulty), 1)


def is_bonus(day: models.Day, start_date: date_type) -> bool:
    """True for a day that predates the user's subscription to this track -
    backfilled purely so history/the calendar has content to browse, not
    something they could have "missed"."""
    return day.date < start_date


def is_late(day: models.Day, start_date: date_type) -> bool:
    """True if the day wasn't (yet, or wasn't) completed on its own calendar
    date. Bonus days (see is_bonus) are never late - they're optional extras
    from before the user's own start date, not something to catch up on."""
    if is_bonus(day, start_date):
        return False
    if day.completed_at is None:
        return day.date < date_type.today() and not day.fully_completed
    return day.completed_at.date() > day.date


def _streaks(completed_dates: set[date_type]) -> tuple[int, int]:
    """(current_streak, longest_streak) for a set of fully-completed dates."""
    today = date_type.today()
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

    return current_streak, longest_streak


def award_new_milestones(db: Session, user: models.User, track: str, current_streak: int) -> tuple[list[int], float]:
    """Awards every streak milestone (config.STREAK_MILESTONES) newly reached
    by current_streak that this (user, track) hasn't already been awarded -
    each one only ever fires once, even across streak resets. Returns
    (newly_awarded milestones in ascending order, their total bonus points)."""
    already = {
        m for (m,) in db.query(models.MilestoneAward.milestone).filter(
            models.MilestoneAward.user_id == user.id, models.MilestoneAward.track == track,
        ).all()
    }
    newly_awarded = []
    total_bonus = 0.0
    for milestone in config.STREAK_MILESTONES:
        if milestone > current_streak or milestone in already:
            continue
        bonus = config.STREAK_MILESTONE_BONUS[milestone]
        db.add(models.MilestoneAward(user_id=user.id, track=track, milestone=milestone, points_awarded=bonus))
        newly_awarded.append(milestone)
        total_bonus += bonus
    return newly_awarded, total_bonus


def maybe_award_completion_bonus(db: Session, user: models.User, day: models.Day) -> tuple[float, list[int]]:
    """Call right after a component completes. If this finishes the day AND it's
    still that day's date, award the on-time bonus and stamp completed_at.
    Either way (on-time or catching up a late day), also checks whether this
    completion newly extended the current streak into a milestone - see
    award_new_milestones. Returns (bonus points, newly-hit milestones)."""
    bonus = 0.0
    milestones_hit: list[int] = []
    if day.fully_completed and day.completed_at is None:
        day.completed_at = datetime.utcnow()
        if day.date == date_type.today():
            bonus = on_time_bonus(day.difficulty)
            day.points_earned += bonus

        completed_dates = _completed_dates(db, user, day.track)
        completed_dates.add(day.date)
        current_streak, _ = _streaks(completed_dates)
        milestones_hit, milestone_bonus = award_new_milestones(db, user, day.track, current_streak)
        if milestone_bonus:
            day.points_earned += milestone_bonus
            bonus += milestone_bonus
    return bonus, milestones_hit


def _completed_dates(db: Session, user: models.User, track: str) -> set[date_type]:
    days = db.query(models.Day).filter(models.Day.user_id == user.id, models.Day.track == track).all()
    return {d.date for d in days if d.fully_completed}


def compute_stats(db: Session, user: models.User, track: str = config.DEFAULT_TRACK, start_date: date_type | None = None) -> dict:
    if start_date is None:
        start_date = user.created_at.date()
    days = db.query(models.Day).filter(
        models.Day.user_id == user.id, models.Day.track == track
    ).order_by(models.Day.date).all()
    completed_dates = {d.date for d in days if d.fully_completed}
    total_points = sum(d.points_earned for d in days)
    days_completed = len(completed_dates)
    today = date_type.today()
    days_missed_open = sum(1 for d in days if d.date >= start_date and d.date < today and not d.fully_completed)

    current_streak, longest_streak = _streaks(completed_dates)

    badges = sorted(
        m for (m,) in db.query(models.MilestoneAward.milestone).filter(
            models.MilestoneAward.user_id == user.id, models.MilestoneAward.track == track,
        ).all()
    )

    return {
        "total_points": round(total_points, 1),
        "current_streak": current_streak,
        "longest_streak": longest_streak,
        "days_completed": days_completed,
        "days_missed_open": days_missed_open,
        "badges": badges,
    }
