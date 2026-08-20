import random

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import config, models, schemas, scoring
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


def grade_and_record_submission(db: Session, user: models.User, day: models.Day, matches: list) -> schemas.CodeReviewSubmitOut:
    """The actual grading + persistence, factored out of the route below so
    routers/claim.py can replay a guest's submission through the exact same
    logic. Caller is responsible for the day/ownership/review-kind/already-
    completed HTTP guards."""
    challenge = db.get(models.CodeReviewChallenge, day.code_review_challenge_id)
    if not challenge:
        raise HTTPException(status_code=500, detail="Code review challenge missing from content bank")

    raw_results, correct_count = scoring.grade_line_matches(challenge.issues, matches)
    results = [schemas.CodeReviewIssueResult(**r) for r in raw_results]

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


@router.post("/{day_id}/submit", response_model=schemas.CodeReviewSubmitOut)
def submit_code_review(day_id: int, body: schemas.CodeReviewSubmitIn, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    day = db.get(models.Day, day_id)
    if not day or day.user_id != user.id:
        raise HTTPException(status_code=404, detail="Day not found")
    if config.TRACKS[day.track]["review_kind"] != "code":
        raise HTTPException(status_code=400, detail="This track doesn't use Code Review.")
    if day.code_review_completed:
        raise HTTPException(status_code=400, detail="Code review already completed for this day")

    return grade_and_record_submission(db, user, day, body.matches)
