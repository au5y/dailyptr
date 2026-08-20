"""
App-wide configuration and the core "weekday -> difficulty" rule that drives
the whole daily-ramp concept: Monday starts easy, Sunday is the hardest.
"""
import os
from enum import Enum


class Difficulty(str, Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"
    EXPERT = "expert"


# Python's date.weekday(): Monday=0 ... Sunday=6
WEEKDAY_DIFFICULTY = {
    0: Difficulty.EASY,     # Monday
    1: Difficulty.EASY,     # Tuesday
    2: Difficulty.MEDIUM,   # Wednesday
    3: Difficulty.MEDIUM,   # Thursday
    4: Difficulty.HARD,     # Friday
    5: Difficulty.HARD,     # Saturday
    6: Difficulty.EXPERT,   # Sunday
}

# Multiplies base point values for quiz/coding/concept components.
DIFFICULTY_POINT_MULTIPLIER = {
    Difficulty.EASY: 1.0,
    Difficulty.MEDIUM: 1.5,
    Difficulty.HARD: 2.0,
    Difficulty.EXPERT: 3.0,
}

BASE_POINTS_PER_QUIZ_QUESTION = 10
BASE_POINTS_PER_CODE_REVIEW = 50  # also the base value for Critical Reasoning Review - same formula, see scoring.points_for_code_review
BASE_POINTS_PER_CONCEPT_CHECK = 15
ON_TIME_STREAK_BONUS = 5  # awarded only when a day is completed on its own date

# Streak milestone badges (see models.MilestoneAward, scoring.award_new_milestones):
# a one-time bonus the first time a user's current streak (per track) reaches
# each threshold. Awarded once per (user, track, milestone) - never re-awarded
# even if the streak later resets and climbs back past it.
STREAK_MILESTONES = [3, 7, 14, 30, 60, 100, 200, 365]
STREAK_MILESTONE_BONUS = {
    3: 20.0, 7: 50.0, 14: 100.0, 30: 250.0, 60: 500.0, 100: 1000.0, 200: 2500.0, 365: 5000.0,
}

QUESTIONS_PER_DAY = 3

# A "track" is an independent daily-challenge subject: its own content pool,
# its own Day rows (keyed by (date, track)), its own streak/points via
# scoring.compute_stats(db, track). Every track is self-checked (no compiler
# involved) - see routers/code_review.py.
#
# "review_kind" picks which required review step a track uses - "code"
# (Code Review, routers/code_review.py) for tracks with literal code, or
# "reasoning" (Critical Reasoning Review, routers/critical_reasoning.py) for
# tracks that are prose/tradeoff-thinking-first. A Day only ever populates
# the one FK/completion trio matching its track's review_kind - see
# models.Day.fully_completed and day_service.py.
DEFAULT_TRACK = "cpp_core"
TRACKS = {
    "cpp_core": {"name": "C++ Core", "review_kind": "code"},
    "html_css": {"name": "Learning HTML/CSS", "review_kind": "code"},
    "system_design": {"name": "System Design", "review_kind": "reasoning"},
}

DATABASE_URL = os.environ.get(
    "DATABASE_URL", f"sqlite:///{os.path.dirname(os.path.dirname(os.path.abspath(__file__)))}/local.db"
)

# Optional: AI grading of concept-check free responses via the Anthropic API.
# Unset -> the app falls back to the plain self-graded "Got it / Missed it" flow.
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
ANTHROPIC_MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-haiku-4-5-20251001")

# Signs per-user session cookies (see app/auth.py). Set a real random value
# in production (e.g. `openssl rand -hex 32`) - the fallback below is fine
# for local dev/tests but means sessions won't survive a code change that
# regenerates it, and anyone with the source can forge cookies.
SECRET_KEY = os.environ.get("SECRET_KEY") or "dev-only-insecure-secret-key"

# Google OAuth ("Sign in with Google" - see app/auth.py) - the app has no
# password auth of its own. Get these from a Google Cloud Console OAuth
# Client (type: Web application); register BOTH your deployed callback URL
# and http://localhost:8000/auth/google/callback as authorized redirect
# URIs on the same client (Google allows a plain-http localhost redirect
# for dev even on a "Web application" client, no separate client needed).
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", "")
# Only needed if the app can't correctly infer its own public URL (e.g.
# behind a reverse proxy that doesn't forward scheme/host) - otherwise the
# callback URL is derived from the incoming request.
GOOGLE_REDIRECT_URI = os.environ.get("GOOGLE_REDIRECT_URI", "")
