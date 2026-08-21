# Roadmap: dailyptr

Source requirement: a daily learning app that verifies C++/software
programming/OOD/design-pattern knowledge (now broadened to more tracks) via
a short multiple-choice quiz, a code-review-style exercise, and a
free-response concept check - getting harder from easy Monday to difficult
Sunday, with the ability to go back on missed days, points as you go, and
self-hosted.

## Shipped

- **Core loop**: FastAPI + Postgres (Alembic migrations) backend, vanilla
  JS/HTML/CSS frontend, weekday->difficulty ramp (easy Mon/Tue, medium
  Wed/Thu, hard Fri/Sat, expert Sun), points/streaks, go-back-on-missed-days
  calendar/history view, deterministic per-`(date, track)` content selection.
- **Three tracks**, switchable from the topbar, each with its own content
  pool and independent streak/points: **C++ Core** (`cpp_core`),
  **Learning HTML/CSS** (`html_css`), **System Design** (`system_design` -
  interdisciplinary design/tradeoff thinking, not just software case
  studies). Adding a track = a content-bank file + `config.TRACKS` entry.
- **Three daily components per track**: a multiple-choice quiz, a
  click-to-flag-then-match review exercise (Code Review for `cpp_core`/
  `html_css`, Critical Reasoning Review for `system_design` - same
  mechanic, prose flaws instead of code bugs), and a free-response concept
  check. All self-checked, objectively graded server-side where possible -
  no compiled/sandboxed code execution (removed; PaaS hosting doesn't offer
  a Docker socket, and it added ~10s/submission latency).
- **Accounts**: Google OAuth sign-in (no passwords), plus a "Play offline"
  guest mode whose progress lives in `localStorage` only and claims into a
  real account on first real sign-in (existing account data always wins on
  conflict).
- **Streak milestone badges**: awarded once per `(user, track, milestone)`
  at 3/7/14/30/60/100/200/365-day streaks, but not yet visible anywhere
  persistent (no profile page exists to show them).
- **Deployed**: live on Railway, reverse-proxied at `au5y.dev/daily`.
  Google OAuth was broken in prod for a bit (fixed 2026-08-20).
- **Content depth**: `system_design` is deepest (87 entries, 30-day
  history backfilled). `cpp_core`/`html_css` got a first growth pass
  2026-08-20 (concept/code-review now 4-5 entries per difficulty tier) but
  aren't yet deep enough to avoid repeats within a month - see MVP below.

Full narrative/decision history for the above lives in git log, not here.

## Remaining for MVP

- [ ] **`cpp_core`/`html_css` content depth**: grow concept-check and
  code-review pools (1 entry/day each) toward ~9 per easy/medium/hard tier
  and ~5 for expert, so a full month has no repeats. Quiz is lower
  priority (3 sampled/day already absorbs a smaller pool). Pure data entry
  in `backend/app/content/*.py`.
- [ ] **AI grading, safely**: turn on `ANTHROPIC_API_KEY` on Railway for
  the existing (currently-dark) concept-check AI-grade button - but only
  after adding a per-account usage cap (daily/weekly quota, 429 past it),
  since any Google sign-in can otherwise hit the endpoint unbounded once a
  real key is live.
- [ ] **Trim OAuth diagnostics**: the login page's `error=<reason>` detail
  was added to debug the Railway OAuth failure; now that it's fixed, trim
  it back to a generic message.

## Backlog (not MVP - revisit later)

- A profile page to actually surface streak badges.
- Stats page upgrade (topic-accuracy breakdown, points-over-time chart).
- Export history as JSON/CSV.
- Weekly recap summary.
- Spaced repetition (weight concept-check selection toward recently-missed
  topics) and weak-topic targeting for quizzes.
- Per-account leaderboard/comparison view.
- A `backend/app/repositories/` data-access layer between routers and the
  raw ORM (currently `db.query(...)` calls are scattered across
  `routers/*.py`/`day_service.py`/`scoring.py` - fine at this size, but a
  good practice project).
- More practice modalities (log/metrics investigation challenges,
  test-writing/mutation-testing exercises, git workflow drills) - ideas
  only, not designed.
- Freezes/streak-protection, an "at risk" reminder.

## Key decisions (for context, not up for relitigating)

- No compiled/sandboxed code execution - self-checked review exercises
  instead, for hosting portability and latency.
- OAuth (Google) + disposable guest accounts, no password auth of our own.
- Tracks share one app/schema (`(date, track)` keyed) rather than separate
  deployments per subject.
- Four difficulty tiers (easy/medium/hard/expert) mapped to weekday pairs,
  not a continuous per-weekday scale.
