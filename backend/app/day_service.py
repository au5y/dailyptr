"""
Turns a calendar date into a concrete Day row (creating + picking its content
on first access). Selection is seeded by the date itself so it's stable if
you reload the page, but still varies day to day across the content pool.
"""
import random
from dataclasses import dataclass
from datetime import date as date_type, timedelta

from fastapi import HTTPException
from sqlalchemy.orm import Session

from . import config, models


@dataclass
class DayContent:
    weekday: int
    difficulty: str
    quiz_question_ids: list[int]
    review_challenge_id: int
    concept_check_id: int


def select_day_content(db: Session, target_date: date_type, track: str) -> DayContent:
    """The deterministic (date, track) -> content pick get_or_create_day uses,
    without touching the Day table - a pure function of (date, track), never
    user_id (see the module docstring). Also used by the stateless guest
    content-fetch endpoint (routers/guest.py) so guests see identical content
    to what a real Day row would pick, without ever writing one."""
    if target_date > date_type.today():
        raise HTTPException(status_code=400, detail="That day hasn't unlocked yet.")
    if track not in config.TRACKS:
        raise HTTPException(status_code=404, detail=f"Unknown track '{track}'.")

    weekday = target_date.weekday()
    difficulty = config.WEEKDAY_DIFFICULTY[weekday].value
    track_salt = sum(ord(c) for c in track)
    rng = random.Random(target_date.toordinal() * 1000 + track_salt)  # deterministic per (date, track)

    review_kind = config.TRACKS[track]["review_kind"]
    review_model = models.CodeReviewChallenge if review_kind == "code" else models.CriticalReasoningChallenge

    quiz_pool = db.query(models.QuizQuestion).filter(models.QuizQuestion.difficulty == difficulty, models.QuizQuestion.track == track).all()
    review_pool = db.query(review_model).filter(review_model.difficulty == difficulty, review_model.track == track).all()
    concept_pool = db.query(models.ConceptCheck).filter(models.ConceptCheck.difficulty == difficulty, models.ConceptCheck.track == track).all()

    if not quiz_pool or not review_pool or not concept_pool:
        raise HTTPException(
            status_code=500,
            detail=f"Content bank is missing '{difficulty}' entries for track '{track}' - run seeding first.",
        )

    quiz_ids, review_challenge_id, concept_check_id = _pick_day_content(rng, quiz_pool, review_pool, concept_pool)
    return DayContent(
        weekday=weekday,
        difficulty=difficulty,
        quiz_question_ids=quiz_ids,
        review_challenge_id=review_challenge_id,
        concept_check_id=concept_check_id,
    )


def get_or_create_day(db: Session, user: models.User, target_date: date_type, track: str = config.DEFAULT_TRACK) -> models.Day:
    if target_date > date_type.today():
        raise HTTPException(status_code=400, detail="That day hasn't unlocked yet.")
    if track not in config.TRACKS:
        raise HTTPException(status_code=404, detail=f"Unknown track '{track}'.")

    existing = db.query(models.Day).filter(
        models.Day.user_id == user.id, models.Day.date == target_date, models.Day.track == track
    ).one_or_none()
    if existing:
        return existing

    content = select_day_content(db, target_date, track)
    review_kind = config.TRACKS[track]["review_kind"]

    day = models.Day(
        user_id=user.id,
        date=target_date,
        track=track,
        weekday=content.weekday,
        difficulty=content.difficulty,
        quiz_question_ids=content.quiz_question_ids,
        code_review_challenge_id=content.review_challenge_id if review_kind == "code" else None,
        critical_reasoning_challenge_id=content.review_challenge_id if review_kind == "reasoning" else None,
        concept_check_id=content.concept_check_id,
        quiz_total=len(content.quiz_question_ids),
    )
    db.add(day)
    db.commit()
    db.refresh(day)
    return day


def get_subscription(db: Session, user: models.User, track: str) -> models.TrackSubscription | None:
    return db.query(models.TrackSubscription).filter(
        models.TrackSubscription.user_id == user.id, models.TrackSubscription.track == track
    ).one_or_none()


def subscribe(db: Session, user: models.User, track: str, backfill_days: int = 30) -> models.TrackSubscription:
    """Idempotent: subscribing to a track you're already on just returns the
    existing row (subscribed_at is a one-time "start line", not a reset)."""
    existing = get_subscription(db, user, track)
    if existing:
        return existing
    subscription = models.TrackSubscription(user_id=user.id, track=track, subscribed_at=date_type.today())
    db.add(subscription)
    db.commit()
    db.refresh(subscription)
    backfill_history(db, user, track, days=backfill_days)
    return subscription


