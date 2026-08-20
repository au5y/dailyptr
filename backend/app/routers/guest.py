from datetime import date as date_type

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from .. import config, day_service, models, schemas, scoring
from ..auth import get_current_user
from ..database import get_db
from .code_review import build_challenge_out as build_code_review_out
from .critical_reasoning import build_challenge_out as build_critical_reasoning_out

router = APIRouter(prefix="/api/guest", tags=["guest"])


def _require_guest(user: models.User) -> None:
    """Every /api/guest/* route requires a resolvable session (same as every
    other route - see auth.AuthMiddleware) but is only meaningful for a guest
    identity; a signed-in account always has (and should use) the real,
    persisted routes. Keeping one unambiguous code path per account type."""
    if not user.google_sub.startswith("guest-"):
        raise HTTPException(status_code=403, detail="This endpoint is for guest sessions only.")


def _valid_track(track: str) -> str:
    if track not in config.TRACKS:
        raise HTTPException(status_code=404, detail=f"Unknown track '{track}'.")
    return track


@router.get("/challenge", response_model=schemas.GuestChallengeOut)
def get_guest_challenge(
    date: date_type = Query(...),
    track: str = Query(config.DEFAULT_TRACK),
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    """Same content a real Day row would get for this (date, track) - see
    day_service.select_day_content - but computed fresh every call, without
    ever writing a Day row. Lets a guest browse/play entirely client-side."""
    _require_guest(user)
    _valid_track(track)
    content = day_service.select_day_content(db, date, track)

    questions = db.query(models.QuizQuestion).filter(models.QuizQuestion.id.in_(content.quiz_question_ids)).all()
    by_id = {q.id: q for q in questions}
    ordered = [by_id[i] for i in content.quiz_question_ids if i in by_id]

    concept = db.get(models.ConceptCheck, content.concept_check_id)

    review_kind = config.TRACKS[track]["review_kind"]
    code_review_out = None
    critical_reasoning_out = None
    if review_kind == "code":
        code_review_out = build_code_review_out(db.get(models.CodeReviewChallenge, content.review_challenge_id))
    else:
        critical_reasoning_out = build_critical_reasoning_out(db.get(models.CriticalReasoningChallenge, content.review_challenge_id))

    return schemas.GuestChallengeOut(
        day=schemas.VirtualDayOut(date=date, track=track, weekday=content.weekday, difficulty=content.difficulty),
        quiz=[schemas.QuizQuestionOut.model_validate(q, from_attributes=True) for q in ordered],
        code_review=code_review_out,
        critical_reasoning=critical_reasoning_out,
        concept=schemas.ConceptCheckOut.model_validate(concept, from_attributes=True),
    )


@router.post("/quiz/answer", response_model=schemas.GuestQuizAnswerOut)
def answer_guest_quiz_question(body: schemas.GuestQuizAnswerIn, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    """Single-question, single-shot grading - no persisted state to check
    "already answered" against, so (unlike quiz.py's authenticated route)
    this can be called repeatedly for the same question; the client's local
    progress store is what tracks which questions are answered."""
    _require_guest(user)
    _valid_track(body.track)
    content = day_service.select_day_content(db, body.date, body.track)
    if body.question_id not in content.quiz_question_ids:
        raise HTTPException(status_code=404, detail="Question not part of this day's quiz")

    question = db.get(models.QuizQuestion, body.question_id)
    return schemas.GuestQuizAnswerOut(
        correct=body.choice_index == question.correct_index,
        correct_index=question.correct_index,
        explanation=question.explanation,
    )


@router.post("/code-review/check", response_model=schemas.CodeReviewSubmitOut)
def check_guest_code_review(body: schemas.GuestReviewCheckIn, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    _require_guest(user)
    _valid_track(body.track)
    if config.TRACKS[body.track]["review_kind"] != "code":
        raise HTTPException(status_code=400, detail="This track doesn't use Code Review.")
    content = day_service.select_day_content(db, body.date, body.track)
    challenge = db.get(models.CodeReviewChallenge, content.review_challenge_id)

    raw_results, correct_count = scoring.grade_line_matches(challenge.issues, body.matches)
    total = len(challenge.issues)
    return schemas.CodeReviewSubmitOut(
        correct_count=correct_count,
        total=total,
        results=[schemas.CodeReviewIssueResult(**r) for r in raw_results],
        points_awarded=scoring.points_for_code_review(correct_count, total, content.difficulty),
        milestones_hit=[],  # no persisted streak history to check for a guest - see schemas.GuestQuizAnswerOut
    )


@router.post("/critical-reasoning/check", response_model=schemas.CriticalReasoningSubmitOut)
def check_guest_critical_reasoning(body: schemas.GuestReviewCheckIn, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    _require_guest(user)
    _valid_track(body.track)
    if config.TRACKS[body.track]["review_kind"] != "reasoning":
        raise HTTPException(status_code=400, detail="This track doesn't use Critical Reasoning Review.")
    content = day_service.select_day_content(db, body.date, body.track)
    challenge = db.get(models.CriticalReasoningChallenge, content.review_challenge_id)

    raw_results, correct_count = scoring.grade_line_matches(challenge.issues, body.matches)
    total = len(challenge.issues)
    return schemas.CriticalReasoningSubmitOut(
        correct_count=correct_count,
        total=total,
        results=[schemas.CriticalReasoningIssueResult(**r) for r in raw_results],
        points_awarded=scoring.points_for_code_review(correct_count, total, content.difficulty),
        milestones_hit=[],
    )


@router.post("/concept/score", response_model=schemas.GuestConceptScoreOut)
def score_guest_concept(body: schemas.GuestConceptScoreIn, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    _require_guest(user)
    _valid_track(body.track)
    content = day_service.select_day_content(db, body.date, body.track)
    points = scoring.points_for_concept(content.difficulty) if body.self_rating_correct else 0.0
    return schemas.GuestConceptScoreOut(points_awarded=points)
