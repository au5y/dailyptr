# dailyptr

A self-hosted daily practice app, sharable with friends: a short
multiple-choice quiz, a code review challenge (spot the bug/smell in a
snippet, self-report what you found, compare against an annotated answer
key), and a self-graded concept check. Difficulty ramps from easy on Monday
to expert on Sunday. Points and a daily streak track your progress, and any
day you miss stays open - a calendar and list view in History let you jump
back and catch up later. Everyone who signs in gets their own independent
progress.

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
the topbar - each has its own content pool, quiz/code-review/concept flow,
and its own streak/points, all scoped per-account (see
`backend/app/config.py: TRACKS`):

- **C++ Core** (`cpp_core`) - general C++ language, STL, and OOD/design-pattern
  questions, plus backend-service-flavored content (HTTP semantics, caching,
  rate limiting, load balancing, distributed systems) bundled into the same
  pool for variety.
- **Learning HTML/CSS** (`html_css`) - markup/style and vanilla-JS code
  review challenges (accessibility, XSS, layout smells) alongside its own
  quiz/concept content.
- **System Design** (`system_design`) - the same self-graded code-review
  shape, but each "snippet" is a short design note instead of literal code
  (a caching strategy, a sharding scheme, a retry policy) with a seeded
  design flaw; the deepest content pool of the three tracks.

Every track is fully self-checked now - there's no compiler or sandbox
involved anywhere in the app (see [How it's built](#how-its-built)). Each day
can be reset from the "Reset day" button next to the difficulty badge, if you
want to retry the same quiz/code-review/concept check (it's the same
content - selection is deterministic per date+track - just with progress and
points for that day cleared).

## How it's built

- **Backend**: FastAPI + SQLAlchemy + Postgres (`backend/`), schema managed
  by Alembic migrations (`backend/alembic/`) run automatically on startup.
- **Frontend**: plain HTML/CSS/JS, no build step (`frontend/`), served
  directly by the backend.
- **Content bank**: quiz questions, code review challenges, and concept
  checks live as plain Python data in `backend/app/content/*.py` - no admin
  UI needed to add more, just append entries and restart (seeding is
  idempotent).

## Running it (self-hosted, Docker)

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
default otherwise.

## Running it locally without Docker (dev mode)

Needs Python 3.11+.

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open http://localhost:8000. Defaults to a local SQLite file when
`DATABASE_URL` isn't set, so this needs nothing else running. It's also what
the automated test suite uses.

## Running the tests

```bash
cd backend
source .venv/bin/activate  # if not already active
python -m pytest tests/ -v
```

Covers: scoring/streak math and a full Monday-through-Sunday API walkthrough
(quiz -> code review -> concept check for each difficulty tier, verifying
points and completion state).

## Configuration

Environment variables (all optional, see `backend/app/config.py` for
defaults):

| Variable | Purpose |
|---|---|
| `DATABASE_URL` | SQLAlchemy URL - `docker-compose.yml` points this at the `postgres` service; defaults to a local SQLite file when unset (e.g. running without Docker) |
| `POSTGRES_PASSWORD` | Password for the `postgres` service's `dailyptr` user in `docker-compose.yml` - set a real random value (e.g. `openssl rand -hex 20`) for any real deployment |
| `FRONTEND_DIR` | Override where static frontend files are served from |
| `ANTHROPIC_API_KEY` | Optional. If set, enables AI-grading of concept-check and code-review free responses via the Anthropic API. Unset -> falls back to the plain self-graded "Got it / Missed it" flow |
| `ANTHROPIC_MODEL` | Model used for AI grading, defaults to a cheap Haiku model |
| `SECRET_KEY` | Signs login session cookies. Set a real random value (e.g. `openssl rand -hex 32`) for any real deployment - the default is fine for local dev/tests only |
| `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` | From a Google Cloud Console OAuth Client (type: Web application) - required for the "Sign in with Google" button to work. Register both your deployed callback URL and `http://localhost:8000/auth/google/callback` as authorized redirect URIs on it (Google allows plain-http `localhost` for dev even on a Web application client) |
| `GOOGLE_REDIRECT_URI` | Only needed if the app can't correctly infer its own public callback URL - e.g. mounted under a path prefix (`/dailyptr/`) behind a reverse proxy. Set it to the exact full URL registered in Google Cloud Console |

## Adding content

Each track's quiz/code-review/concept banks live as plain Python data in
`backend/app/content/`: `quiz_bank.py` / `code_review_bank.py` /
`concept_bank.py` for the base content, `cpp_backend_bank.py` bundled into
`cpp_core`, and `html_css_bank.py` / `system_design_bank.py` for those
tracks. Append an entry in the same shape as the existing ones in the
relevant file, tagged with a `difficulty` of `easy` / `medium` / `hard` /
`expert`. `code_review_bank.py`'s `CODE_REVIEW_CHALLENGES` is keyed by track
directly (`{track: [entries]}`) rather than needing a separate default-track
mapping in `seed.py`. Restart the app (or re-run seeding) and it's picked up
automatically - `seed_content()` only inserts entries not already in the DB
(keyed by track + text), so this is always safe to re-run. To add a whole
new track, add it to `config.TRACKS` and give it its own bank file(s) wired
into `seed.py`.

## Security note

Every account's data is isolated (each `Day` row is scoped to the account
that owns it). That said, this is still a small self-hosted project built
for friends to share, not an audited multi-tenant service - treat it
accordingly if you expose it beyond people you trust.
