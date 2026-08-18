# Roadmap: C++ Daily Skill Refresher

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

- **Code editor upgrade**: swap the plain `<textarea>` for CodeMirror or
  Monaco (via CDN) for syntax highlighting and bracket matching, for the
  non-block-mode path.
- **Content volume**: still true - `cpp_core`'s pool grew this session
  (quiz 21->33, coding 7->11, concept 6->10) but a real week-over-week user
  will still see repeats within a couple months. `html_css` is much thinner
  (12/4/4) and would benefit most from more content. Pure data entry in
  `backend/app/content/*.py`.
- **Spaced repetition for concept checks**: weight selection toward topics
  self-graded "missed" recently (needs a small history table keyed by
  concept id, per track).
- **Weak-topic targeting for quizzes**: same idea for quiz topic selection.

## Phase 3 - Harden the sandbox further

- **Compile-time diagnostics**: stderr is dumped back to the user as-is;
  worth stripping absolute tmpdir paths that leak the host's temp directory
  name (cosmetic, but visible now since Docker mode actually works).
- **Structured per-test-case results**: promote the harness's pass/fail
  lines to a real `list[TestCaseResult]` in the API response instead of a
  text blob, so the frontend can render a table.
- **Resource limit tuning**: current Docker limits (128MB / 0.5 CPU / 10s)
  are conservative guesses; revisit once real submissions (including the
  new cpp_backend-flavored problems) show what they actually need.

## Phase 4 - Make progress visible

- **Stats page upgrade**: topic-accuracy breakdown and a points-over-time
  chart (the calendar heatmap part of this already shipped in Phase 1).
- **Export**: a "download my history as JSON/CSV" button - still the backup
  story until/unless real accounts exist (Phase 5).
- **Weekly recap**: an optional end-of-week summary.

## Phase 5 - Only if requirements change

- **Multi-user accounts**: not needed for a single-person daily habit tool;
  would need real auth, per-user `Day`/stats scoping (tracks already prove
  out a `(date, track)`-keyed model that a `(date, track, user)` model could
  follow), and probably a leaderboard.
- **Public exposure / reverse proxy + TLS + auth gate**: still assumes
  localhost or a private network (Tailscale works fine today - see below).
  If exposed to the open internet, add a reverse proxy with a password gate
  or real auth first.
- **Judge0 or another external judge**: only worth it for far more problems
  than hand-writing harnesses can keep up with.

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
- **No auth / single user**: matches "just me" daily practice use case.
  Tested reachable over Tailscale (MagicDNS hostname or `100.x.x.x`) without
  any code changes, since the container already binds `0.0.0.0:8000`.
- **Tracks over separate apps**: rather than standing up a second
  deployment for HTML/CSS practice, one app now supports multiple content
  pools behind a `(date, track)` key - less infrastructure, shared
  scoring/history/calendar machinery, at the cost of `uses_sandbox`
  branching in `routers/coding.py` for tracks without a compiler.
- **Block mode reveals the reference solution's lines up front** (shuffled)
  rather than gating them behind completion - a deliberate tradeoff for a
  self-hosted, single-user, no-login app where "spoiling" your own
  challenge isn't a real concern the way it would be in a graded course.
- **Difficulty tiers are 4 buckets (easy/medium/hard/expert) mapped 2
  weekdays each except expert (Sunday only)**, not a continuous 1-7 scale,
  so the content bank doesn't need a separate pool per individual weekday.
