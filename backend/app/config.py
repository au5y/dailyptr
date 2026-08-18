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
