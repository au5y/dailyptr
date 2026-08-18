from datetime import date as date_type

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from .. import config, models, schemas, scoring
from ..database import get_db
from ..day_service import get_or_create_day

router = APIRouter(prefix="/api", tags=["challenges"])


def _valid_track(track: str) -> str:
    if track not in config.TRACKS:
        raise HTTPException(status_code=404, detail=f"Unknown track '{track}'.")
    return track


def _build_challenge_out(db: Session, day: models.Day) -> schemas.ChallengeOut:
    questions = (
        db.query(models.QuizQuestion)
        .filter(models.QuizQuestion.id.in_(day.quiz_question_ids))
        .all()
    )
    by_id = {q.id: q for q in questions}
    ordered = [by_id[i] for i in day.quiz_question_ids if i in by_id]

    coding = db.get(models.CodingProblem, day.coding_problem_id)
    concept = db.get(models.ConceptCheck, day.concept_check_id)

    day_out = schemas.DayOut.model_validate(day, from_attributes=True)
    day_out.is_late = scoring.is_late(day)

    return schemas.ChallengeOut(
        day=day_out,
        quiz=[schemas.QuizQuestionOut.model_validate(q, from_attributes=True) for q in ordered],
        coding=schemas.CodingProblemOut.model_validate(coding, from_attributes=True),
        concept=schemas.ConceptCheckOut.model_validate(concept, from_attributes=True),
    )


@router.get("/config", response_model=schemas.AppConfigOut)
def get_app_config():
    return schemas.AppConfigOut(ai_grading_enabled=bool(config.ANTHROPIC_API_KEY))


@router.get("/tracks", response_model=list[schemas.TrackOut])
def get_tracks():
    return [schemas.TrackOut(id=tid, name=meta["name"], uses_sandbox=meta["uses_sandbox"]) for tid, meta in config.TRACKS.items()]


@router.get("/today", response_model=schemas.ChallengeOut)
def get_today(track: str = Query(config.DEFAULT_TRACK), db: Session = Depends(get_db)):
    day = get_or_create_day(db, date_type.today(), _valid_track(track))
    return _build_challenge_out(db, day)


@router.get("/day/{target_date}", response_model=schemas.ChallengeOut)
def get_day(target_date: date_type, track: str = Query(config.DEFAULT_TRACK), db: Session = Depends(get_db)):
    day = get_or_create_day(db, target_date, _valid_track(track))
    return _build_challenge_out(db, day)


@router.get("/history", response_model=list[schemas.DayOut])
def get_history(track: str = Query(config.DEFAULT_TRACK), db: Session = Depends(get_db)):
    _valid_track(track)
    days = db.query(models.Day).filter(models.Day.track == track).order_by(models.Day.date.desc()).all()
    out = []
    for d in days:
        do = schemas.DayOut.model_validate(d, from_attributes=True)
        do.is_late = scoring.is_late(d)
        out.append(do)
    return out


@router.get("/stats", response_model=schemas.StatsOut)
def get_stats(track: str = Query(config.DEFAULT_TRACK), db: Session = Depends(get_db)):
    return scoring.compute_stats(db, _valid_track(track))


@router.post("/day/{day_id}/reset", response_model=schemas.ChallengeOut)
def reset_day(day_id: int, db: Session = Depends(get_db)):
    """Resets a day's progress (quiz/code/concept completion, points, attempts)
    so it can be retried - the same content, since it's picked deterministically
    from (date, track). Does not touch other days' points/streak bookkeeping;
    those are computed live from each day's current state."""
    day = db.get(models.Day, day_id)
    if not day:
        raise HTTPException(status_code=404, detail="Day not found")

    day.quiz_completed = False
    day.quiz_correct = 0
    day.coding_completed = False
    day.coding_attempts = 0
    day.concept_completed = False
    day.concept_self_rating = False
    day.points_earned = 0.0
    day.completed_at = None
    db.commit()
    db.refresh(day)

    return _build_challenge_out(db, day)
