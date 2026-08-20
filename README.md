# dailyptr

A self-hosted daily practice app, sharable with friends: a short
multiple-choice quiz, a small coding problem that compiles and runs your
real C++ in a sandbox, and a self-graded concept check. Difficulty ramps
from easy on Monday to expert on Sunday. Points and a daily streak track
your progress, and any day you miss stays open - a calendar and list view
in History let you jump back and catch up later. Everyone who signs in gets
their own independent progress.

See [`PLAN.md`](./PLAN.md) for the phased roadmap this scaffold is step one of.

> **Note:** this project is mostly "vibe coded" - built quickly with heavy AI
> assistance and comparatively light manual review. Treat it as a personal
> tool rather than a hardened, audited codebase.

## Accounts

Everyone gets their own progress: sign in with Google, or tap **Play
offline** on the login page to get a disposable local account with no
Google identity attached (still saved server-side, just not tied to any
account - see `backend/app/auth.py`). There's no password auth of any
kind. See [Configuration](#configuration) for the env vars a real Google
sign-in needs; without them the Google button won't work but Play offline
always does.

## Tracks

The app supports multiple independent daily-challenge tracks, switchable from
the topbar - each has its own content pool, quiz/code/concept flow, and its
own streak/points, all scoped per-account (see `backend/app/config.py: TRACKS`):

- **C++ Core** (`cpp_core`) - general C++ language, STL, and OOD/design-pattern
  questions, plus backend-service-flavored content (HTTP semantics, caching,
  rate limiting, load balancing, distributed systems) bundled into the same
  pool for variety - all real, compiled coding problems.
- **Learning HTML/CSS** (`html_css`) - no compiler for markup/styles, so this
  track's "coding" step is self-checked: you submit your attempt and the
  reference solution is revealed to compare against, instead of a pass/fail
  test run (see `uses_sandbox` in `config.TRACKS` and `routers/coding.py`).
- **System Design** (`system_design`) - same self-checked pattern as
  `html_css` (submit a free-text design attempt, compare against a revealed
  reference solution); the deepest content pool of the three tracks.

Each day can be reset from the "Reset day" button next to the difficulty
badge, if you want to retry the same quiz/code/concept check (it's the same
content - selection is deterministic per date+track - just with progress and
points for that day cleared). The Code tab also has an optional "Block mode"
toggle (off by default) that swaps the free-text editor for Duolingo-style
tappable pieces of the reference solution, shuffled, for assembling the
answer instead of typing it - handy on mobile.

## How it's built

- **Backend**: FastAPI + SQLAlchemy + Postgres (`backend/`), schema managed
  by Alembic migrations (`backend/alembic/`) run automatically on startup.
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
docker compose up -d
```

Then open http://localhost:8000. This brings up a `postgres` service
alongside `web` - data persists in a named Docker volume
(`dailyptr_pg_data`), not a host path. Set `POSTGRES_PASSWORD` (e.g. via
`.env` in this directory - see [Configuration](#configuration)) to a real
random value for anything beyond local dev; it falls back to an insecure
default otherwise. This mode runs every code submission inside a throwaway,
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
| `DATABASE_URL` | SQLAlchemy URL - `docker-compose.yml` points this at the `postgres` service; defaults to a local SQLite file when unset (e.g. running without Docker) |
| `POSTGRES_PASSWORD` | Password for the `postgres` service's `dailyptr` user in `docker-compose.yml` - set a real random value (e.g. `openssl rand -hex 20`) for any real deployment |
| `SANDBOX_MODE` | `docker` (default in compose) or `subprocess` (default locally) |
| `SANDBOX_IMAGE` | Image tag used for the docker sandbox backend |
| `SANDBOX_TIMEOUT_SECONDS` | Compile+run wall-clock limit per submission |
| `SANDBOX_MEMORY_LIMIT` / `SANDBOX_CPU_LIMIT` | Docker resource limits per submission |
| `SANDBOX_TMP_DIR` / `SANDBOX_HOST_TMP_DIR` | Docker-outside-of-Docker path translation for the sandbox's bind mount - already wired up in `docker-compose.yml`, only relevant if you change that setup |
| `FRONTEND_DIR` | Override where static frontend files are served from |
| `ANTHROPIC_API_KEY` | Optional. If set, enables AI-grading of concept-check free responses via the Anthropic API. Unset -> falls back to the plain self-graded "Got it / Missed it" flow |
| `ANTHROPIC_MODEL` | Model used for AI grading, defaults to a cheap Haiku model |
| `SECRET_KEY` | Signs login session cookies. Set a real random value (e.g. `openssl rand -hex 32`) for any real deployment - the default is fine for local dev/tests only |
| `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` | From a Google Cloud Console OAuth Client (type: Web application) - required for the "Sign in with Google" button to work. Register both your deployed callback URL and `http://localhost:8000/auth/google/callback` as authorized redirect URIs on it (Google allows plain-http `localhost` for dev even on a Web application client) |
| `GOOGLE_REDIRECT_URI` | Only needed if the app can't correctly infer its own public callback URL - e.g. mounted under a path prefix (`/dailyptr/`) behind a reverse proxy. Set it to the exact full URL registered in Google Cloud Console |

## Adding content

Each track's quiz/coding/concept banks live as plain Python data in
`backend/app/content/`: `quiz_bank.py` / `coding_bank.py` / `concept_bank.py`
for `cpp_core`, `cpp_backend_bank.py` for `cpp_backend`, and
`html_css_bank.py` for `html_css`. Append an entry in the same shape as the
existing ones in the relevant file, tagged with a `difficulty` of
`easy` / `medium` / `hard` / `expert`. Restart the app (or re-run seeding)
and it's picked up automatically - `seed_content()` only inserts entries not
already in the DB (keyed by track + text), so this is always safe to re-run.
Coding problems for sandboxed tracks (`cpp_core`, `cpp_backend`) are the most
involved to add because you write the test harness yourself (see the
docstring at the top of `coding_bank.py`); for the non-sandboxed `html_css`
track, a "coding" entry needs a `reference_solution` instead of a
`harness_template`. Quiz questions and concept checks are just data either
way. To add a whole new track, add it to `config.TRACKS` and give it its own
bank file(s) wired into `seed.py`.

## Security note

Every account's data is isolated (each `Day` row is scoped to the account
that owns it), and the Docker sandbox mode gives real isolation for the C++
execution itself (no network, dropped capabilities, resource limits). That
said, this is still a small self-hosted project built for friends to share,
not an audited multi-tenant service - treat it accordingly if you expose it
beyond people you trust.
