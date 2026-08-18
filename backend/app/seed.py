"""
Idempotent content seeding: inserts any bank entries not already present
(matched by their natural text key), so re-running on every app startup is
safe and picks up new content you add to the bank files over time.
"""
from sqlalchemy.orm import Session

from . import models
from .content.quiz_bank import QUIZ_QUESTIONS
from .content.coding_bank import CODING_PROBLEMS
from .content.concept_bank import CONCEPT_CHECKS


def seed_content(db: Session) -> None:
    existing_questions = {q for (q,) in db.query(models.QuizQuestion.question).all()}
    for item in QUIZ_QUESTIONS:
        if item["question"] in existing_questions:
            continue
        db.add(models.QuizQuestion(**item))

    existing_titles = {t for (t,) in db.query(models.CodingProblem.title).all()}
    for item in CODING_PROBLEMS:
        if item["title"] in existing_titles:
            continue
        db.add(models.CodingProblem(**item))

    existing_prompts = {p for (p,) in db.query(models.ConceptCheck.prompt).all()}
    for item in CONCEPT_CHECKS:
        if item["prompt"] in existing_prompts:
            continue
        db.add(models.ConceptCheck(**item))

    db.commit()
