from datetime import datetime, date as date_type

from sqlalchemy import String, Integer, Float, Boolean, Date, DateTime, JSON, ForeignKey, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base


class QuizQuestion(Base):
    __tablename__ = "quiz_questions"

    id: Mapped[int] = mapped_column(primary_key=True)
    track: Mapped[str] = mapped_column(String(32), index=True, default="cpp_core")
    difficulty: Mapped[str] = mapped_column(String(16), index=True)
    topic: Mapped[str] = mapped_column(String(64))
    question: Mapped[str] = mapped_column(Text)
    choices: Mapped[list] = mapped_column(JSON)  # list[str]
    correct_index: Mapped[int] = mapped_column(Integer)
    explanation: Mapped[str] = mapped_column(Text, default="")


class CodingProblem(Base):
    __tablename__ = "coding_problems"

    id: Mapped[int] = mapped_column(primary_key=True)
    track: Mapped[str] = mapped_column(String(32), index=True, default="cpp_core")
    difficulty: Mapped[str] = mapped_column(String(16), index=True)
    topic: Mapped[str] = mapped_column(String(64))
    title: Mapped[str] = mapped_column(String(128))
    description: Mapped[str] = mapped_column(Text)
    starter_code: Mapped[str] = mapped_column(Text)
    # harness_template contains the literal token {{USER_CODE}} where the
    # user's submitted code is spliced in before compiling. It embeds its
    # own test cases and prints "RESULT:<passed>/<total>" as the last line.
    # Only used for tracks with uses_sandbox=True (see config.TRACKS) - empty
    # for tracks like html_css that self-check instead of compiling.
    harness_template: Mapped[str] = mapped_column(Text, default="")
    test_case_summary: Mapped[str] = mapped_column(Text, default="")  # human-readable, shown to user
    # Curated cppreference.com (etc.) links relevant to this problem's topic,
    # e.g. [{"label": "std::string", "url": "https://en.cppreference.com/w/cpp/string/basic_string"}].
    docs: Mapped[list] = mapped_column(JSON, default=list)
    # Non-sandbox tracks only: a reference solution revealed after the user
    # submits their own attempt, instead of a compiled pass/fail (see
    # routers/coding.py). Never sent to the client before submission.
    reference_solution: Mapped[str] = mapped_column(Text, default="")


class ConceptCheck(Base):
    __tablename__ = "concept_checks"

    id: Mapped[int] = mapped_column(primary_key=True)
    track: Mapped[str] = mapped_column(String(32), index=True, default="cpp_core")
    difficulty: Mapped[str] = mapped_column(String(16), index=True)
    topic: Mapped[str] = mapped_column(String(64))
    prompt: Mapped[str] = mapped_column(Text)
    model_answer: Mapped[str] = mapped_column(Text)


class Day(Base):
    """One calendar day's worth of challenge content and the user's progress on it."""

    __tablename__ = "days"
    __table_args__ = (UniqueConstraint("date", "track", name="uq_days_date_track"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    date: Mapped[date_type] = mapped_column(Date, index=True)
    track: Mapped[str] = mapped_column(String(32), index=True, default="cpp_core")
    weekday: Mapped[int] = mapped_column(Integer)  # 0=Mon .. 6=Sun
    difficulty: Mapped[str] = mapped_column(String(16))

    quiz_question_ids: Mapped[list] = mapped_column(JSON)  # list[int]
    coding_problem_id: Mapped[int] = mapped_column(ForeignKey("coding_problems.id"))
    concept_check_id: Mapped[int] = mapped_column(ForeignKey("concept_checks.id"))

    quiz_completed: Mapped[bool] = mapped_column(Boolean, default=False)
    quiz_correct: Mapped[int] = mapped_column(Integer, default=0)
    quiz_total: Mapped[int] = mapped_column(Integer, default=0)

    coding_completed: Mapped[bool] = mapped_column(Boolean, default=False)
    coding_attempts: Mapped[int] = mapped_column(Integer, default=0)

    concept_completed: Mapped[bool] = mapped_column(Boolean, default=False)
    concept_self_rating: Mapped[bool] = mapped_column(Boolean, default=False)

    points_earned: Mapped[float] = mapped_column(Float, default=0.0)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    @property
    def fully_completed(self) -> bool:
        return self.quiz_completed and self.coding_completed and self.concept_completed


class CodeSubmission(Base):
    """Audit log of every code submission (also lets the sandbox module be tested independently)."""

    __tablename__ = "code_submissions"

    id: Mapped[int] = mapped_column(primary_key=True)
    day_id: Mapped[int] = mapped_column(ForeignKey("days.id"))
    problem_id: Mapped[int] = mapped_column(ForeignKey("coding_problems.id"))
    code: Mapped[str] = mapped_column(Text)
    passed: Mapped[bool] = mapped_column(Boolean, default=False)
    tests_passed: Mapped[int] = mapped_column(Integer, default=0)
    tests_total: Mapped[int] = mapped_column(Integer, default=0)
    output: Mapped[str] = mapped_column(Text, default="")
    error: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
