import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse, PlainTextResponse, RedirectResponse
from starlette.middleware.sessions import SessionMiddleware

from . import auth, config
from .database import init_db, SessionLocal
from .seed import seed_content
from .routers import challenges, quiz, code_review, critical_reasoning, concept

# The frontend is a handful of static files. docker-compose mounts the repo's
# ./frontend directory to /app/frontend inside the container; running locally
# with `uvicorn app.main:app` from backend/, it lives one directory further
# up at ../frontend relative to this file. Try both; API-only use is fine too.
_APP_DIR = os.path.dirname(os.path.abspath(__file__))  # .../app
_CANDIDATES = [
    os.environ.get("FRONTEND_DIR"),
    os.path.join(os.path.dirname(_APP_DIR), "frontend"),               # docker: /app/frontend
    os.path.join(os.path.dirname(os.path.dirname(_APP_DIR)), "frontend"),  # local: repo_root/frontend
]
FRONTEND_DIR = next((c for c in _CANDIDATES if c and os.path.isdir(c)), None)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    db = SessionLocal()
    try:
        seed_content(db)
    finally:
        db.close()
    yield


app = FastAPI(title="dailyptr", lifespan=lifespan)
app.add_middleware(auth.AuthMiddleware)
# Outermost (added last -> runs first): gives every request a request.session,
# which authlib's OAuth client uses to stash CSRF state/nonce across the
# redirect-to-Google-and-back handshake below.
app.add_middleware(SessionMiddleware, secret_key=config.SECRET_KEY, same_site="lax")

app.include_router(challenges.router)
app.include_router(quiz.router)
app.include_router(code_review.router)
app.include_router(critical_reasoning.router)
app.include_router(concept.router)


@app.get("/healthz")
def healthz():
    return PlainTextResponse("ok")


@app.get("/login")
def login_page():
    if FRONTEND_DIR:
        return FileResponse(os.path.join(FRONTEND_DIR, "login.html"))
    return HTMLResponse("<h1>dailyptr</h1><p>Login page unavailable.</p>")


@app.get("/auth/google/login")
async def google_login(request: Request):
    redirect_uri = config.GOOGLE_REDIRECT_URI or str(request.url_for("google_callback"))
    return await auth.oauth.google.authorize_redirect(request, redirect_uri)


def _relative_to_root(request: Request) -> str:
    """A relative "climb back to app root" path from the current request's
    URL, so it also works when served under a reverse-proxy path prefix
    (e.g. /dailyptr/) - a bare "." only resolves to root from a top-level
    path like /login; nested paths like /auth/google/callback need to climb
    back out ("../..") or they land on their own parent directory instead."""
    depth = request.url.path.count("/") - 1
    return "../" * depth if depth else "."


def _log_in_and_redirect(request: Request, user) -> RedirectResponse:
    # A brand-new user isn't subscribed to any track yet, and isn't
    # backfilled with history until they pick topics on the onboarding
    # screen (see /api/onboarding) - the frontend shows that screen whenever
    # /api/me reports onboarded=False, which is what `user.onboarded`
    # defaults to (see models.User).
    response = RedirectResponse(url=_relative_to_root(request), status_code=303)
    auth.set_session_cookie(response, request, user)
    return response


@app.get("/auth/google/callback", name="google_callback")
async def google_callback(request: Request):
    token = await auth.oauth.google.authorize_access_token(request)
    claims = token.get("userinfo") or {}

    db = SessionLocal()
    try:
        user, _is_new = auth.find_or_create_google_user(db, claims["sub"], claims.get("email", ""), claims.get("name", ""))
        return _log_in_and_redirect(request, user)
    finally:
        db.close()


@app.post("/auth/guest")
def guest_login(request: Request):
    """No Google account needed - a disposable local account, same as any
    other User except its identity is a random token instead of a Google
    sub/email. Progress is still saved server-side (this isn't a real
    offline/PWA mode - the server itself is still required), it just skips
    the OAuth round trip for someone who doesn't want to sign in with Google."""
    db = SessionLocal()
    try:
        user = auth.create_guest_user(db)
        return _log_in_and_redirect(request, user)
    finally:
        db.close()


@app.post("/logout")
def logout():
    response = RedirectResponse(url="login", status_code=303)
    response.delete_cookie(auth.COOKIE_NAME)
    return response


if FRONTEND_DIR:
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

    @app.get("/")
    def serve_index():
        return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))
