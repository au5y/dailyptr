from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas, scoring
from ..auth import get_current_user
from ..database import get_db

router = APIRouter(prefix="/api/quiz", tags=["quiz"])


@router.post("/{day_id}/question/{question_id}/answer", response_model=schemas.QuizAnswerOut)
def answer_quiz_question(
    day_id: int,
    question_id: int,
    body: schemas.QuizAnswerIn,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    day = db.get(models.Day, day_id)
    if not day or day.user_id != user.id:
        raise HTTPException(status_code=404, detail="Day not found")
    if day.quiz_completed:
        raise HTTPException(status_code=400, detail="Quiz already completed for this day")
    if question_id not in day.quiz_question_ids:
        raise HTTPException(status_code=404, detail="Question not part of this day's quiz")

    question = db.get(models.QuizQuestion, question_id)
    is_correct = body.choice_index == question.correct_index

    # Re-answering (picking a different choice) just overwrites the entry -
    # only the latest pick per question counts once the quiz finalizes below.
    day.quiz_answers = {**day.quiz_answers, str(question_id): body.choice_index}

    points_awarded = 0.0
    milestones_hit: list[int] = []
    if len(day.quiz_answers) == len(day.quiz_question_ids):
        by_id = {q.id: q for q in db.query(models.QuizQuestion).filter(models.QuizQuestion.id.in_(day.quiz_question_ids)).all()}
        correct = sum(
            1 for qid in day.quiz_question_ids
            if day.quiz_answers.get(str(qid)) == by_id[qid].correct_index
        )
        day.quiz_completed = True
        day.quiz_correct = correct
        day.quiz_total = len(day.quiz_question_ids)
        points_awarded = scoring.points_for_quiz(correct, day.difficulty)
        day.points_earned += points_awarded
        bonus, milestones_hit = scoring.maybe_award_completion_bonus(db, user, day)
        points_awarded += bonus

    db.commit()

    return schemas.QuizAnswerOut(
        correct=is_correct,
        correct_index=question.correct_index,
        explanation=question.explanation,
        quiz_completed=day.quiz_completed,
        quiz_correct=day.quiz_correct,
        quiz_total=day.quiz_total,
        points_awarded=points_awarded,
        milestones_hit=milestones_hit,
    )
