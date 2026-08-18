import random

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import config, models, schemas, scoring
from ..database import get_db
from ..sandbox import grade_submission
from ..sandbox.common import SandboxResult

router = APIRouter(prefix="/api/coding", tags=["coding"])


@router.get("/{day_id}/blocks", response_model=schemas.CodeBlocksOut)
def get_code_blocks(day_id: int, db: Session = Depends(get_db)):
    """Shuffled lines of the reference solution, for the optional block-assembly
    mode - fetched only when the user turns that mode on (see schemas.CodeBlocksOut)."""
    day = db.get(models.Day, day_id)
    if not day:
        raise HTTPException(status_code=404, detail="Day not found")

    problem = db.get(models.CodingProblem, day.coding_problem_id)
    if not problem:
        raise HTTPException(status_code=500, detail="Coding problem missing from content bank")
    if not problem.reference_solution:
        raise HTTPException(status_code=404, detail="Block mode isn't available for this problem")

    lines = [ln for ln in problem.reference_solution.split("\n") if ln.strip()]
    random.shuffle(lines)
    return schemas.CodeBlocksOut(lines=lines)


@router.post("/{day_id}/submit", response_model=schemas.CodeSubmitOut)
def submit_code(day_id: int, body: schemas.CodeSubmitIn, db: Session = Depends(get_db)):
    day = db.get(models.Day, day_id)
    if not day:
        raise HTTPException(status_code=404, detail="Day not found")

    problem = db.get(models.CodingProblem, day.coding_problem_id)
    if not problem:
        raise HTTPException(status_code=500, detail="Coding problem missing from content bank")

    uses_sandbox = config.TRACKS.get(day.track, config.TRACKS[config.DEFAULT_TRACK])["uses_sandbox"]

    if uses_sandbox:
        result = grade_submission(problem.harness_template, body.code)
        reference_solution = None
    else:
        # No compiler for this track (e.g. html_css) - any non-empty attempt
        # self-certifies as "done", and the reference solution is revealed
        # for the user to compare against, same spirit as the concept check.
        if not body.code.strip():
            raise HTTPException(status_code=400, detail="Write your attempt first")
        result = SandboxResult(True, 1, 1, "Submitted - compare your attempt against the reference solution below.", "")
        reference_solution = problem.reference_solution

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
        reference_solution=reference_solution,
    )
