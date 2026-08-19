import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from .database import init_db, SessionLocal
from .day_service import backfill_history
from .seed import seed_content
from .routers import challenges, quiz, coding, concept

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
        # Give System Design a month of pre-populated history immediately,
        # rather than only creating days lazily as the calendar is clicked into.
        backfill_history(db, "system_design", days=30)
    finally:
        db.close()
    yield


app = FastAPI(title="dailyptr", lifespan=lifespan)

app.include_router(challenges.router)
app.include_router(quiz.router)
app.include_router(coding.router)
app.include_router(concept.router)

if FRONTEND_DIR:
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

    @app.get("/")
    def serve_index():
        return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))
