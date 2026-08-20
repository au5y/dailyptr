# Roadmap: dailyptr

Source requirement (from the project description): a daily learning app that
verifies and tests C++, software programming, OOD, and design pattern
knowledge via a short multiple-choice quiz, a small coding problem that runs
in a sandbox, and other knowledge checks - getting harder from easy Monday
to difficult Sunday, with the ability to go back on missed days, points as
you go, and fully self-hosted.

## Phase 0 - Scaffold (done)

The original vertical slice: FastAPI + SQLite backend (`Day`, `QuizQuestion`,
`CodingProblem`, `ConceptCheck`, `CodeSubmission`), weekday->difficulty
ramp, a seeded content bank, real sandboxed C++ execution (Docker or
subprocess backend), points/streak scoring, a "go back on missed days"
model, a minimal vanilla JS/HTML/CSS frontend, and an automated test suite.
Single-user, no-auth, Docker Compose deployment. See git history for detail
- this section is kept short since everything in it has since been revised.

## Phase 1 - Redesign, mobile, and multi-track content (done)

Everything below shipped and was verified with real interaction tests
(Playwright driving actual clicks/taps against the running app, not just
screenshots) plus the existing pytest suite.

- **Visual redesign**: Solarized-dark palette, watercolor background blobs,
  a Duolingo-style skill-tree node nav (Quiz/Code/Concept) replacing plain
  tabs, a mascot flame with contextual messages, chunky 3D-press buttons.
  Implemented from a Claude Design `.dc.html` spec the user authored/edited.
- **Tracks**: the app now supports more than one independent daily-challenge
  subject, switchable from the topbar, each with its own content pool and
  its own streak/points (`Day` etc. are keyed by `(date, track)` - see
  `backend/app/config.py: TRACKS`).
  - **C++ Core** (`cpp_core`) - the original C++/STL/OOD/design-pattern
    content, plus backend-service-flavored content (HTTP semantics, caching,
    rate limiting, load balancing, distributed systems) that was briefly its
    own "C++ Backend" track and is now bundled into this same pool for
    variety (`content/coding_bank.py`, `quiz_bank.py`, `concept_bank.py`,
    `cpp_backend_bank.py`).
  - **Learning HTML/CSS** (`html_css`) - no compiler for markup/styles, so
    its "coding" step is self-checked instead of compiled: submit an
    attempt, get the reference solution revealed to compare against
    (`content/html_css_bank.py`, `uses_sandbox` in `config.TRACKS`).
  - Adding a third track means: a bank file with quiz/coding/concept lists
    tagged with the new track id, wiring it into `seed.py`'s source lists,
    and adding it to `config.TRACKS`.
