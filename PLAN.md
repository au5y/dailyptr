# Roadmap: C++ Daily Skill Refresher

Source requirement (from the project description): a daily learning app that
verifies and tests C++, software programming, OOD, and design pattern
knowledge via a short multiple-choice quiz, a small coding problem that runs
in a sandbox, and other knowledge checks - getting harder from easy Monday
to difficult Sunday, with the ability to go back on missed days, points as
you go, and fully self-hosted.

## Phase 0 - Scaffold (done, this commit)

What exists right now and has been verified working end to end:

- FastAPI + SQLite backend with a real data model: `Day`, `QuizQuestion`,
  `CodingProblem`, `ConceptCheck`, `CodeSubmission`.
- Weekday -> difficulty mapping (Mon/Tue easy, Wed/Thu medium, Fri/Sat hard,
  Sun expert), each with a points multiplier.
- A seeded content bank: 21 quiz questions, 7 coding problems, 7 concept
  checks, spanning C++ semantics, memory/RAII, STL, OOD/SOLID, and design
  patterns (Singleton, Strategy, Decorator, Observer, Template Method, plus
  an LRU Cache design problem as the expert-tier coding challenge).
- Real sandboxed code execution with two backends: a Docker one (network
  disabled, memory/CPU/pids limits, disposable container per submission -
  intended for actual self-hosted use) and a subprocess one (rlimits only -
  for local dev without a Docker daemon). Both share one grading contract
  and are covered by tests that run real g++ against every seeded problem,
  plus deliberately broken/malicious/infinite-looping submissions to check
  failure handling.
- Points + streak scoring: quiz points scale with correct answers x
  difficulty multiplier, coding/concept checks award a flat amount x
  multiplier, plus a small on-time bonus if you finish a day on its actual
  date. Streak is computed from which calendar dates are fully completed,
  so it naturally survives you working from the History view.
- A "go back if you miss a day" model: every day of every week is
  independently addressable (`GET /api/day/{date}`), content is picked
  deterministically per date (stable across reloads) but only once you've
  actually opened that date, and there's no penalty for completing a day
  late beyond not getting the on-time bonus.
- A minimal but complete vanilla JS/HTML/CSS frontend: today's challenge,
  the three components as tabs, and a History view to browse/complete any
  past day.
- 11 automated tests (scoring math, the sandbox grader, and a full
  Monday-through-Sunday API walkthrough) - all passing.
- Single-user, no-auth, Docker Compose deployment (per your choice - see
  "Decisions" below for why, and what multi-user would take).

This is a working vertical slice, not a stub: you can `docker compose up`
today and actually do a full week of daily practice with it.

## Phase 1 - Make it enjoyable to use daily (next)

- **Code editor upgrade**: swap the plain `<textarea>` for CodeMirror or
  Monaco (via CDN) for syntax highlighting, bracket matching, and a monospace
  editing experience that doesn't fight you.
- **Content volume**: the seed bank is intentionally small (proof of the
  pattern, not a full curriculum). Expand each difficulty tier to 15-20 quiz
  questions and 5-8 coding problems so a real week-over-week user doesn't see
  repeats for a couple of months. This is pure data entry in
  `backend/app/content/*.py` - the mechanism already supports it.
- **Spaced repetition for concept checks**: instead of one random pick per
  difficulty per day, weight selection toward topics you self-graded "missed"
  recently (needs a small history table keyed by concept id).
- **Weak-topic targeting for quizzes**: same idea - track per-topic accuracy
  over time and bias question selection toward topics you're worse at,
  instead of pure random sampling.

## Phase 2 - Harden the sandbox for real daily use

- **Compile-time and memory diagnostics surfaced better**: currently stderr
  is just dumped back to the user; worth lightly formatting compiler errors
  (strip absolute tmpdir paths, which currently leak the host's temp
  directory name in error text - cosmetic but worth cleaning up).
- **Multiple test-case granularity**: today a submission is pass/fail per
  problem; showing per-test-case pass/fail already exists in the harness
  output text but isn't structured in the API response - promote it to a
  real `list[TestCaseResult]` so the frontend can render a table instead of
  a text blob.
- **Resource limit tuning**: current Docker limits (128MB / 0.5 CPU / 10s)
  are conservative guesses; revisit once you see what real submissions need
  (e.g. an expert-tier problem doing legitimate heavier computation).
- **Sandbox image caching**: `sandbox-runner` image already only needs
  building once; consider pre-warming a small pool of containers if
  container-start latency (~0.5-1s typically) ever feels slow in practice.

## Phase 3 - Make progress visible

- **Stats/history page upgrade**: a simple calendar heatmap (GitHub-style)
  of completed days, topic-accuracy breakdown, and a points-over-time chart.
- **Export**: a "download my history as JSON/CSV" button - since this is
  fully self-hosted with no account system, this is the backup story until/
  unless real accounts exist (see Phase 4).
- **Weekly recap**: an optional end-of-week summary (could be a simple page,
  or - since you're comfortable with self-hosting - an optional scheduled
  job that emails/notifies a recap).

## Phase 4 - Only if requirements change

These were explicitly scoped *out* for now based on your answers when this
was built, but are worth revisiting if the way you use the app changes:

- **Multi-user accounts**: not needed for a single-person daily habit tool;
  would matter if you wanted friends/coworkers doing the same daily
  challenge on one deployment. Would need real auth (sessions or JWT),
  per-user `Day`/stats scoping, and probably a leaderboard.
- **Public exposure / reverse proxy + TLS + auth gate**: today this assumes
  localhost or a private network. If you ever want to hit it from your phone
  over the open internet, add at minimum a reverse proxy (Caddy/nginx) with
  a password gate or real auth before exposing port 8000 publicly - the
  Docker sandbox isolates code execution, not the web app itself.
- **Judge0 or another external judge**: only worth it if you want far more
  problems than you're willing to hand-write harnesses for; the current
  approach (you own the harness) gives full control over grading
  correctness at the cost of writing it yourself.

## Decisions made while scaffolding this (and why)

Captured here so future-you doesn't have to reverse-engineer the reasoning:

- **Stack**: Python/FastAPI + SQLite + vanilla JS. Chosen over Node/React or
  Go for fastest iteration on the sandbox-orchestration logic (which is the
  most novel part of this app) and zero frontend build tooling.
- **Sandbox**: Docker container per submission, using the
  Docker-outside-of-Docker pattern (backend container talks to the host
  daemon via a mounted socket) rather than Docker-in-Docker, which is
  simpler and avoids the storage-driver headaches of nested Docker.
  Subprocess-with-rlimits exists purely as a lower-friction dev/test
  fallback, not a production security boundary.
- **No auth / single user**: matches "just me" daily practice use case;
  revisit under Phase 4 if that changes.
- **Difficulty tiers are 4 buckets (easy/medium/hard/expert) mapped 2
  weekdays each except expert (Sunday only)**, rather than a continuous 1-7
  scale, so the content bank doesn't need a separate pool per individual
  weekday - halves the content-authoring burden while still delivering a
  visible Monday->Sunday ramp.