def start_date_for(db: Session, user: models.User, track: str) -> date_type:
    """The date a day on this track starts counting as "late"/"missed" if
    left incomplete - the user's subscription date, or their account creation
    date as a fallback for accounts that predate per-track subscriptions."""
    subscription = get_subscription(db, user, track)
    return subscription.subscribed_at if subscription else user.created_at.date()


def _pick_day_content(rng: random.Random, quiz_pool: list, review_pool: list, concept_pool: list) -> tuple[list[int], int, int]:
    n_quiz = min(config.QUESTIONS_PER_DAY, len(quiz_pool))
    quiz_ids = [q.id for q in rng.sample(quiz_pool, n_quiz)]
    return quiz_ids, rng.choice(review_pool).id, rng.choice(concept_pool).id


def backfill_history(db: Session, user: models.User, track: str, days: int = 30) -> None:
    """Pre-create Day rows for the last `days` days (today inclusive) for `track`,
    so a new user's calendar/history shows a month of already-open days instead
    of only creating them lazily on first click. Idempotent (skips dates that
    already have a row) and safe to call repeatedly, e.g. once right after
    signup and again whenever a track is subscribed to.

    Content pools only vary by (difficulty, track) - just 4 difficulties - so
    this fetches each pool once and reuses it across every date that shares a
    difficulty, and does one INSERT/commit for the whole batch, rather than
    the naive one-query-and-one-commit-per-day-per-pool approach (which was
    ~4 queries and a commit for every single day, even though most of that
    work is identical across days)."""
    if track not in config.TRACKS:
        raise HTTPException(status_code=404, detail=f"Unknown track '{track}'.")

    today = date_type.today()
    target_dates = [today - timedelta(days=offset) for offset in range(days)]

    existing_dates = {
        d for (d,) in db.query(models.Day.date).filter(
            models.Day.user_id == user.id, models.Day.track == track, models.Day.date.in_(target_dates)
        ).all()
    }
    missing_dates = [d for d in target_dates if d not in existing_dates]
    if not missing_dates:
        return

    review_kind = config.TRACKS[track]["review_kind"]
    review_model = models.CodeReviewChallenge if review_kind == "code" else models.CriticalReasoningChallenge

    pools_by_difficulty: dict[str, tuple[list, list, list]] = {}
    track_salt = sum(ord(c) for c in track)
    new_days = []
    for target_date in missing_dates:
        weekday = target_date.weekday()
        difficulty = config.WEEKDAY_DIFFICULTY[weekday].value

        if difficulty not in pools_by_difficulty:
            quiz_pool = db.query(models.QuizQuestion).filter(models.QuizQuestion.difficulty == difficulty, models.QuizQuestion.track == track).all()
            review_pool = db.query(review_model).filter(review_model.difficulty == difficulty, review_model.track == track).all()
            concept_pool = db.query(models.ConceptCheck).filter(models.ConceptCheck.difficulty == difficulty, models.ConceptCheck.track == track).all()
            if not quiz_pool or not review_pool or not concept_pool:
                raise HTTPException(
                    status_code=500,
                    detail=f"Content bank is missing '{difficulty}' entries for track '{track}' - run seeding first.",
                )
            pools_by_difficulty[difficulty] = (quiz_pool, review_pool, concept_pool)
        quiz_pool, review_pool, concept_pool = pools_by_difficulty[difficulty]

        rng = random.Random(target_date.toordinal() * 1000 + track_salt)  # same seeding as get_or_create_day
        quiz_ids, review_challenge_id, concept_check_id = _pick_day_content(rng, quiz_pool, review_pool, concept_pool)

        new_days.append(models.Day(
            user_id=user.id,
            date=target_date,
            track=track,
            weekday=weekday,
            difficulty=difficulty,
            quiz_question_ids=quiz_ids,
            code_review_challenge_id=review_challenge_id if review_kind == "code" else None,
            critical_reasoning_challenge_id=review_challenge_id if review_kind == "reasoning" else None,
            concept_check_id=concept_check_id,
            quiz_total=len(quiz_ids),
        ))

    db.add_all(new_days)
    db.commit()
