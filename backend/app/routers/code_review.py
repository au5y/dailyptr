import random

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas, scoring
from ..auth import get_current_user
from ..database import get_db

router = APIRouter(prefix="/api/code-review", tags=["code_review"])


def build_challenge_out(challenge: models.CodeReviewChallenge) -> schemas.CodeReviewChallengeOut:
    """Shuffles the real reason for each issue together with the challenge's
    decoy reasons into the answer bank the client picks matches from."""
    reason_bank = [issue["reason"] for issue in challenge.issues] + list(challenge.distractor_reasons)
    random.shuffle(reason_bank)
    return schemas.CodeReviewChallengeOut(
        id=challenge.id,
        title=challenge.title,
        snippet=challenge.snippet,
        reason_bank=reason_bank,
    )


@router.post("/{day_id}/submit", response_model=schemas.CodeReviewSubmitOut)
def submit_code_review(day_id: int, body: schemas.CodeReviewSubmitIn, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    day = db.get(models.Day, day_id)
    if not day or day.user_id != user.id:
        raise HTTPException(status_code=404, detail="Day not found")
    if day.code_review_completed:
        raise HTTPException(status_code=400, detail="Code review already completed for this day")

    challenge = db.get(models.CodeReviewChallenge, day.code_review_challenge_id)
    if not challenge:
        raise HTTPException(status_code=500, detail="Code review challenge missing from content bank")

    # Last match submitted for a given line wins, mirroring how re-picking a
    # quiz choice overwrites the earlier one.
    submitted = {m.line: m.reason for m in body.matches}

    results = []
    correct_count = 0
    for issue in challenge.issues:
        line_found = issue["line"] in submitted
        reason_correct = line_found and submitted[issue["line"]] == issue["reason"]
        if line_found and reason_correct:
            correct_count += 1
        results.append(schemas.CodeReviewIssueResult(
            line=issue["line"],
            reason=issue["reason"],
            explanation=issue["explanation"],
            line_found=line_found,
            reason_correct=reason_correct,
        ))

    total = len(challenge.issues)
    day.code_review_completed = True
    day.code_review_correct = correct_count
    day.code_review_total = total

    points_awarded = scoring.points_for_code_review(correct_count, total, day.difficulty)
    day.points_earned += points_awarded
    bonus, milestones_hit = scoring.maybe_award_completion_bonus(db, user, day)
    points_awarded += bonus
    db.commit()

    return schemas.CodeReviewSubmitOut(
        correct_count=correct_count,
        total=total,
        results=results,
        points_awarded=points_awarded,
        milestones_hit=milestones_hit,
    )
