"""
Turns a calendar date into a concrete Day row (creating + picking its content
on first access). Selection is seeded by the date itself so it's stable if
you reload the page, but still varies day to day across the content pool.
"""
import random
from datetime import date as date_type, timedelta

from fastapi import HTTPException
from sqlalchemy.orm import Session

from . import config, models


def get_or_create_day(db: Session, target_date: date_type, track: str = config.DEFAULT_TRACK) -> models.Day:
    if target_date > date_type.today():
        raise HTTPException(status_code=400, detail="That day hasn't unlocked yet.")
    if track not in config.TRACKS:
        raise HTTPException(status_code=404, detail=f"Unknown track '{track}'.")

    existing = db.query(models.Day).filter(models.Day.date == target_date, models.Day.track == track).one_or_none()
    if existing:
        return existing

    weekday = target_date.weekday()
    difficulty = config.WEEKDAY_DIFFICULTY[weekday].value
    track_salt = sum(ord(c) for c in track)
    rng = random.Random(target_date.toordinal() * 1000 + track_salt)  # deterministic per (date, track)

    quiz_pool = db.query(models.QuizQuestion).filter(models.QuizQuestion.difficulty == difficulty, models.QuizQuestion.track == track).all()
    coding_pool = db.query(models.CodingProblem).filter(models.CodingProblem.difficulty == difficulty, models.CodingProblem.track == track).all()
    concept_pool = db.query(models.ConceptCheck).filter(models.ConceptCheck.difficulty == difficulty, models.ConceptCheck.track == track).all()

    if not quiz_pool or not coding_pool or not concept_pool:
        raise HTTPException(
            status_code=500,
            detail=f"Content bank is missing '{difficulty}' entries for track '{track}' - run seeding first.",
        )

    n_quiz = min(config.QUESTIONS_PER_DAY, len(quiz_pool))
    quiz_ids = [q.id for q in rng.sample(quiz_pool, n_quiz)]
    coding_problem = rng.choice(coding_pool)
    concept_check = rng.choice(concept_pool)

    day = models.Day(
        date=target_date,
        track=track,
        weekday=weekday,
        difficulty=difficulty,
        quiz_question_ids=quiz_ids,
        coding_problem_id=coding_problem.id,
        concept_check_id=concept_check.id,
        quiz_total=n_quiz,
    )
    db.add(day)
    db.commit()
    db.refresh(day)
    return day


def backfill_history(db: Session, track: str, days: int = 30) -> None:
    """Pre-create Day rows for the last `days` days (today inclusive) for `track`,
    so its calendar/history shows a month of already-open days instead of only
    creating them lazily on first click. get_or_create_day is idempotent (checks
    for an existing row before creating), so this is cheap and safe to call on
    every startup."""
    today = date_type.today()
    for offset in range(days):
        get_or_create_day(db, today - timedelta(days=offset), track)
