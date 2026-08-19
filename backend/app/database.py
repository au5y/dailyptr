from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

from . import config

connect_args = {"check_same_thread": False} if config.DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(config.DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    # Import models so they're registered on Base's metadata before create_all.
    from . import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
    _migrate_add_onboarded_column()


def _migrate_add_onboarded_column():
    """create_all only adds brand-new tables, not columns on tables that
    already exist - so a pre-existing users table (from before `onboarded`
    was added) needs a one-time ALTER TABLE. Accounts that already exist at
    that point already have their tracks set up, so they're backfilled to
    onboarded=True rather than being sent through topic selection."""
    if not config.DATABASE_URL.startswith("sqlite"):
        return
    with engine.begin() as conn:
        from sqlalchemy import text

        cols = {row[1] for row in conn.exec_driver_sql("PRAGMA table_info(users)")}
        if "onboarded" not in cols:
            conn.exec_driver_sql("ALTER TABLE users ADD COLUMN onboarded BOOLEAN DEFAULT 0")
            conn.execute(text("UPDATE users SET onboarded = 1"))
