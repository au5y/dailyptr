from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import ai_grading, config, models, schemas, scoring
from ..auth import get_current_user
from ..database import get_db

router = APIRouter(prefix="/api/concept", tags=["concept"])


def _check_and_spend_ai_grade_quota(db: Session, user: models.User) -> None:
    """Raises 429 once a user has spent AI_GRADE_DAILY_LIMIT calls today.
    Spent *before* calling the API (not just on success) so a string of
    failed/retried calls still counts against the cap - the whole point is
    bounding real API spend, not just successful grades.

    `user` comes from AuthMiddleware's own short-lived session (already
    closed by the time routes run - see auth.py), so it's detached; mutating
    it and committing on this route's `db` session would silently no-op.
    Re-fetch the row into `db` first so the update actually persists."""
    db_user = db.get(models.User, user.id)
    today = date.today()
    if db_user.ai_grade_count_date != today:
        db_user.ai_grade_count = 0
        db_user.ai_grade_count_date = today
    if db_user.ai_grade_count >= config.AI_GRADE_DAILY_LIMIT:
        raise HTTPException(status_code=429, detail=f"Daily AI-grade limit reached ({config.AI_GRADE_DAILY_LIMIT}/day) - try again tomorrow")
    db_user.ai_grade_count += 1
    db.commit()


@router.post("/{day_id}/ai-grade", response_model=schemas.ConceptGradeOut)
def ai_grade_concept(day_id: int, body: schemas.ConceptGradeIn, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    day = db.get(models.Day, day_id)
    if not day or day.user_id != user.id:
        raise HTTPException(status_code=404, detail="Day not found")

    concept = db.get(models.ConceptCheck, day.concept_check_id)
    if not concept:
        raise HTTPException(status_code=500, detail="Concept check missing from content bank")

    if not body.notes.strip():
        raise HTTPException(status_code=400, detail="Write your answer first")

    _check_and_spend_ai_grade_quota(db, user)

    try:
        correct, feedback = ai_grading.grade_concept(concept.prompt, concept.model_answer, body.notes)
    except RuntimeError:
        raise HTTPException(status_code=503, detail="AI grading not configured (set ANTHROPIC_API_KEY)")
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"AI grading failed: {e}")

    return schemas.ConceptGradeOut(correct=correct, feedback=feedback)


def record_submission(db: Session, user: models.User, day: models.Day, self_rating_correct: bool) -> schemas.ConceptSubmitOut:
    """The actual persistence, factored out of the route below so
    routers/claim.py can replay a guest's self-rating through the exact same
    logic. Caller is responsible for the day/ownership HTTP guard; unlike the
    other components this is idempotent by construction (no-ops if already
    completed) rather than raising, matching the route's original behavior."""
    concept = db.get(models.ConceptCheck, day.concept_check_id)
    if not concept:
        raise HTTPException(status_code=500, detail="Concept check missing from content bank")

    points = 0.0
    bonus = 0.0
    milestones_hit: list[int] = []
    if not day.concept_completed:
        day.concept_completed = True
        day.concept_self_rating = self_rating_correct
        if self_rating_correct:
            points = scoring.points_for_concept(day.difficulty)
            day.points_earned += points
        bonus, milestones_hit = scoring.maybe_award_completion_bonus(db, user, day)
        db.commit()

    return schemas.ConceptSubmitOut(model_answer=concept.model_answer, points_awarded=points + bonus, milestones_hit=milestones_hit)


@router.post("/{day_id}/submit", response_model=schemas.ConceptSubmitOut)
def submit_concept(day_id: int, body: schemas.ConceptSubmitIn, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    day = db.get(models.Day, day_id)
    if not day or day.user_id != user.id:
        raise HTTPException(status_code=404, detail="Day not found")

    return record_submission(db, user, day, body.self_rating_correct)
