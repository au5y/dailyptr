from datetime import date as date_type, datetime

from pydantic import BaseModel, ConfigDict


class QuizQuestionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    topic: str
    question: str
    choices: list[str]
    # correct_index intentionally omitted - not sent to the client until graded


class CodeReviewChallengeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    snippet: str
    # Shuffled: the real reason for every issue in the snippet, plus decoys -
    # built by the router, not stored directly on the model. Which entries
    # are real vs. decoy, and which line each real one belongs to, are
    # intentionally not sent until graded.
    reason_bank: list[str]


class CriticalReasoningChallengeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    passage: str
    # Same shuffled-answer-bank shape as CodeReviewChallengeOut.reason_bank.
    reason_bank: list[str]


class ConceptCheckOut(BaseModel):
    # protected_namespaces=() silences Pydantic's "model_*" field name warning -
    # model_answer here means "the reference answer", nothing to do with ML models.
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())

    id: int
    prompt: str
    # Self-graded, not multiple choice, so there's no "cheating" risk in
    # sending the model answer up front - the reveal button just delays
    # showing it in the UI until the user has written their own attempt.
    model_answer: str


class TrackOut(BaseModel):
    id: str
    name: str
    review_kind: str  # "code" or "reasoning" - see config.TRACKS
    subscribed: bool = False


class OnboardingIn(BaseModel):
    tracks: list[str]


class SubscribeIn(BaseModel):
    track: str


class DayOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    date: date_type
    track: str
    weekday: int
    difficulty: str
    quiz_completed: bool
    quiz_correct: int
    quiz_total: int
    code_review_completed: bool
    code_review_correct: int
    code_review_total: int
    critical_reasoning_completed: bool
    critical_reasoning_correct: int
    critical_reasoning_total: int
    concept_completed: bool
    concept_self_rating: bool
    points_earned: float
    completed_at: datetime | None
    fully_completed: bool
    is_late: bool = False  # set by the router, not stored directly on the row
    is_bonus: bool = False  # set by the router - day predates the user's subscription to this track


class ChallengeOut(BaseModel):
    day: DayOut
    quiz: list[QuizQuestionOut]
    # Exactly one of these two is populated, depending on the day's track's
    # review_kind (see config.TRACKS) - the other is null.
    code_review: CodeReviewChallengeOut | None = None
    critical_reasoning: CriticalReasoningChallengeOut | None = None
    concept: ConceptCheckOut


class VirtualDayOut(BaseModel):
    """A day's shape for a guest content fetch (routers/guest.py) - no
    persisted Day row exists, so there's no id/points_earned/completed_at/
    fully_completed the way DayOut has - just the deterministic (date, track)
    facts day_service.select_day_content computes."""

    date: date_type
    track: str
    weekday: int
    difficulty: str


class GuestChallengeOut(BaseModel):
    day: VirtualDayOut
    quiz: list[QuizQuestionOut]
    code_review: CodeReviewChallengeOut | None = None
    critical_reasoning: CriticalReasoningChallengeOut | None = None
    concept: ConceptCheckOut


class QuizAnswerIn(BaseModel):
    choice_index: int


class QuizAnswerOut(BaseModel):
    correct: bool
    correct_index: int
    explanation: str
    # True once every question in the quiz has been answered - the point at
    # which the quiz as a whole is scored and locked.
    quiz_completed: bool
    quiz_correct: int
    quiz_total: int
    points_awarded: float
    # Streak milestones (config.STREAK_MILESTONES) newly reached by this
    # submission, if it's the one that finished the day - usually empty.
    milestones_hit: list[int] = []


class ConceptSubmitIn(BaseModel):
    self_rating_correct: bool


