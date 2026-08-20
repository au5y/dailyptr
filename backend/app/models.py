from datetime import datetime, date as date_type

from sqlalchemy import String, Integer, Float, Boolean, Date, DateTime, JSON, ForeignKey, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base


class User(Base):
    """Identity comes entirely from Google (see app/auth.py) - no password of
    our own to store. google_sub is Google's stable, unique per-account
    identifier (the ID token's `sub` claim) - the actual lookup key; email is
    kept for display and is unique because Google itself guarantees that."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    google_sub: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    # False right after signup until the topic-selection screen is completed
    # (see routers/challenges.py:/api/onboarding). Existing accounts from
    # before this field existed are backfilled to True - see database.py.
    onboarded: Mapped[bool] = mapped_column(Boolean, default=False)


class TrackSubscription(Base):
    """A user's opt-in to one track, and the date that opt-in happened. That
    date is the user's "start line" for that track: day_service/scoring use
    it to tell a genuinely missed day (on/after subscribing) apart from a
    backfilled "bonus" day from before they ever signed up for the track."""

    __tablename__ = "track_subscriptions"
    __table_args__ = (UniqueConstraint("user_id", "track", name="uq_track_subscriptions_user_track"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    track: Mapped[str] = mapped_column(String(32), index=True)
    subscribed_at: Mapped[date_type] = mapped_column(Date, default=date_type.today)


class MilestoneAward(Base):
    """A one-time record that a user's current streak on a track reached a
    given threshold (see config.STREAK_MILESTONES) - the badge/bonus-points
    unlock. Unique on (user_id, track, milestone) so it's only ever awarded
    once, even if the streak later resets and climbs back past the same
    threshold again - see scoring.award_new_milestones."""

    __tablename__ = "milestone_awards"
    __table_args__ = (UniqueConstraint("user_id", "track", "milestone", name="uq_milestone_awards_user_track_milestone"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    track: Mapped[str] = mapped_column(String(32), index=True)
    milestone: Mapped[int] = mapped_column(Integer)  # streak length threshold, e.g. 7
    points_awarded: Mapped[float] = mapped_column(Float, default=0.0)
    awarded_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


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


class CodeReviewChallenge(Base):
    """A ~20-30 line snippet seeded with 1-3 bugs/smells (correctness,
    security, a real anti-pattern). Objectively graded: the user clicks the
    line(s) they think are buggy and matches each to a reason from an answer
    bank - see routers/code_review.py.

    `issues` is a JSON list of {"line": int (1-indexed into `snippet`),
    "reason": str (short tag, matched against via the answer bank),
    "explanation": str (longer text revealed after grading)}. `distractor_
    reasons` is a JSON list of plausible-but-wrong short tags mixed in with
    the real ones to build the answer bank the client is shown - see
    schemas.CodeReviewChallengeOut.reason_bank."""

    __tablename__ = "code_review_challenges"

    id: Mapped[int] = mapped_column(primary_key=True)
    track: Mapped[str] = mapped_column(String(32), index=True, default="cpp_core")
    difficulty: Mapped[str] = mapped_column(String(16), index=True)
    topic: Mapped[str] = mapped_column(String(64))
    title: Mapped[str] = mapped_column(String(128))
    snippet: Mapped[str] = mapped_column(Text)  # the broken code to review
    issues: Mapped[list] = mapped_column(JSON)  # list[{"line", "reason", "explanation"}]
    distractor_reasons: Mapped[list] = mapped_column(JSON, default=list)  # list[str]


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
    __table_args__ = (UniqueConstraint("user_id", "date", "track", name="uq_days_user_date_track"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    date: Mapped[date_type] = mapped_column(Date, index=True)
    track: Mapped[str] = mapped_column(String(32), index=True, default="cpp_core")
    weekday: Mapped[int] = mapped_column(Integer)  # 0=Mon .. 6=Sun
    difficulty: Mapped[str] = mapped_column(String(16))

    quiz_question_ids: Mapped[list] = mapped_column(JSON)  # list[int]
    code_review_challenge_id: Mapped[int] = mapped_column(ForeignKey("code_review_challenges.id"))
    concept_check_id: Mapped[int] = mapped_column(ForeignKey("concept_checks.id"))

    quiz_completed: Mapped[bool] = mapped_column(Boolean, default=False)
    quiz_correct: Mapped[int] = mapped_column(Integer, default=0)
    quiz_total: Mapped[int] = mapped_column(Integer, default=0)
    # question_id (as str, JSON keys are always strings) -> chosen choice index.
    # Answering a question writes/overwrites its entry here immediately; the
    # quiz as a whole finalizes (quiz_completed, scoring) once every id in
    # quiz_question_ids has an entry - see routers/quiz.py.
    quiz_answers: Mapped[dict] = mapped_column(JSON, default=dict)

    code_review_completed: Mapped[bool] = mapped_column(Boolean, default=False)
    code_review_correct: Mapped[int] = mapped_column(Integer, default=0)
    code_review_total: Mapped[int] = mapped_column(Integer, default=0)

    concept_completed: Mapped[bool] = mapped_column(Boolean, default=False)
    concept_self_rating: Mapped[bool] = mapped_column(Boolean, default=False)

    points_earned: Mapped[float] = mapped_column(Float, default=0.0)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    @property
    def fully_completed(self) -> bool:
        return self.quiz_completed and self.code_review_completed and self.concept_completed
