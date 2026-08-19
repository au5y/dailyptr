"""
"Sign in with Google" - the app has no password of its own. A user's
identity is Google's `sub` claim (find-or-create a local User row keyed on
it the first time we see it); everything after that is our own signed
session cookie (itsdangerous, no server-side session store needed).
Guest accounts (see create_guest_user) are the one exception - a random
token stands in for the Google identity so someone can play without a
Google account at all.
"""
import uuid

from authlib.integrations.starlette_client import OAuth
from fastapi import HTTPException, Request
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer
from sqlalchemy.orm import Session
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import RedirectResponse, Response

from . import config, models
from .database import SessionLocal

COOKIE_NAME = "dailyptr_session"
SESSION_MAX_AGE_SECONDS = 30 * 24 * 60 * 60  # 30 days

# Paths reachable without a session.
_OPEN_PATH_PREFIXES = ("/login", "/auth", "/static", "/healthz")

_serializer = URLSafeTimedSerializer(config.SECRET_KEY)

oauth = OAuth()
oauth.register(
    name="google",
    client_id=config.GOOGLE_CLIENT_ID,
    client_secret=config.GOOGLE_CLIENT_SECRET,
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"},
)


def make_session_cookie(user_id: int) -> str:
    return _serializer.dumps({"user_id": user_id})


def _user_id_from_cookie(value: str | None) -> int | None:
    if not value:
        return None
    try:
        data = _serializer.loads(value, max_age=SESSION_MAX_AGE_SECONDS)
        return data.get("user_id")
    except (BadSignature, SignatureExpired):
        return None


def find_or_create_google_user(db: Session, sub: str, email: str, name: str) -> tuple[models.User, bool]:
    """Returns (user, created)."""
    user = db.query(models.User).filter(models.User.google_sub == sub).one_or_none()
    if user:
        return user, False
    user = models.User(google_sub=sub, email=email, name=name)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user, True


def create_guest_user(db: Session) -> models.User:
    token = uuid.uuid4().hex
    user = models.User(google_sub=f"guest-{token}", email=f"guest-{token}@offline.local", name="Guest")
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


class AuthMiddleware(BaseHTTPMiddleware):
    """Resolves the session cookie into a User (stashed on request.state.user)
    when present/valid, and blocks access to everything outside the open
    paths for anyone without one."""

    async def dispatch(self, request: Request, call_next):
        request.state.user = None

        user_id = _user_id_from_cookie(request.cookies.get(COOKIE_NAME))
        if user_id is not None:
            db = SessionLocal()
            try:
                request.state.user = db.get(models.User, user_id)
            finally:
                db.close()

        path = request.url.path
        if any(path == p or path.startswith(p + "/") for p in _OPEN_PATH_PREFIXES):
            return await call_next(request)

        if request.state.user is not None:
            return await call_next(request)

        if path.startswith("/api/"):
            return Response(status_code=401, content="Not authenticated")
        # Relative redirect (no leading slash) so this also works when the
        # app is served under a reverse-proxy path prefix (e.g. /dailyptr/).
        return RedirectResponse(url="login")


def get_current_user(request: Request) -> models.User:
    """FastAPI dependency for routers - AuthMiddleware already guarantees a
    logged-in user reached this point for any non-open path, so this just
    surfaces it (the 401 is a defensive fallback, not the normal path)."""
    user = getattr(request.state, "user", None)
    if user is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user


def set_session_cookie(response: Response, request: Request, user: models.User) -> None:
    response.set_cookie(
        COOKIE_NAME,
        make_session_cookie(user.id),
        httponly=True,
        samesite="lax",
        secure=request.url.scheme == "https",
        max_age=SESSION_MAX_AGE_SECONDS,
    )