- **Calendar view** (this was Phase 3's top item, done early): a month-grid
  toggle alongside the existing list in History, colored by day status,
  works for days never opened yet (creates them on click, same as the list).
- **Reset day**: a button next to the difficulty badge that clears one day's
  progress/points (same content - selection is deterministic per
  date+track) so you can retry it.
- **Block mode**: an optional, off-by-default toggle on the Code tab that
  swaps the free-text editor for a Duolingo-style tap-to-assemble UI -
  shuffled lines of the reference solution as tappable chips, aimed at
  mobile where typing real code is painful. Backs onto a new
  `reference_solution` field on `CodingProblem` (now populated for every
  problem in every track) and `GET /api/coding/{day_id}/blocks`.
- **Optional AI grading**: the concept check can be graded by the Anthropic
  API (`ANTHROPIC_API_KEY`, cheap Haiku model) instead of pure self-report;
  falls back cleanly when unset. Coding problems also got a small curated
  "Docs" panel of relevant cppreference.com (or MDN, for html_css) links.
- **Mobile pass**: real fixes, not just smaller fonts - full-width
  Compile & Run button, bigger/segmented track-switcher touch targets, a
  visible indicator dot on quiz choices for pushed/correct/incorrect state.
- **Two real bugs found and fixed via button-driven testing** (worth
  remembering, since they'd bite again the same way):
  - `.btn-chunky`'s own `display` declaration tied the browser's default
    `[hidden]{display:none}` rule on CSS specificity, so hiding any chunky
    button via the `hidden` property never actually hid it visually. Fixed
    with a blanket `[hidden]{display:none!important}` rule.
  - `SANDBOX_MODE=docker` (the documented production path) was completely
    broken: the Debian `docker.io` package no longer ships the `docker` CLI
    on the `python:3.11-slim` base image (only `dockerd`), and even with the
    CLI installed, the docker-outside-of-docker bind mount used a
    container-local tmp path that doesn't exist on the host daemon's side.
    Fixed by installing the static docker CLI directly and sharing one real
    host directory for sandbox tmp files with container<->host path
    translation (`SANDBOX_TMP_DIR` / `SANDBOX_HOST_TMP_DIR`).
- The disclaimer that this project is heavily AI-assisted lives in this
  README now, not as a UI banner.

## Phase 2 - Make it enjoyable to use daily (next up)

- **Accounts (done)**: the app moved from single-user/no-login to real
  per-account sign-in, so it can be shared with friends instead of just
  one person. No password auth of any kind:
  - **"Sign in with Google"** (`backend/app/auth.py`, via `authlib`) - a
    `User` is keyed on Google's `sub` claim (find-or-create on first
    login), with a signed session cookie (`itsdangerous`) after that. Needs
    a Google Cloud Console OAuth Client (`GOOGLE_CLIENT_ID`/`_SECRET` env
    vars); both the deployed callback URL and
    `http://localhost:8000/auth/google/callback` need to be registered as
    authorized redirect URIs on it (Google allows plain-http `localhost`
    for dev even on a "Web application" client).
  - **"Play offline"** - a disposable guest account (random token stands in
    for the Google identity) for anyone who doesn't want to use a Google
    account. Still saved server-side (not a real offline/PWA mode - the
    server is still required), just not tied to any external identity.
  - **Every `Day` row is now scoped per-account**: the unique constraint
    became `(user_id, date, track)` instead of `(date, track)`, and every
    router that looked up a `Day` by id (`reset_day`, quiz/coding/concept
    submit) now also checks `day.user_id == current_user.id` - this closes
    an IDOR that existed even before accounts were added (any `day_id` was
    previously actionable by anyone, since there was only ever one user).
  - **Two real bugs worth remembering** (same spirit as Phase 1's list):
    since `init_db()` is `Base.metadata.create_all` only (additive, never
    alters existing tables), changing the `User` schema mid-flight (first
    username/password, then Google-only) left a stale `users` table on any
    box that had already run once - showed up as
    `sqlite3.OperationalError: no such column: users.google_sub` on first
    real login. No migration framework exists yet, so a schema change to
    `User`/`Day` currently means wiping the DB file, fine pre-launch but
    worth fixing before this holds real user data. Separately, the OAuth
    callback's post-login `RedirectResponse(url=".")` 404'd - relative "."
    resolves against the *current* path, so from a nested route like
    `/auth/google/callback` it lands on `/auth/google/` instead of the app
    root; fixed with a helper that climbs back out based on the current
    path's depth (`main.py: _relative_to_root`), which also keeps working
    if the app is deployed under a reverse-proxy path prefix.
- **System Design track (done)**: a third track, `system_design`
  (`backend/app/content/system_design_bank.py`), following the same
  self-checked pattern as `html_css` (`uses_sandbox: False` - submit a
  free-text design attempt, then compare against a revealed reference
  solution). Seeded with 29 entries per content type (8 easy/8 medium/8
  hard/5 expert = 87 total) - deliberately deeper than the other two tracks
  so a month of daily use has low repetition; expert-tier practice problems
  are classic "design X" case studies (URL shortener, rate limiter, chat
  system, news feed, distributed cache). The code editor falls back to
  plain-text mode for this track (no C++/HTML highlighting misfiring on
  prose) via a small mode lookup table in `app.js`. On every boot, the app
  also backfills the past 30 days of `system_design` `Day` rows
  (`day_service.backfill_history`, called from `main.py`'s lifespan) so its
  calendar/history shows a month of already-open days immediately instead
  of only creating them lazily on click - reuses the existing idempotent
  `get_or_create_day`, no new selection logic needed.
- **Rebrand to "dailyptr"**: renamed the app-facing title/brand text
  (`frontend/index.html`, FastAPI `title=` in `main.py`), README/PLAN
  headings, and the Docker image names (`cpp-refresher-*` ->
  `dailyptr-*` in `docker-compose.yml`, `config.py`'s `SANDBOX_IMAGE`
  default, and the sandbox Dockerfile comment) to reflect that the app is
  now multi-track, not C++-only.
- **Grow content toward a full year (not started)**: the user asked for
  this to be scheduled as follow-up work, not built now. Goal: extend all
  three tracks' pools toward roughly 40-45 entries per difficulty tier per
  content type (~4-5x System Design's current depth, which is itself the
  deepest track today), so even a full year of daily use stays low-repeat.
  Consider extending the `backfill_history` approach to the other two
  tracks as well while doing this pass.
- **Code editor upgrade (done)**: swapped the plain `<textarea>` for
  CodeMirror 5 (via CDN, `CodeMirror.fromTextArea`) for syntax highlighting
  and bracket matching on the non-block-mode path; block mode is untouched.
  Mode switches between `text/x-c++src` and `htmlmixed` based on the active
  track. A custom theme (`.cm-s-dailyptr` in style.css) matches the existing
  dark panel look instead of pulling a premade CDN theme. Needed a
  `cmEditor.refresh()` both when un-hiding from block mode and when
  switching into the Code tab the first time - CodeMirror mis-measures
  itself if initialized/updated while its container is `display:none`.
- **Content volume**: still true - `cpp_core`'s pool grew this session
  (quiz 21->33, coding 7->11, concept 6->10) but a real week-over-week user
  will still see repeats within a couple months. `html_css` is much thinner
  (12/4/4) and would benefit most from more content. Pure data entry in
  `backend/app/content/*.py`.
- **Spaced repetition for concept checks**: weight selection toward topics
  self-graded "missed" recently (needs a small history table keyed by
  concept id, per track).
- **Weak-topic targeting for quizzes**: same idea for quiz topic selection.

## Practice projects (things for Austin to build himself, not just ask for)

Backend-engineering exercises the app's own infra happens to motivate -
tracked here so they don't get silently done *for* him instead of *by* him.
Both assume starting from au5y-serv's current state (database was wiped
2026-08-19, so there's no real user data riding on either yet - good timing
for a clean cutover rather than a data-migration exercise, though writing a
one-off "copy the old SQLite rows over" script first is itself good reps if
that's wanted too).

- **Swap SQLite for Postgres + adopt real migrations (Alembic)**: replaces
  Phase 5's old "a real migration framework" bullet with a concrete plan.
  `requirements.txt` already has `psycopg2-binary`, and `database.py`
  already branches `connect_args` on `DATABASE_URL.startswith("sqlite")`,
  so the app itself barely needs to change - swapping `DATABASE_URL` to a
  `postgresql://...` URL should just work. What's actually worth doing by
  hand:
  1. Add a `postgres:16-alpine` service to `docker-compose.yml` (au5y-serv
     already runs this exact image for `authentik-db` - same pattern) with
     a named volume for persistence and a healthcheck the `web` service
     depends on.
  2. Replace `database.py`'s `_migrate_add_onboarded_column` - a hand-rolled,
     SQLite-only, one-column patch (raw `PRAGMA table_info` + `ALTER TABLE`)
     that would silently no-op or break on Postgres - with `alembic init`,
     an initial migration capturing the current schema, and `alembic
     upgrade head` run on startup/deploy instead of `Base.metadata.create_all`.
     Every future model change becomes a real migration instead of another
     ad hoc patch function.
  3. **The "object management layer" part**: introduce a repository /
     data-access layer between the routers and the raw ORM. Right now
     `db.query(models.Day)...`-style calls are scattered directly across
     `routers/*.py`, `day_service.py`, and `scoring.py` - fine at this size,
     but it's exactly the kind of thing that's worth practicing properly:
     a `backend/app/repositories/` module (or similar) exposing named
     methods (`DayRepository.get_or_create(...)`,
     `UserRepository.find_or_create_google_user(...)`,
     `TrackSubscriptionRepository.subscribe(...)`) that own all the query
     construction, so route handlers only ever call intention-revealing
     methods and never touch `db.query(...)` directly. Makes the ORM layer
     mockable/swappable and is the actual pattern (Repository / DAL) that
     "object management layer" is reaching for.

## Phase 3 - Harden the sandbox further

- **Replace the per-submission sandbox runner (design question raised
  2026-08-19, not decided)**: profiling on au5y-serv this session found
  `docker run` itself costs ~3s per submission *before* any compiling
  happens - confirmed independent of dailyptr's own image (`docker run --rm
  alpine true` costs the same there), so it's inherent to "spin up one
  disposable container per submission" on a host already running two dozen
  other containers. That's on top of `docker_runner.py`/`subprocess_runner.py`
  both being homegrown, and `SANDBOX_MODE=docker` specifically requiring a
  mounted host Docker socket that PaaS hosts like Render/Railway don't
  offer at all (see `Dockerfile.render`'s subprocess-mode fallback, which
  is explicitly documented as "NOT a real sandbox" - shares the app
  container's filesystem/network, rlimits only). Options, roughly in order
  of recommendation:
  1. **Self-hosted external execution service (e.g. Piston)** - dailyptr
     POSTs source+stdin to an HTTP API instead of shelling out to `docker
     run` itself; the execution engine owns its own per-request isolation
     internally, so dailyptr's own container no longer needs docker-socket
     access at all. Solves the sandbox-hardening question and the
     Railway/Render portability question in one move - highest leverage of
     these options.
  2. **A warm container pool** - keep N long-lived isolated containers
     around and dispatch via `docker exec` instead of `docker run` each
     time, recycling/resetting between submissions. Cuts the ~3s
     create-cost but adds real complexity (pool lifecycle, guaranteeing no
     state leaks between two different users' code in the same reused
     container) for less benefit than option 1.
  3. **Firecracker microVMs** (what Vercel Sandbox / fly.io use) - ~125ms
     boot instead of several seconds, the technically "correct" answer if
     this ever needs to hold up under untrusted strangers at scale.
     Meaningful extra infra (KVM, firecracker-containerd) for a personal
     app - probably overkill right now.
  4. **Drop compiled execution for the C++ track, self-check it like
     html_css/system_design** - simplest to build, but gives up the "does
     it actually compile and pass" rigor that's the C++ track's whole
     point. Not recommended.
- **Compile-time diagnostics**: stderr is dumped back to the user as-is;
  worth stripping absolute tmpdir paths that leak the host's temp directory
  name (cosmetic, but visible now since Docker mode actually works).
- **Structured per-test-case results**: promote the harness's pass/fail
  lines to a real `list[TestCaseResult]` in the API response instead of a
  text blob, so the frontend can render a table.
- **Resource limit tuning (partially done 2026-08-19)**: `SANDBOX_CPU_LIMIT`
  raised 0.5 -> 1.0 core after measuring that the STL-heavy harness compile
  (`bits/stdc++.h`) takes ~1.9s of real CPU time uncapped but was being
  stretched to 4-6s wall time by the 0.5-core cap even with the host mostly
  idle; cut a real submission's round trip from ~11.5s to ~9.9s. Memory
  (128MB) and timeout (10s) limits are still untouched conservative
  guesses - revisit once real submissions (including the cpp_backend-flavored
  problems) show what they actually need.

## Phase 4 - Make progress visible

- **Stats page upgrade**: topic-accuracy breakdown and a points-over-time
  chart (the calendar heatmap part of this already shipped in Phase 1).
- **Export**: a "download my history as JSON/CSV" button - the backup
  story for your own data now that accounts exist.
- **Weekly recap**: an optional end-of-week summary.

## Phase 5 - Only if requirements change

- **Multi-user accounts (done - see Phase 2)**: shipped once the goal
  became sharing with friends rather than solo use. A per-account
  leaderboard/comparison view is a natural follow-up now that the data
  exists, but not built yet.
- **Public exposure / reverse proxy + TLS**: the auth gate itself now
  exists (Google sign-in / guest accounts, Phase 2), but the app still
  needs to actually sit behind a reverse proxy with real TLS to be exposed
  beyond localhost/Tailscale - self-hosted, in progress.
- **A real migration framework**: superseded by the detailed "Swap SQLite
  for Postgres + adopt real migrations" entry under **Practice projects**
  above.
- **Judge0 or another external judge**: only worth it for far more problems
  than hand-writing harnesses can keep up with - see also the Piston-style
  option under Phase 3's sandbox-replacement writeup, which is the same
  idea for a different reason (portability/isolation, not problem volume).

## Phase 6 - Practice modalities beyond quiz/coding/concept (ideas, not decided)

Raised 2026-08-19: what else is worth practicing daily that isn't LeetCode-
style algorithms, a trivia quiz, or open-ended free response? Rough ideas,
roughly ordered by how cheaply they'd bolt onto what already exists:

- **Code review challenges** (recommended next content type - no new
  infra): show a small diff or snippet with 1-3 seeded bugs/smells
  (correctness, security, a real anti-pattern), self-report which ones were
  found, reveal an annotated answer key. Reuses the concept-check
  self-grade UI/pattern almost exactly - just a diff instead of a prompt.
- **Debugging challenges** (recommended next content type - no new infra):
  a stack trace or failing-test output plus a broken snippet, multiple
  choice on the root cause. Reuses the quiz UI/grading directly.
- **Log/metrics investigation challenges**: give a snippet of logs, timings,
  or a resource graph, ask what's actually wrong - basically what this
  session's own perf-debugging detour was (~11.5s code submissions traced
  to container-startup + CPU-throttled compiles). Quiz-style grading,
  distinctly non-leetcode, and closer to what real on-call work looks like
  than almost anything else on this list.
- **Test-writing exercises** (biggest lift, highest realism payoff): given
  a spec, write unit tests against it; grade by running the submitted tests
  against N seeded *buggy* reference implementations and checking how many
  they actually catch (mutation-testing-style). A natural extension of the
  existing coding-problem sandbox infra once Phase 3's sandbox-replacement
  question is settled, rather than a separate system.
- **Git workflow drills** (lower priority - harder to grade
  automatically): present a merge-conflict or messy-history scenario,
  have the user resolve/rebase it. Needs a real git sandbox per attempt,
  more infra than everything else on this list for a niche skill.

## Decisions made along the way (and why)

- **Stack**: Python/FastAPI + SQLite + vanilla JS, chosen for fastest
  iteration on the sandbox-orchestration logic with zero frontend build
  tooling. Still true - the redesign and block-mode work were done in plain
  JS/CSS without reaching for a framework.
- **Sandbox**: Docker-outside-of-Docker (backend container talks to the host
  daemon via a mounted socket), not Docker-in-Docker. This pattern is
  correct but has a real gotcha (see Phase 1's bug list) around bind-mount
  paths not lining up between the two "sides" - now fixed and documented in
  `app/sandbox/docker_runner.py`.
- **Google sign-in + guest accounts, no passwords of our own** (Phase 2):
  once the goal became sharing with friends rather than solo use, the
  choice was OAuth (Google) over hand-rolled password auth - no password
  storage/hashing/reset-flow to get right, at the cost of requiring a
  Google Cloud OAuth Client to be set up. "Play offline" (a disposable
  guest account) exists specifically so a Google account isn't a hard
  requirement to try the app. Reachable over Tailscale (MagicDNS hostname
  or `100.x.x.x`) without any code changes, since the container already
  binds `0.0.0.0:8000`.
- **Tracks over separate apps**: rather than standing up a second
  deployment for HTML/CSS practice, one app now supports multiple content
  pools behind a `(date, track)` key - less infrastructure, shared
  scoring/history/calendar machinery, at the cost of `uses_sandbox`
  branching in `routers/coding.py` for tracks without a compiler.
- **Block mode reveals the reference solution's lines up front** (shuffled)
  rather than gating them behind completion - a deliberate tradeoff for a
  self-hosted practice app among friends, not a graded course, where
  "spoiling" your own challenge isn't a real concern.
- **Difficulty tiers are 4 buckets (easy/medium/hard/expert) mapped 2
  weekdays each except expert (Sunday only)**, not a continuous 1-7 scale,
  so the content bank doesn't need a separate pool per individual weekday.
