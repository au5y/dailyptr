from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .. import config, day_service, models, schemas, scoring
from ..auth import get_current_user
from ..database import get_db
from .code_review import grade_and_record_submission as grade_code_review
from .concept import record_submission as record_concept
from .critical_reasoning import grade_and_record_submission as grade_critical_reasoning
from .quiz import grade_and_record_answer

router = APIRouter(prefix="/api", tags=["claim"])


@router.post("/claim", response_model=schemas.ClaimOut)
def claim_guest_progress(body: schemas.ClaimIn, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    """Replays a guest's locally-accumulated progress into this (now
    signed-in) account, using the exact same grading/persistence functions
    live play does - correctness/points are always recomputed server-side
    from the content bank, never trusted from the client's claimed results.

    Merge rule (decided explicitly, not a default worth revisiting lightly):
    per (track, date) or per-track subscription key, existing account data
    always wins - a local record is only used to fill a gap the account
    doesn't already have. Two independent attempts at the same key are never
    merged (there's no sane way to merge two streak sequences). Idempotent:
    calling this twice with the same payload is a no-op the second time,
    since every target key will already exist."""
    claimed_subscriptions: list[str] = []
    skipped_subscriptions: list[str] = []
    for sub in body.subscriptions:
        if sub.track not in config.TRACKS:
            continue
        if day_service.get_subscription(db, user, sub.track):
            skipped_subscriptions.append(sub.track)
            continue
        db.add(models.TrackSubscription(user_id=user.id, track=sub.track, subscribed_at=sub.subscribed_at))
        db.commit()
        claimed_subscriptions.append(sub.track)

    # A guest who picked topics and played is functionally "onboarded" -
    # without this, a first-time Google sign-in after guest play would land
    # back on the onboarding screen despite having just claimed real
    # progress, since User.onboarded is a separate flag /api/onboarding
    # normally sets and nothing else here touches it.
    if claimed_subscriptions and not user.onboarded:
        # `user` came from AuthMiddleware's own (already-closed) session, so
        # it's detached from `db` - mutate a copy `db` actually tracks (same
        # pattern as routers/challenges.py's onboarding endpoint).
        db_user = db.get(models.User, user.id)
        db_user.onboarded = True
        db.commit()

    by_track: dict[str, list[schemas.ClaimDayIn]] = {}
    for day_in in body.days:
        by_track.setdefault(day_in.track, []).append(day_in)

    claimed_days: list[schemas.DayOut] = []
    skipped_days: list[dict] = []
    for track, day_ins in by_track.items():
        if track not in config.TRACKS:
            continue
        start_date = day_service.start_date_for(db, user, track)
        for day_in in sorted(day_ins, key=lambda d: d.date):  # ascending, so streak replay is chronological
            existing = db.query(models.Day).filter(
                models.Day.user_id == user.id, models.Day.date == day_in.date, models.Day.track == track
            ).one_or_none()
            if existing:
                skipped_days.append({"track": track, "date": day_in.date.isoformat(), "reason": "account already has this day"})
                continue

            day = day_service.get_or_create_day(db, user, day_in.date, track)

            for qid_str, choice_index in day_in.quiz_answers.items():
                if int(qid_str) in day.quiz_question_ids and not day.quiz_completed:
                    grade_and_record_answer(db, user, day, int(qid_str), choice_index)

            review_kind = config.TRACKS[track]["review_kind"]
            if review_kind == "code" and day_in.code_review_matches is not None and not day.code_review_completed:
                grade_code_review(db, user, day, day_in.code_review_matches)
            elif review_kind == "reasoning" and day_in.critical_reasoning_matches is not None and not day.critical_reasoning_completed:
                grade_critical_reasoning(db, user, day, day_in.critical_reasoning_matches)

            if day_in.concept_self_rating is not None and not day.concept_completed:
                record_concept(db, user, day, day_in.concept_self_rating)

            db.refresh(day)
            day_out = schemas.DayOut.model_validate(day, from_attributes=True)
            day_out.is_late = scoring.is_late(day, start_date)
            day_out.is_bonus = scoring.is_bonus(day, start_date)
            claimed_days.append(day_out)

    return schemas.ClaimOut(
        claimed_days=claimed_days,
        skipped_days=skipped_days,
        claimed_subscriptions=claimed_subscriptions,
        skipped_subscriptions=skipped_subscriptions,
    )
