from datetime import date as date_type

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .. import config, models, schemas, scoring
from ..database import get_db
from ..day_service import get_or_create_day

router = APIRouter(prefix="/api", tags=["challenges"])


@router.get("/config", response_model=schemas.AppConfigOut)
def get_app_config():
    return schemas.AppConfigOut(ai_grading_enabled=bool(config.ANTHROPIC_API_KEY))


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


@router.get("/today", response_model=schemas.ChallengeOut)
def get_today(db: Session = Depends(get_db)):
    day = get_or_create_day(db, date_type.today())
    return _build_challenge_out(db, day)


@router.get("/day/{target_date}", response_model=schemas.ChallengeOut)
def get_day(target_date: date_type, db: Session = Depends(get_db)):
    day = get_or_create_day(db, target_date)
    return _build_challenge_out(db, day)


@router.get("/history", response_model=list[schemas.DayOut])
def get_history(db: Session = Depends(get_db)):
    days = db.query(models.Day).order_by(models.Day.date.desc()).all()
    out = []
    for d in days:
        do = schemas.DayOut.model_validate(d, from_attributes=True)
        do.is_late = scoring.is_late(d)
        out.append(do)
    return out


@router.get("/stats", response_model=schemas.StatsOut)
def get_stats(db: Session = Depends(get_db)):
    return scoring.compute_stats(db)
