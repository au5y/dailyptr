---
name: deploy
description: Push the local dailyptr repo's committed changes to origin main, then SSH to austin@au5y-serv and update its self-hosted copy (git pull, rebuild the Docker image, restart the container) so the live site matches main. Use when the user asks to deploy, ship, push and update the server, or refresh the hosted site.
---

Ground truth about this setup (verified 2026-08-19 - re-check if any of it seems wrong):

- Local repo: `/home/austin/dailyptr`, remote `origin` = `git@github.com:au5y/dailyptr.git`.
- Live host: `austin@au5y-serv` (SSH key auth already works, no password needed).
- On au5y-serv the site is a plain `git clone` of the same repo at `/home/austin/docker/dailyptr` (sibling to au5y's other `docker/*` compose services, but not part of that outer repo). `git pull` there tracks `origin/main` directly - no rsync needed.
- It's deployed via `docker compose` (`docker-compose.yml` in that directory) as container `dailyptr-web`, port 8000, plus a `dailyptr-sandbox-image-1` helper image that's built but never run standalone (used to spin up per-submission sandbox containers).
- `data/app.db` (SQLite) and `data/sandbox-tmp/` are bind-mounted from the host and owned by root (created by the container running as root) - they persist across rebuilds/restarts as long as you don't delete them. **Never delete `data/` as part of a routine deploy** - that wipes the live database. Only do that if the user explicitly asks to reset/wipe the database, and confirm with them first since it's irreversible.
- No `.env` file exists on the server and no `SECRET_KEY`/`GOOGLE_CLIENT_ID`/`GOOGLE_CLIENT_SECRET`/`ANTHROPIC_API_KEY` are set - the live site currently runs with the insecure default session secret and Google sign-in unconfigured (guest login only). Not this skill's job to fix, but worth mentioning to the user once per session if it comes up.

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
   This recreates `dailyptr-web` from the new image; the bind-mounted `data/` dir (and thus the database) is untouched. Any new SQLAlchemy tables/columns are applied automatically on startup via `app/database.py`'s migration in `init_db()` - no manual migration step needed as of the schema this skill description was written against (check `backend/app/database.py` if that ever changes).

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
ssh austin@au5y-serv "cd /home/austin/docker/dailyptr && docker compose down && rm -rf data && docker compose up -d"
```
Confirm with the user first - this deletes all accounts and progress on the live site with no undo.
