from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas, scoring
from ..database import get_db
from ..sandbox import grade_submission

router = APIRouter(prefix="/api/coding", tags=["coding"])


@router.post("/{day_id}/submit", response_model=schemas.CodeSubmitOut)
def submit_code(day_id: int, body: schemas.CodeSubmitIn, db: Session = Depends(get_db)):
    day = db.get(models.Day, day_id)
    if not day:
        raise HTTPException(status_code=404, detail="Day not found")

    problem = db.get(models.CodingProblem, day.coding_problem_id)
    if not problem:
        raise HTTPException(status_code=500, detail="Coding problem missing from content bank")

    result = grade_submission(problem.harness_template, body.code)

    day.coding_attempts += 1
    db.add(models.CodeSubmission(
        day_id=day.id,
        problem_id=problem.id,
        code=body.code,
        passed=result.passed,
        tests_passed=result.tests_passed,
        tests_total=result.tests_total,
        output=result.output[-4000:],
        error=result.error[-4000:],
    ))

    points = 0.0
    bonus = 0.0
    if result.passed and not day.coding_completed:
        day.coding_completed = True
        points = scoring.points_for_coding(day.difficulty)
        day.points_earned += points
        bonus = scoring.maybe_award_completion_bonus(day)

    db.commit()

    return schemas.CodeSubmitOut(
        passed=result.passed,
        tests_passed=result.tests_passed,
        tests_total=result.tests_total,
        output=result.output,
        error=result.error,
        points_awarded=points + bonus,
    )
