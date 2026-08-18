# C++ Daily Skill Refresher

A self-hosted daily practice app: a short multiple-choice quiz, a small
coding problem that compiles and runs your real C++ in a sandbox, and a
self-graded concept check. Difficulty ramps from easy on Monday to expert
on Sunday. Points and a daily streak track your progress, and any day you
miss stays open so you can go back and catch up later.

See [`PLAN.md`](./PLAN.md) for the phased roadmap this scaffold is step one of.

## How it's built

- **Backend**: FastAPI + SQLAlchemy + SQLite (`backend/`). One process, no
  external services required besides the sandbox.
- **Frontend**: plain HTML/CSS/JS, no build step (`frontend/`), served
  directly by the backend.
- **Sandbox**: each coding submission is compiled and run against a set of
  test cases, either in a disposable, network-disabled Docker container
  (`sandbox-runner/`, used in production) or as a resource-limited local
  subprocess (used for local dev without Docker). See
  `backend/app/sandbox/*.py` for the full tradeoffs.
- **Content bank**: quiz questions, coding problems, and concept checks live
  as plain Python data in `backend/app/content/*.py` - no admin UI needed to
  add more, just append entries and restart (seeding is idempotent).

## Running it (self-hosted, Docker - recommended)

Requires Docker and Docker Compose.

```bash
docker compose build
docker compose up web
```

Then open http://localhost:8000. Data persists in `./data/app.db` on the
host. This mode runs every code submission inside a throwaway,
network-disabled container built from `sandbox-runner/Dockerfile` - see the
comments in `docker-compose.yml` for how the backend reaches the host's
Docker daemon to do this ("Docker-outside-of-Docker").

## Running it locally without Docker (dev mode)

Needs Python 3.11+ and a `g++` on your PATH.

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
SANDBOX_MODE=subprocess uvicorn app.main:app --reload
```

Open http://localhost:8000. `SANDBOX_MODE=subprocess` compiles/runs
submissions directly on your machine with basic CPU/memory rlimits instead
of Docker - fine for local development, not a real sandbox (see
`backend/app/sandbox/subprocess_runner.py`). It's also what the automated
test suite uses, so it doesn't need a Docker daemon to run.

## Running the tests

```bash
cd backend
source .venv/bin/activate  # if not already active
python -m pytest tests/ -v
```

Covers: scoring/streak math, the sandbox grader against every seeded coding
problem (correct solution, incomplete starter code, invalid C++, and an
infinite loop - each exercised for real, not mocked), and a full
Monday-through-Sunday API walkthrough (quiz -> code -> concept check for
each difficulty tier, verifying points and completion state).

## Configuration

Environment variables (all optional, see `backend/app/config.py` for
defaults):

| Variable | Purpose |
|---|---|
| `DATABASE_URL` | SQLAlchemy URL, defaults to a local SQLite file |
| `SANDBOX_MODE` | `docker` (default in compose) or `subprocess` (default locally) |
| `SANDBOX_IMAGE` | Image tag used for the docker sandbox backend |
| `SANDBOX_TIMEOUT_SECONDS` | Compile+run wall-clock limit per submission |
| `SANDBOX_MEMORY_LIMIT` / `SANDBOX_CPU_LIMIT` | Docker resource limits per submission |
| `FRONTEND_DIR` | Override where static frontend files are served from |
| `ANTHROPIC_API_KEY` | Optional. If set, enables AI-grading of concept-check free responses via the Anthropic API. Unset -> falls back to the plain self-graded "Got it / Missed it" flow |
| `ANTHROPIC_MODEL` | Model used for AI grading, defaults to a cheap Haiku model |

## Adding content

Open `backend/app/content/quiz_bank.py`, `coding_bank.py`, or
`concept_bank.py` and append an entry in the same shape as the existing
ones, tagged with a `difficulty` of `easy` / `medium` / `hard` / `expert`.
Restart the app (or re-run seeding) and it's picked up automatically -
`seed_content()` only inserts entries that aren't already in the DB, so this
is always safe to re-run. Coding problems are the most involved to add
because you write the test harness yourself (see the docstring at the top
of `coding_bank.py`); quiz questions and concept checks are just data.

## Security note

This is designed to be run by one person, on their own machine or private
network - there's intentionally no login (see `PLAN.md` for why, and what
it'd take to add one). The Docker sandbox mode gives real isolation for the
C++ execution itself (no network, dropped capabilities, resource limits),
but the app has no authentication layer, so don't expose it to the public
internet without adding one first.
