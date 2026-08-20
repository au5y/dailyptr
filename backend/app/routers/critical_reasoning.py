import random

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import config, models, schemas, scoring
from ..auth import get_current_user
from ..database import get_db

router = APIRouter(prefix="/api/critical-reasoning", tags=["critical_reasoning"])


def build_challenge_out(challenge: models.CriticalReasoningChallenge) -> schemas.CriticalReasoningChallengeOut:
    """Shuffles the real reason for each issue together with the challenge's
    decoy reasons into the answer bank the client picks matches from."""
    reason_bank = [issue["reason"] for issue in challenge.issues] + list(challenge.distractor_reasons)
    random.shuffle(reason_bank)
    return schemas.CriticalReasoningChallengeOut(
        id=challenge.id,
        title=challenge.title,
        passage=challenge.passage,
        reason_bank=reason_bank,
    )


@router.post("/{day_id}/submit", response_model=schemas.CriticalReasoningSubmitOut)
def submit_critical_reasoning(day_id: int, body: schemas.CriticalReasoningSubmitIn, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    day = db.get(models.Day, day_id)
    if not day or day.user_id != user.id:
        raise HTTPException(status_code=404, detail="Day not found")
    if config.TRACKS[day.track]["review_kind"] != "reasoning":
        raise HTTPException(status_code=400, detail="This track doesn't use Critical Reasoning Review.")
    if day.critical_reasoning_completed:
        raise HTTPException(status_code=400, detail="Critical reasoning review already completed for this day")

    challenge = db.get(models.CriticalReasoningChallenge, day.critical_reasoning_challenge_id)
    if not challenge:
        raise HTTPException(status_code=500, detail="Critical reasoning challenge missing from content bank")

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
        results.append(schemas.CriticalReasoningIssueResult(
            line=issue["line"],
            reason=issue["reason"],
            explanation=issue["explanation"],
            line_found=line_found,
            reason_correct=reason_correct,
        ))

    total = len(challenge.issues)
    day.critical_reasoning_completed = True
    day.critical_reasoning_correct = correct_count
    day.critical_reasoning_total = total

    points_awarded = scoring.points_for_code_review(correct_count, total, day.difficulty)
    day.points_earned += points_awarded
    bonus, milestones_hit = scoring.maybe_award_completion_bonus(db, user, day)
    points_awarded += bonus
    db.commit()

    return schemas.CriticalReasoningSubmitOut(
        correct_count=correct_count,
        total=total,
        results=results,
        points_awarded=points_awarded,
        milestones_hit=milestones_hit,
    )
