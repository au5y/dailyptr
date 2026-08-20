---
name: deploy
description: Push the local dailyptr repo's committed changes to origin main, then SSH to austin@au5y-serv and update its self-hosted copy (git pull, rebuild the Docker image, restart the container) so the live site matches main. Use when the user asks to deploy, ship, push and update the server, or refresh the hosted site.
---

Ground truth about this setup (verified 2026-08-19 - re-check if any of it seems wrong):

- Local repo: `/home/austin/dailyptr`, remote `origin` = `git@github.com:au5y/dailyptr.git`.
- Live host: `austin@au5y-serv` (SSH key auth already works, no password needed).
- On au5y-serv the site is a plain `git clone` of the same repo at `/home/austin/docker/dailyptr` (sibling to au5y's other `docker/*` compose services, but not part of that outer repo). `git pull` there tracks `origin/main` directly - no rsync needed.
- It's deployed via `docker compose` (`docker-compose.yml` in that directory) as containers `dailyptr-web` (port 8000) and `dailyptr-postgres`, plus a `dailyptr-sandbox-image-1` helper image that's built but never run standalone (used to spin up per-submission sandbox containers).
- **Database is Postgres** (`dailyptr-postgres`, a named Docker volume `dailyptr_pg_data` - not a host bind mount), not SQLite. Schema is managed by Alembic (`backend/alembic/`), run automatically via `app/database.py: init_db()` on every app startup (`alembic upgrade head` - idempotent, no separate manual migration step for a routine deploy). A brand-new model change needs a real migration file generated first though (`alembic revision --autogenerate`) - that's a code change to commit/push like any other, not something this skill generates for you.
- **Never delete the `dailyptr_pg_data` volume (or run `docker compose down -v`) as part of a routine deploy** - that wipes the live database. Only do that if the user explicitly asks to reset/wipe the database, and confirm with them first since it's irreversible.
- `.env` in that directory holds `SECRET_KEY`, `GOOGLE_CLIENT_ID`/`_SECRET`, `GOOGLE_REDIRECT_URI`, and `POSTGRES_PASSWORD` - all real values as of 2026-08-19 (Google sign-in is configured; `ANTHROPIC_API_KEY` is deliberately left unset, so AI grading falls back to plain self-report). Never print its contents.

## Steps

1. **Check the local tree.** Run `git status` in `/home/austin/dailyptr`.
   - If not on `main`, stop and tell the user - they need to merge/switch first.
   - If there are uncommitted changes, show them to the user and ask whether to commit (with a real message describing the change) before continuing. Don't silently commit whatever is lying around - follow the normal commit-only-when-asked rule, but here "deploy" implies the user wants their pending work shipped, so it's reasonable to ask "commit and push these?" rather than refusing outright.
   - If already committed and just unpushed, skip straight to pushing.

2. **Push.** `git push origin main`. If it's rejected (remote has commits you don't have), stop and tell the user - don't force-push.

3. **Update the server.**
   ```
   ssh austin@au5y-serv "cd /home/austin/docker/dailyptr && git pull"
   ```
   Confirm the pulled commit SHA matches what you just pushed.

4. **Rebuild and restart.**
   ```
   ssh austin@au5y-serv "cd /home/austin/docker/dailyptr && docker compose build && docker compose up -d"
   ```
   This recreates `dailyptr-web` from the new image; `dailyptr-postgres` and its named volume are untouched (compose only recreates a service whose config actually changed). Alembic runs automatically on `web`'s startup and applies any new migration file that shipped in this deploy.

5. **Verify.**
   ```
   ssh austin@au5y-serv "curl -s -o /dev/null -w '%{http_code}\n' http://localhost:8000/healthz"
   ssh austin@au5y-serv "docker logs dailyptr-web --tail 30"
   ```
   Expect `200` and a clean "Application startup complete" in the logs, no tracebacks. If it fails, check `docker compose ps` for a crash-looping container and read the fuller logs before reporting success.

6. Report back: the commit SHA now live, and the healthz result. Don't claim success without having actually checked step 5's output.

## Wiping the database (only if explicitly requested)

Not part of a normal deploy. If the user explicitly asks to reset the live database:
```
ssh austin@au5y-serv "cd /home/austin/docker/dailyptr && docker compose down -v && docker compose up -d"
```
`-v` removes the named volumes (`dailyptr_pg_data`), not just the containers - that's the actual wipe. Confirm with the user first - this deletes all accounts and progress on the live site with no undo.
