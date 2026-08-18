from datetime import date as date_type, datetime

from pydantic import BaseModel, ConfigDict


class QuizQuestionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    topic: str
    question: str
    choices: list[str]
    # correct_index intentionally omitted - not sent to the client until graded


class DocLink(BaseModel):
    label: str
    url: str


class CodingProblemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str
    starter_code: str
    test_case_summary: str
    docs: list[DocLink] = []


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
    uses_sandbox: bool


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
    coding_completed: bool
    coding_attempts: int
    concept_completed: bool
    concept_self_rating: bool
    points_earned: float
    completed_at: datetime | None
    fully_completed: bool
    is_late: bool = False  # set by the router, not stored directly on the row


class ChallengeOut(BaseModel):
    day: DayOut
    quiz: list[QuizQuestionOut]
    coding: CodingProblemOut
    concept: ConceptCheckOut


class QuizSubmitIn(BaseModel):
    answers: dict[int, int]  # question_id -> chosen_index


class QuizSubmitOut(BaseModel):
    correct: int
    total: int
    points_awarded: float
    results: dict[int, bool]
    explanations: dict[int, str]
    # Revealed only now that the quiz is graded - lets the UI highlight the
    # correct choice, not just whether the user's pick was right.
    correct_indices: dict[int, int]


class CodeSubmitIn(BaseModel):
    code: str


class CodeSubmitOut(BaseModel):
    passed: bool
    tests_passed: int
    tests_total: int
    output: str
    error: str
    points_awarded: float
    # Only set for non-sandboxed tracks (see config.TRACKS) - the reference
    # solution to compare your own attempt against, revealed after submitting.
    reference_solution: str | None = None


class ConceptSubmitIn(BaseModel):
    self_rating_correct: bool


class ConceptSubmitOut(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    model_answer: str
    points_awarded: float


class CodeBlocksOut(BaseModel):
    # Shuffled lines of the reference solution, for the optional Duolingo-style
    # "assemble the code" mobile mode - see routers/coding.py. Only fetched
    # when the user turns that mode on; a plain ChallengeOut never includes it.
    lines: list[str]


class ConceptGradeIn(BaseModel):
    notes: str


class ConceptGradeOut(BaseModel):
    correct: bool
    feedback: str


class AppConfigOut(BaseModel):
    ai_grading_enabled: bool


class StatsOut(BaseModel):
    total_points: float
    current_streak: int
    longest_streak: int
    days_completed: int
    days_missed_open: int  # past days not yet fully completed
