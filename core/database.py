"""
app/core/database.py

SQLAlchemy engine + session factory + declarative Base + FastAPI dependency.
"""
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker, declarative_base

from core.config import settings

engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True, echo=False)

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
    _apply_sqlite_schema_fixes()


def _apply_sqlite_schema_fixes():
    """Apply missing SQLite schema columns when the table already exists."""
    inspector = inspect(engine)
    if not inspector.has_table('users'):
        return

    existing_columns = {column['name'] for column in inspector.get_columns('users')}
    with engine.connect() as connection:
        if 'avatar_url' not in existing_columns:
            connection.execute(text('ALTER TABLE users ADD COLUMN avatar_url VARCHAR(1024)'))
        if 'updated_at' not in existing_columns:
            connection.execute(text('ALTER TABLE users ADD COLUMN updated_at DATETIME'))
        if 'two_factor_enabled' not in existing_columns:
            connection.execute(text('ALTER TABLE users ADD COLUMN two_factor_enabled BOOLEAN'))
        if 'two_factor_secret' not in existing_columns:
            connection.execute(text('ALTER TABLE users ADD COLUMN two_factor_secret VARCHAR(255)'))

    if inspector.has_table('career_profiles'):
        career_columns = {column['name'] for column in inspector.get_columns('career_profiles')}
        with engine.connect() as connection:
            if 'education' not in career_columns:
                connection.execute(text('ALTER TABLE career_profiles ADD COLUMN education VARCHAR(120)'))
            if 'preferred_roles' not in career_columns:
                connection.execute(text('ALTER TABLE career_profiles ADD COLUMN preferred_roles VARCHAR(255)'))
            if 'resume' not in career_columns:
                connection.execute(text('ALTER TABLE career_profiles ADD COLUMN resume VARCHAR(2000)'))

    if inspector.has_table('health_profiles'):
        health_columns = {column['name'] for column in inspector.get_columns('health_profiles')}
        with engine.connect() as connection:
            if 'medical_conditions' not in health_columns:
                connection.execute(text('ALTER TABLE health_profiles ADD COLUMN medical_conditions VARCHAR(500)'))
            if 'lifestyle' not in health_columns:
                connection.execute(text('ALTER TABLE health_profiles ADD COLUMN lifestyle VARCHAR(50)'))
            if 'workout' not in health_columns:
                connection.execute(text('ALTER TABLE health_profiles ADD COLUMN workout VARCHAR(120)'))
            if 'health_goals' not in health_columns:
                connection.execute(text('ALTER TABLE health_profiles ADD COLUMN health_goals VARCHAR(255)'))
            if 'water_intake' not in health_columns:
                connection.execute(text('ALTER TABLE health_profiles ADD COLUMN water_intake FLOAT'))

    if inspector.has_table('finance_profiles'):
        finance_columns = {column['name'] for column in inspector.get_columns('finance_profiles')}
        with engine.connect() as connection:
            if 'investments' not in finance_columns:
                connection.execute(text('ALTER TABLE finance_profiles ADD COLUMN investments VARCHAR(255)'))
            if 'financial_goals' not in finance_columns:
                connection.execute(text('ALTER TABLE finance_profiles ADD COLUMN financial_goals VARCHAR(255)'))
            if 'budget' not in finance_columns:
                connection.execute(text('ALTER TABLE finance_profiles ADD COLUMN budget VARCHAR(500)'))