class ConceptSubmitOut(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    model_answer: str
    points_awarded: float
    milestones_hit: list[int] = []


class ConceptGradeIn(BaseModel):
    notes: str


class ConceptGradeOut(BaseModel):
    correct: bool
    feedback: str


class CodeReviewMatchIn(BaseModel):
    line: int
    reason: str


class CodeReviewSubmitIn(BaseModel):
    # One entry per line the user flagged, each paired with the reason they
    # picked for it from CodeReviewChallengeOut.reason_bank.
    matches: list[CodeReviewMatchIn]


class CodeReviewIssueResult(BaseModel):
    line: int
    reason: str
    explanation: str
    # Whether the user flagged this line at all, and (if so) whether the
    # reason they matched to it was the right one.
    line_found: bool
    reason_correct: bool


class CodeReviewSubmitOut(BaseModel):
    correct_count: int
    total: int
    results: list[CodeReviewIssueResult]
    points_awarded: float
    milestones_hit: list[int] = []


class CriticalReasoningMatchIn(BaseModel):
    line: int
    reason: str


class CriticalReasoningSubmitIn(BaseModel):
    matches: list[CriticalReasoningMatchIn]


class CriticalReasoningIssueResult(BaseModel):
    line: int
    reason: str
    explanation: str
    line_found: bool
    reason_correct: bool


class CriticalReasoningSubmitOut(BaseModel):
    correct_count: int
    total: int
    results: list[CriticalReasoningIssueResult]
    points_awarded: float
    milestones_hit: list[int] = []


class GuestQuizAnswerIn(BaseModel):
    date: date_type
    track: str
    question_id: int
    choice_index: int


class GuestQuizAnswerOut(BaseModel):
    """Deliberately no quiz_completed/points_awarded - a stateless single-
    question grade doesn't know whether this was the day's last question
    (that's client-side accumulated state, see frontend Progress module,
    not built yet); the client computes quiz points itself from
    AppConfigOut.scoring once every question in the day is answered."""

    correct: bool
    correct_index: int
    explanation: str


class GuestReviewCheckIn(BaseModel):
    date: date_type
    track: str
    matches: list[CodeReviewMatchIn]


class GuestConceptScoreIn(BaseModel):
    date: date_type
    track: str
    self_rating_correct: bool


class GuestConceptScoreOut(BaseModel):
    points_awarded: float


class ScoringConfigOut(BaseModel):
    """The scoring constants needed to compute guest quiz points client-side
    (routers/guest.py's stateless quiz endpoint deliberately doesn't return
    points_awarded - see its docstring). Point arithmetic is a deterministic
    formula, not a security-sensitive judgment (correctness itself is always
    server-checked); it's also recomputed authoritatively at claim time."""

    base_quiz: float
    base_concept: float
    on_time_bonus: float
    difficulty_multipliers: dict[str, float]


class AppConfigOut(BaseModel):
    ai_grading_enabled: bool
    scoring: ScoringConfigOut


class MeOut(BaseModel):
    email: str
    name: str
    onboarded: bool
    is_guest: bool


class StatsOut(BaseModel):
    total_points: float
    current_streak: int
    longest_streak: int
    days_completed: int
    days_missed_open: int  # past days not yet fully completed
    badges: list[int]  # streak milestones (config.STREAK_MILESTONES) earned on this track


class ClaimSubscriptionIn(BaseModel):
    track: str
    # The guest's original local subscribe date - preserved (not "today") so
    # a claimed day's is_late/is_bonus classification stays consistent with
    # what the guest actually saw locally. Ignored if the account already
    # has a subscription for this track (existing wins - see ClaimOut).
    subscribed_at: date_type


class ClaimDayIn(BaseModel):
    track: str
    date: date_type
    quiz_answers: dict[str, int] = {}  # question_id (str) -> choice_index, whatever was accumulated locally
    code_review_matches: list[CodeReviewMatchIn] | None = None
    critical_reasoning_matches: list[CriticalReasoningMatchIn] | None = None
    concept_self_rating: bool | None = None


class ClaimIn(BaseModel):
    subscriptions: list[ClaimSubscriptionIn] = []
    days: list[ClaimDayIn] = []


class ClaimOut(BaseModel):
    claimed_days: list[DayOut]
    skipped_days: list[dict]  # [{"track": ..., "date": ..., "reason": ...}]
    claimed_subscriptions: list[str]  # track ids newly subscribed
    skipped_subscriptions: list[str]  # already subscribed - left untouched
