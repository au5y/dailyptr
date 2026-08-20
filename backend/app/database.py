import os

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

from . import config

connect_args = {"check_same_thread": False} if config.DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(config.DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

_BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Brings the database up to the latest schema by running Alembic's
    migrations (see alembic/versions/) - replaces the old
    Base.metadata.create_all() + hand-rolled per-column ALTER TABLE patch,
    which only ever worked for SQLite and needed a new one-off patch
    function for every future schema change. `alembic upgrade head` is
    idempotent (no-ops if already current), so calling this on every app
    startup - same as before - is still safe and requires no separate
    manual migration step at deploy time."""
    alembic_cfg = Config(os.path.join(_BACKEND_DIR, "alembic.ini"))
    # Overridden with an absolute path so this resolves correctly regardless
    # of the process's current working directory (alembic.ini's own
    # script_location = alembic is only a relative path).
    alembic_cfg.set_main_option("script_location", os.path.join(_BACKEND_DIR, "alembic"))
    command.upgrade(alembic_cfg, "head")
