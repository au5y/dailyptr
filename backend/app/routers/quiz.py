from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas, scoring
from ..database import get_db

router = APIRouter(prefix="/api/quiz", tags=["quiz"])


@router.post("/{day_id}/submit", response_model=schemas.QuizSubmitOut)
def submit_quiz(day_id: int, body: schemas.QuizSubmitIn, db: Session = Depends(get_db)):
    day = db.get(models.Day, day_id)
    if not day:
        raise HTTPException(status_code=404, detail="Day not found")
    if day.quiz_completed:
        raise HTTPException(status_code=400, detail="Quiz already submitted for this day")

    questions = (
        db.query(models.QuizQuestion)
        .filter(models.QuizQuestion.id.in_(day.quiz_question_ids))
        .all()
    )
    by_id = {q.id: q for q in questions}

    results: dict[int, bool] = {}
    explanations: dict[int, str] = {}
    correct_indices: dict[int, int] = {}
    correct = 0
    for qid in day.quiz_question_ids:
        q = by_id.get(qid)
        if q is None:
            continue
        chosen = body.answers.get(qid)
        is_correct = chosen == q.correct_index
        if is_correct:
            correct += 1
        results[qid] = is_correct
        explanations[qid] = q.explanation
        correct_indices[qid] = q.correct_index

    day.quiz_completed = True
    day.quiz_correct = correct
    day.quiz_total = len(day.quiz_question_ids)

    points = scoring.points_for_quiz(correct, day.difficulty)
    day.points_earned += points
    bonus = scoring.maybe_award_completion_bonus(day)
    db.commit()

    return schemas.QuizSubmitOut(
        correct=correct,
        total=day.quiz_total,
        points_awarded=points + bonus,
        results=results,
        explanations=explanations,
        correct_indices=correct_indices,
    )
