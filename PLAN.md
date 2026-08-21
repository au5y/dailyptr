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
- **System Design track (done, scope broadening in progress)**: a third
  track, `system_design` (`backend/app/content/system_design_bank.py`),
  following the same self-checked pattern as `html_css` (`uses_sandbox:
  False` - submit a free-text design attempt, then compare against a
  revealed reference solution). Seeded with 29 entries per content type (8
  easy/8 medium/8 hard/5 expert = 87 total) - deliberately deeper than the
  other two tracks so a month of daily use has low repetition. The code
  editor falls back to plain-text mode for this track (no C++/HTML
  highlighting misfiring on prose) via a small mode lookup table in
  `app.js`. On every boot, the app also backfills the past 30 days of
  `system_design` `Day` rows (`day_service.backfill_history`, called from
  `main.py`'s lifespan) so its calendar/history shows a month of
  already-open days immediately instead of only creating them lazily on
  click - reuses the existing idempotent `get_or_create_day`, no new
  selection logic needed.
  - **Reframed as the interdisciplinary track, not a software-architecture
    track (decided 2026-08-20)**: today's 87 entries lean almost entirely
    on classic software case studies (URL shortener, rate limiter, chat
    system, news feed, distributed cache). Going forward this track's
    content pool should broaden to general design/tradeoff thinking that
    isn't software-specific - e.g. organizational design, product/process
    design, physical/infrastructure systems, ops and incident-response
    structure, economics/mechanism-design-flavored problems - alongside the
    existing software case studies rather than replacing them outright.
    Mechanically nothing changes for the quiz/concept content (still
    free-text attempt vs. revealed reference solution); this is a
    content-authoring direction, not a new feature - existing 87 quiz/concept
    entries stay as-is until new non-software ones are written. The track's
    *review step* did change (2026-08-20): `system_design` now uses Critical
    Reasoning Review instead of Code Review (see the Phase 6 entry below),
    which is itself already interdisciplinary content (org design, incident
    postmortems, pricing strategy) rather than software case studies -
    a first real step on this broadening, not the whole of it.
- **Rebrand to "dailyptr"**: renamed the app-facing title/brand text
  (`frontend/index.html`, FastAPI `title=` in `main.py`), README/PLAN
  headings, and the Docker image names (`cpp-refresher-*` ->
  `dailyptr-*` in `docker-compose.yml`, `config.py`'s `SANDBOX_IMAGE`
  default, and the sandbox Dockerfile comment) to reflect that the app is
  now multi-track, not C++-only.
- **Content volume growth - C++ Core and HTML/CSS (first pass done,
  2026-08-20; not yet at true no-repeat-month depth)**: added quiz/
  concept/code-review entries to both tracks, on-task for each track's
  actual subject (C++/STL/OOD/design patterns/concurrency for `cpp_core`;
  markup/CSS/layout/accessibility for `html_css`) rather than generic dev
  trivia, keeping the two tracks distinct from each other and from System
  Design's interdisciplinary content. New counts per difficulty tier
  (easy/medium/hard/expert):
  - `cpp_core`: quiz 9/9/9/6 (unchanged, already reasonably deep),
    concept 5/5/5/3 (was 3/3/3/2), code-review 4/4/4/3 (was 2/2/2/2).
  - `html_css`: quiz 5/5/5/3 (was 3/3/3/3), concept 4/4/4/3 (was 1/1/1/1),
    code-review 4/4/4/3 (was 2/2/2/2).
  Verified: all entries parse and seed cleanly into a fresh DB (no
  duplicate titles/questions, every code-review marker resolves), full
  pytest suite still green (33 tests).
  **Still short of "a full month, zero repeats"**: since a Day picks 1
  concept-check and 1 code-review entry (vs. `QUESTIONS_PER_DAY=3` sampled
  per quiz), those two need roughly 9 entries per weekday-pair tier
  (easy/medium/hard) and ~5 for expert (Sunday-only) to cover a ~4.3-week
  month with zero repeats - current depth (4-5 per tier) covers roughly
  2-2.5 weeks before repeating. Next increment: keep adding concept/
  code-review entries toward that ~9/9/9/5 target for both tracks (quiz
  can stay lower priority since its 3-per-day sampling absorbs a smaller
  pool better). Consider extending the `system_design`-style
  `backfill_history` approach to these two tracks once pools are deep
  enough to support it.
- **Grow System Design toward a full year (later)**: same idea as above,
  deferred - extend it toward roughly 40-45 entries per difficulty tier
  once the C++/HTML-CSS push above is done.
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
- **Turn on AI grading for real, with an abuse guard (next up, decided
  2026-08-20)**: the concept-check "AI-grade my answer" button
  (`frontend/app.js:962`, `POST /concept/{day_id}/ai-grade`) already exists
  and is gated to signed-in (non-guest) accounts, but sits dark today
  because `ANTHROPIC_API_KEY` isn't set anywhere it's deployed. Before
  setting the real key on Railway: any Google account can currently sign in
  and hit this endpoint with no limit, which against a real API key means
  anyone who signs in can run up usage/cost unbounded - needs a per-account
  cap (e.g. a small daily/weekly quota, tracked per user, 429ing past it)
  before the key goes live, not after.
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

## Phase 3 - Harden the sandbox further (moot - sandbox removed, see Phase 7)

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

- **Streak milestone badges (built 2026-08-20, not visible/findable yet)**:
  backend + History-page row exist (`config.STREAK_MILESTONES` =
  3/7/14/30/60/100/200/365 days, `MilestoneAward` table unique on `(user,
  track, milestone)`, toast on the tab that completes the day), but there's
  currently no obvious, persistent place to go see your earned badges -
  belongs on a real profile/account page, which doesn't exist yet. Revisit
  once a profile page is built rather than trying to surface it further in
  History. Freezes/protection, an "at risk" reminder, and a friends
  leaderboard were explicitly not built this pass either - worth returning
  to.
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
- **Public exposure / reverse proxy + TLS (done, 2026-08-20)**: live on
  Railway, reverse-proxied at `au5y.dev/daily`. Google OAuth sign-in was
  broken in production for a bit (Railway's log capture wasn't showing
  anything mid-request, so the callback couldn't be debugged blind) - fixed
  by routing callback failures through `login?error=<reason>` so the real
  exception surfaced on the page, which found and fixed the actual cause
  (redirect URI / path-prefix mismatch under `/daily`), plus a follow-up fix
  for the favicon 404ing under the same prefix. Diagnostic error-surfacing
  on the login page is still in place - worth trimming to a generic message
  now that it's served its purpose.
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

- **Code review challenges (done, 2026-08-20 - see Phase 7)**: show a
  snippet with 1-3 seeded issues, click-to-flag the buggy line(s) then
  match each to a reason from an answer bank, objectively graded
  server-side. Shipped as `models.CodeReviewChallenge` /
  `routers/code_review.py`, covering all three tracks.
- **Critical reasoning review (done, 2026-08-20)**: the non-code complement
  to Code Review - same click-to-flag-then-match mechanic, but the "snippet"
  is a paragraph of prose reasoning (a business justification, an incident
  postmortem, a design rationale, an argument) seeded with 1-3 real flaws
  (correlation/causation mixups, survivorship bias, unstated assumptions,
  Simpson's paradox, etc.) instead of code bugs. Shipped as a genuinely
  separate model/router (`models.CriticalReasoningChallenge`,
  `routers/critical_reasoning.py`, `content/critical_reasoning_bank.py` -
  8 entries, 2 per difficulty tier), not a variant of Code Review, matching
  the codebase's one-model-per-content-type convention. Introduced
  `config.TRACKS[track]["review_kind"]` ("code" vs "reasoning") as the
  mechanism deciding which of the two a track's `Day` rows use as their
  *required* review step - `Day.fully_completed` reads whichever one
  applies. `system_design` switched from Code Review to Critical Reasoning
  (its 8 old code-review entries, forced into pseudocode, were deleted from
  `code_review_bank.py`); `cpp_core`/`html_css` are untouched. Frontend
  (`app.js`) generalizes the render/submit logic behind a small
  `REVIEW_KIND_CONFIG` map keyed by DOM-id-prefix/endpoint/Day-field-name
  rather than duplicating the interaction code, since - unlike the backend,
  which stayed a straightforward sibling router given the differing field
  names - the click/match/submit behavior itself is identical either way.
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

## Phase 7 - Replaced compiled coding problems with Code Review challenges (done)

Decided 2026-08-19: writing/compiling C++ in the app was going away
entirely, not staying alongside something new - "nix the writing of
code... even with the formatting" was explicit. The Code tab's compiled
LeetCode-style problems were retired, and with them the whole sandbox
subsystem that existed to run them - which also happened to be the thing
that made Railway/Render hosting awkward (`SANDBOX_MODE=docker` needs a
host Docker socket that PaaS hosts don't give you) and the thing
responsible for the ~10s-per-submission latency traced earlier that
session. Removed: `models.CodingProblem`/`CodeSubmission`,
`routers/coding.py`, `backend/app/sandbox/` (the whole package), the Code
tab/CodeMirror/block-mode UI in `frontend/`, `docker-compose.yml`'s docker
CLI install + `/var/run/docker.sock` mount + `SANDBOX_*` env vars +
`sandbox-runner/` build context, and `config.py`'s `SANDBOX_*` settings and
`uses_sandbox` (every track became the same shape once nothing compiles),
plus a migration dropping the now-unused columns/tables.

The replacement picked was **Phase 6's Code Review idea**, not the
originally-sketched "Debug challenge" (multiple choice on a broken
snippet's root cause) - self-graded at first (spot 1-3 seeded bugs/smells
in a snippet, self-report, reveal an annotated answer key).
`models.CodeReviewChallenge`, `routers/code_review.py`, and
`content/code_review_bank.py` are the result, covering all three tracks
(system_design's "snippet" is a short design note instead of literal
code).

**Update, 2026-08-20 - Code Review made objectively-graded, not self-reported
(done)**: the self-graded version above didn't last a full day. New shape:
a longer snippet (~15-30 lines, up from a handful) seeded with 1-3 issues,
each with a short `reason` tag plus a longer `explanation`
(`models.CodeReviewChallenge.issues`, JSON). The user clicks the line(s)
they think are buggy, then matches each flagged line to a reason from an
answer bank built by mixing the snippet's real reasons with per-entry
`distractor_reasons` (`routers/code_review.py: build_challenge_out`) -
click-to-flag-then-tap-to-match, not drag-and-drop (simpler, works the same
on mobile). Grading is now fully objective and server-side
(`POST /code-review/{day_id}/submit` compares submitted `{line, reason}`
pairs against the answer key), so **AI grading and self-rating for code
review are gone entirely** - `ai_grading.grade_code_review` removed,
`Day.code_review_self_rating` replaced by `code_review_correct`/
`code_review_total` (mirrors how the quiz already scores), points now scale
with the fraction of issues correctly matched
(`scoring.points_for_code_review(correct_count, total, difficulty)`) instead
of a flat pass/fail amount. All 24 entries across the three tracks were
rewritten to the new shape (line numbers are computed from marker tokens at
content-bank-build time, not hand-counted, so future edits can't silently
drift out of sync with the seeded `issues`).

Two real bugs worth remembering (same spirit as Phase 1/2's lists):
- **Editing an already-applied Alembic migration file in place, under the
  same revision id, does not make Postgres re-run it.** Alembic tracks
  "current schema state" purely by revision id in `alembic_version` - if a
  DB already recorded that id before the file's contents changed, a normal
  restart sees `current == head` and skips straight to app startup, leaving
  the DB on the *old* column shape while the app code expects the new one.
  Hit this rewriting the `code_review_challenges`/`days` columns for the
  redesign above; the fix was a one-off manual `ALTER TABLE` patch on the
  local dev DB (documented in this session's transcript, not repeated here).
  Going forward: once a migration has shipped, always add a **new** revision
  for further schema changes instead of editing an old one in place - which
  is exactly what `c3f7a1d6e9b2` (milestone_awards, below) did correctly.
- **`docker restart <container>` does not pick up a freshly-built image** -
  it restarts the same container from whatever image it was originally
  `create`d from. After `docker compose build web`, the running dev
  container needs `docker compose up -d web` (recreate), not `docker
  restart`, or it silently keeps serving the old backend code (while the
  bind-mounted frontend updates live, which made this confusing to spot -
  new JS hitting old API responses, not an obviously-stale deploy).

## Phase 8 - Guest mode: local-only until sign-in (done, 2026-08-20)

**Update, 2026-08-20 - backend half built and tested; frontend deferred.**
Two open questions below got decided this session: (1) guest identity stays
exactly as it is today (`POST /auth/guest` still creates a real, disposable
`User` row + session cookie - genuine anonymity would mean reworking the
whole app-shell-serving path in `AuthMiddleware` for no real benefit, since
the goal was always "no *progress* data in the DB," not "no identity at
all"); (2) the merge rule for claiming is **existing account data always
wins** per `(date, track)` key and per subscribed track - a local guest
record only fills a gap the account doesn't already have, never merged with
one that exists (streaks are sequences, not counters). Also decided:
subscriptions/onboarding move local too, not just `Day` progress.

Shipped: `day_service.select_day_content` (the pure (date,track)->content
pick, extracted out of `get_or_create_day` so both the real and guest paths
share one selection implementation); `routers/guest.py` (`GET
/api/guest/challenge`, `POST /api/guest/quiz/answer`, `/code-review/check`,
`/critical-reasoning/check`, `/concept/score` - all stateless, all re-derive
content server-side from `(date, track)` alone, write no `Day` row, require
a guest identity but 403 for real accounts); `scoring.grade_line_matches`
(the line-matching algorithm extracted out of `code_review.py`/
`critical_reasoning.py` once guest mode made it a 4th caller - crossed the
duplication threshold the codebase's "keep them as full sibling routers"
precedent didn't); `grade_and_record_*`/`record_submission` service
functions extracted from each grading router's HTTP handler; and
`routers/claim.py` (`POST /api/claim`) which replays a guest's accumulated
local days/subscriptions into a real account through those exact same
service functions - never a third reimplementation of grading logic -
applying the skip-if-exists merge rule, chronologically per track so streak/
milestone replay comes out identical to live day-by-day play. All net-new
`backend/tests/test_guest.py`/`test_claim.py` plus the full existing suite
green (32 tests) - the extractions were verified to be zero-behavior-change
before being reused a second/third time.

**Update, 2026-08-20 (same day) - frontend wired in, feature complete.**
`frontend/app.js` gained a `Progress` module (an IIFE-scoped closure) that's
the single seam between guest and signed-in - every render/handler function
now calls only `Progress.*` and addresses a day by `(track, date)` rather
than `current.day.id` (which doesn't exist for a guest's virtual,
unpersisted day). Real accounts still hit the id-addressed endpoints
underneath (`Progress` keeps a small internal `track|date -> Day id` cache
populated by `getChallenge`, never exposed outside the module); guests hit
`/api/guest/*` and read/write a `dailyptr-guest-progress` localStorage
object (schema: `{onboarded, subscriptions: {track: subscribed_at}, days:
{"track|date": {...progress fields, plus raw quiz_answers/code_review_matches/
critical_reasoning_matches/concept_self_rating so a later claim can regrade
from scratch}}}`). Client-side ports of `scoring._streaks`/`is_late`/
`is_bonus`/the on-time completion bonus drive local stats/history - badges
stay suppressed for guests (`getStats()` always returns `badges: []`,
per the earlier decision that a locally-shown badge could fail to reproduce
post-claim). `POST /api/onboarding`/`/api/subscribe` are now guest-unused;
guest onboarding/track-adding writes straight to localStorage. `init()`
calls `Progress.maybeClaim()` once, right after determining a session is
real (not guest) and before the onboarded/track checks below it depend on
whatever claim just created.

**One real bug caught and fixed in this pass** (worth remembering, same
spirit as earlier sessions' bug lists): `POST /api/claim` created real
`TrackSubscription` rows but never set `User.onboarded = True` - a
brand-new account's first real sign-in after guest play would create
subscriptions via claim, then get bounced straight back to the onboarding
screen on next boot (since `Progress.isOnboarded` for a real account just
reads `me.onboarded`, and nothing had ever set it). Fixed in
`routers/claim.py`: if any subscriptions were newly claimed and the account
wasn't already onboarded, mark it onboarded too - test coverage added
(`test_claim_marks_account_onboarded`). Also hit the same detached-session
gotcha `routers/challenges.py`'s onboarding endpoint already has a comment
about: `user` from `get_current_user` is bound to `AuthMiddleware`'s own
(already-closed) session, so mutating it directly no-ops - has to be
`db.get(models.User, user.id)` first.

**Decided this session, not built**: no stateless AI-grade endpoint for
guests - the "AI-grade my answer" button is simply hidden when `isGuest`
(concept AI grading needs a `ConceptCheck` lookup that's cheap to add
statelessly, but wasn't judged worth it for an optional, already
config-gated feature). Guests get the plain reveal-and-self-rate flow.

Verified live (no browser automation tool was available in this
environment, so driven the same way the Code Review/Critical Reasoning
features were - real HTTP requests against the actual running server,
mirroring exactly what `Progress` sends): a guest completing a full
`cpp_core` day (quiz + code review + concept) via `/api/guest/*` creates
**zero** `Day` rows and computes the same point total (150 for a medium-
difficulty full day) a signed-in account gets for the identical
performance - confirms the client-side quiz-point/on-time-bonus formulas
match the server's exactly. `pytest tests/` green throughout (33 tests,
including the new claim-onboarding regression test).

Decided 2026-08-19: guest ("Play offline") accounts currently create a real
`User` row and persist every `Day`/submission to Postgres exactly like a
real account - just with a random identity instead of a Google one. New
requirement: a guest's progress should live **only in their own browser**
(not the database) until/unless they sign in with Google, at which point
their locally-accumulated progress gets pushed up into their new real
account. This is a genuine architecture change (auth flow, every router,
and the frontend's state management all touch it), so it's a spec, not a
same-session build.

**The key fact that makes this tractable**: a day's content selection
(which quiz questions / code review challenge / concept check get picked) is
already a *pure function* of `(date, track)` - `day_service.py`'s RNG is
seeded from `target_date.toordinal()` and the track name only, never from
`user_id`. Every user, guest or not, sees identical content for the same
`(date, track)`. That means "what's today's challenge" doesn't inherently
need a persisted `Day` row or even a real user at all - only *progress on*
that challenge does.

**Shape of the change**:
- **A stateless content-fetch path for guests**: same deterministic
  picking logic `day_service.py` already has, exposed without writing a
  `Day` row - e.g. a variant that returns the same `ChallengeOut` shape
  (or close to it) keyed on `(date, track)` alone, no `user_id` involved.
- **Stateless grading for guests**: quiz grading is already "look up
  `correct_index` from the content bank, compare, compute points," and code
  review grading is the same idea keyed on `{line, reason}` pairs instead of
  an index - neither structurally needs a `Day` row, just needs splitting
  from the "now persist it" half that currently follows it in each router.
  Concept-check grading is already self-reported/trusted today (no change
  in trust model there).
- **Client-side progress store** (`frontend/app.js`): a
  `localStorage`-backed object, not actual cookies (cookies are sent on
  every request and capped around 4KB - localStorage is the right tool for
  a structured per-day progress blob that only needs to live in this one
  browser) - keyed by `(track, date)`, shaped like today's `DayOut`
  (`quiz_completed`, `points_earned`, etc.) so as much of the existing
  rendering code as possible doesn't need to know whether it's looking at
  server or local state.
- **History/calendar/stats for guests**: computed client-side from that
  same localStorage store instead of `/api/history`/`/api/stats` - no
  cross-device sync, which is an inherent, acceptable limitation of "not in
  the database yet."
- **Claim-on-sign-in**: after a successful Google sign-in that started as a
  guest with local progress, POST the accumulated local data to a new
  endpoint that replays it into real `Day`/grading calls for the
  now-authenticated user. **Recompute correctness/points server-side from
  the content bank rather than trusting the client's claimed results** for
  anything that has a real answer key (quiz, code review) - the same way
  submissions are graded live today. This isn't a new trust hole: it's the
  same trust model concept-checks already use (self-reported), just applied
  to a batch of past days instead of one live submission.
- **Open question**: does "Play offline" still create *any* server-side
  identity up front (so a session cookie has something to reference,
  consistent with how auth currently works), or does guest mode need to
  work with no cookie/session at all until the first real sign-in? The
  simpler path is probably keeping a lightweight guest `User` row for
  session-cookie purposes but genuinely never writing `Day`/submission rows
  against it - worth deciding explicitly rather than assuming.

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
