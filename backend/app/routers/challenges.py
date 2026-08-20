from datetime import date as date_type

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from .. import config, models, schemas, scoring
from ..auth import get_current_user
from ..database import get_db
from ..day_service import get_or_create_day, start_date_for, subscribe
from .code_review import build_challenge_out as build_code_review_out

router = APIRouter(prefix="/api", tags=["challenges"])


def _valid_track(track: str) -> str:
    if track not in config.TRACKS:
        raise HTTPException(status_code=404, detail=f"Unknown track '{track}'.")
    return track


def _build_challenge_out(db: Session, user: models.User, day: models.Day) -> schemas.ChallengeOut:
    questions = (
        db.query(models.QuizQuestion)
        .filter(models.QuizQuestion.id.in_(day.quiz_question_ids))
        .all()
    )
    by_id = {q.id: q for q in questions}
    ordered = [by_id[i] for i in day.quiz_question_ids if i in by_id]

    code_review = db.get(models.CodeReviewChallenge, day.code_review_challenge_id)
    concept = db.get(models.ConceptCheck, day.concept_check_id)

    start_date = start_date_for(db, user, day.track)
    day_out = schemas.DayOut.model_validate(day, from_attributes=True)
    day_out.is_late = scoring.is_late(day, start_date)
    day_out.is_bonus = scoring.is_bonus(day, start_date)

    return schemas.ChallengeOut(
        day=day_out,
        quiz=[schemas.QuizQuestionOut.model_validate(q, from_attributes=True) for q in ordered],
        code_review=build_code_review_out(code_review),
        concept=schemas.ConceptCheckOut.model_validate(concept, from_attributes=True),
    )


@router.get("/config", response_model=schemas.AppConfigOut)
def get_app_config():
    return schemas.AppConfigOut(ai_grading_enabled=bool(config.ANTHROPIC_API_KEY))


@router.get("/me", response_model=schemas.MeOut)
def get_me(user: models.User = Depends(get_current_user)):
    return schemas.MeOut(
        email=user.email,
        name=user.name,
        onboarded=user.onboarded,
        is_guest=user.google_sub.startswith("guest-"),
    )


@router.get("/tracks", response_model=list[schemas.TrackOut])
def get_tracks(db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    subscribed = {
        s.track for s in db.query(models.TrackSubscription).filter(models.TrackSubscription.user_id == user.id).all()
    }
    return [
        schemas.TrackOut(id=tid, name=meta["name"], subscribed=tid in subscribed)
        for tid, meta in config.TRACKS.items()
    ]


@router.post("/onboarding", response_model=list[schemas.TrackOut])
def complete_onboarding(body: schemas.OnboardingIn, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    """First-login topic selection: subscribes the user to each chosen track
    (stamping today as that track's "start line" - see day_service.subscribe)
    and marks onboarding done so this doesn't run again."""
    chosen = [_valid_track(t) for t in dict.fromkeys(body.tracks)]  # de-dupe, preserve order
    if not chosen:
        raise HTTPException(status_code=400, detail="Pick at least one topic.")
    for track in chosen:
        subscribe(db, user, track)
    # `user` came from AuthMiddleware's own (already-closed) session, so it's
    # detached from `db` - mutate a copy of it that `db` actually tracks.
    db_user = db.get(models.User, user.id)
    db_user.onboarded = True
    db.commit()
    return get_tracks(db, user)


@router.post("/subscribe", response_model=list[schemas.TrackOut])
def add_subscription(body: schemas.SubscribeIn, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    """Subscribe to an additional track after onboarding (e.g. from the track
    switcher's "add topic" control). Today becomes that track's start line."""
    subscribe(db, user, _valid_track(body.track))
    return get_tracks(db, user)


@router.get("/today", response_model=schemas.ChallengeOut)
def get_today(track: str = Query(config.DEFAULT_TRACK), db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    day = get_or_create_day(db, user, date_type.today(), _valid_track(track))
    return _build_challenge_out(db, user, day)


@router.get("/day/{target_date}", response_model=schemas.ChallengeOut)
def get_day(target_date: date_type, track: str = Query(config.DEFAULT_TRACK), db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    day = get_or_create_day(db, user, target_date, _valid_track(track))
    return _build_challenge_out(db, user, day)


@router.get("/history", response_model=list[schemas.DayOut])
def get_history(track: str = Query(config.DEFAULT_TRACK), db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    _valid_track(track)
    start_date = start_date_for(db, user, track)
    days = db.query(models.Day).filter(
        models.Day.user_id == user.id, models.Day.track == track
    ).order_by(models.Day.date.desc()).all()
    out = []
    for d in days:
        do = schemas.DayOut.model_validate(d, from_attributes=True)
        do.is_late = scoring.is_late(d, start_date)
        do.is_bonus = scoring.is_bonus(d, start_date)
        out.append(do)
    return out


@router.get("/stats", response_model=schemas.StatsOut)
def get_stats(track: str = Query(config.DEFAULT_TRACK), db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    track = _valid_track(track)
    return scoring.compute_stats(db, user, track, start_date_for(db, user, track))


@router.post("/day/{day_id}/reset", response_model=schemas.ChallengeOut)
def reset_day(day_id: int, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    """Resets a day's progress (quiz/code/concept completion, points, attempts)
    so it can be retried - the same content, since it's picked deterministically
    from (date, track). Does not touch other days' points/streak bookkeeping;
    those are computed live from each day's current state."""
    day = db.get(models.Day, day_id)
    if not day or day.user_id != user.id:
        raise HTTPException(status_code=404, detail="Day not found")

    day.quiz_completed = False
    day.quiz_correct = 0
    day.quiz_answers = {}
    day.code_review_completed = False
    day.code_review_correct = 0
    day.code_review_total = 0
    day.concept_completed = False
    day.concept_self_rating = False
    day.points_earned = 0.0
    day.completed_at = None
    db.commit()
    db.refresh(day)

    return _build_challenge_out(db, user, day)
