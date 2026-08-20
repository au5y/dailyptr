from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import ai_grading, models, schemas, scoring
from ..auth import get_current_user
from ..database import get_db

router = APIRouter(prefix="/api/concept", tags=["concept"])


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
