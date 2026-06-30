"""
app/core/database.py

SQLAlchemy engine + session factory + declarative Base + FastAPI dependency.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from core.config import settings

engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True,echo=False)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """FastAPI dependency that yields a DB session per request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    Creates all tables if they don't exist. Fine for first-run/dev.
    In production, rely on Alembic migrations instead (see alembic/).
    """
    # Import all models so they register on Base.metadata before create_all
    from models import user, profile, conversation, memory, report  # noqa: F401

    Base.metadata.create_all(bind=engine)
