"""
Idempotent content seeding: inserts any bank entries not already present
(matched by their natural text key + track), so re-running on every app
startup is safe and picks up new content you add to the bank files over
time.
"""
from sqlalchemy.orm import Session

from . import models
from .content.quiz_bank import QUIZ_QUESTIONS
from .content.coding_bank import CODING_PROBLEMS
from .content.concept_bank import CONCEPT_CHECKS
from .content.cpp_backend_bank import CPP_BACKEND_QUIZ, CPP_BACKEND_CODING, CPP_BACKEND_CONCEPT
from .content.html_css_bank import HTML_CSS_QUIZ, HTML_CSS_PRACTICE, HTML_CSS_CONCEPT

# (items, default track) - items from bank files don't carry an explicit
# "track" key, so it's defaulted here per source list. The former standalone
# "C++ Backend" track's content now bundles straight into cpp_core's pool
# (same track, more variety) rather than living behind its own switcher tab.
QUIZ_SOURCES = [(QUIZ_QUESTIONS, "cpp_core"), (CPP_BACKEND_QUIZ, "cpp_core"), (HTML_CSS_QUIZ, "html_css")]
CODING_SOURCES = [(CODING_PROBLEMS, "cpp_core"), (CPP_BACKEND_CODING, "cpp_core"), (HTML_CSS_PRACTICE, "html_css")]
CONCEPT_SOURCES = [(CONCEPT_CHECKS, "cpp_core"), (CPP_BACKEND_CONCEPT, "cpp_core"), (HTML_CSS_CONCEPT, "html_css")]


def seed_content(db: Session) -> None:
    existing_questions = {(t, q) for (t, q) in db.query(models.QuizQuestion.track, models.QuizQuestion.question).all()}
    for items, default_track in QUIZ_SOURCES:
        for item in items:
            item = {**item, "track": item.get("track", default_track)}
            if (item["track"], item["question"]) in existing_questions:
                continue
            db.add(models.QuizQuestion(**item))

    existing_titles = {(t, title) for (t, title) in db.query(models.CodingProblem.track, models.CodingProblem.title).all()}
    for items, default_track in CODING_SOURCES:
        for item in items:
            item = {**item, "track": item.get("track", default_track)}
            if (item["track"], item["title"]) in existing_titles:
                continue
            db.add(models.CodingProblem(**item))

    existing_prompts = {(t, p) for (t, p) in db.query(models.ConceptCheck.track, models.ConceptCheck.prompt).all()}
    for items, default_track in CONCEPT_SOURCES:
        for item in items:
            item = {**item, "track": item.get("track", default_track)}
            if (item["track"], item["prompt"]) in existing_prompts:
                continue
            db.add(models.ConceptCheck(**item))

    db.commit()
