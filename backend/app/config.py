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
BASE_POINTS_PER_CODING_PROBLEM = 50
BASE_POINTS_PER_CONCEPT_CHECK = 15
ON_TIME_STREAK_BONUS = 5  # awarded only when a day is completed on its own date

QUESTIONS_PER_DAY = 3

# A "track" is an independent daily-challenge subject: its own content pool,
# its own Day rows (keyed by (date, track)), its own streak/points via
# scoring.compute_stats(db, track). "uses_sandbox" tracks compile/run real
# C++ through app/sandbox; others (currently html_css) get a self-check flow
# instead - see routers/coding.py.
DEFAULT_TRACK = "cpp_core"
TRACKS = {
    "cpp_core": {"name": "C++ Core", "uses_sandbox": True},
    "html_css": {"name": "Learning HTML/CSS", "uses_sandbox": False},
}

DATABASE_URL = os.environ.get(
    "DATABASE_URL", f"sqlite:///{os.path.dirname(os.path.dirname(os.path.abspath(__file__)))}/local.db"
)

# "docker"  -> spins up a real, network-disabled container per submission (production / self-hosted)
# "subprocess" -> compiles/runs with a locked-down local subprocess (local dev, no Docker daemon needed)
SANDBOX_MODE = os.environ.get("SANDBOX_MODE", "subprocess")
SANDBOX_IMAGE = os.environ.get("SANDBOX_IMAGE", "cpp-refresher-sandbox:latest")
SANDBOX_TIMEOUT_SECONDS = int(os.environ.get("SANDBOX_TIMEOUT_SECONDS", "10"))
SANDBOX_MEMORY_LIMIT = os.environ.get("SANDBOX_MEMORY_LIMIT", "128m")
SANDBOX_CPU_LIMIT = os.environ.get("SANDBOX_CPU_LIMIT", "0.5")

# Docker-outside-of-Docker path translation (only matters for SANDBOX_MODE=docker):
# this backend process's temp files live at SANDBOX_TMP_DIR *inside its own
# container*, but the `docker run -v <path>:/sandbox` it issues goes to the
# HOST daemon over the mounted socket, which resolves that path on the HOST
# filesystem - a container-local /tmp path means nothing there. docker-compose
# bind-mounts one real host directory at SANDBOX_TMP_DIR inside this container
# and also tells it that same directory's HOST-side absolute path via
# SANDBOX_HOST_TMP_DIR, so docker_runner.py can swap the prefix when building
# the mount flag. Leave SANDBOX_HOST_TMP_DIR unset if running the backend
# directly on the host (no translation needed - the path is the same on both
# "sides" because there's only one side).
SANDBOX_TMP_DIR = os.environ.get("SANDBOX_TMP_DIR") or None  # None -> tempfile's normal default
SANDBOX_HOST_TMP_DIR = os.environ.get("SANDBOX_HOST_TMP_DIR", "")

# Optional: AI grading of concept-check free responses via the Anthropic API.
# Unset -> the app falls back to the plain self-graded "Got it / Missed it" flow.
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
ANTHROPIC_MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-haiku-4-5-20251001")
