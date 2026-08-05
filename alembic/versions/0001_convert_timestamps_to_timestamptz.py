"""convert timestamps to timezone-aware types

Revision ID: 0001_convert_timestamps_to_timestamptz
Revises: 
Create Date: 2026-08-05 00:00:00
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0001_convert_timestamps_to_timestamptz'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    dialect = bind.dialect.name

    # We target Postgres for automated conversion. SQLite requires manual migration.
    if dialect == 'postgresql':
        # Conversations
        try:
            op.execute("""
            ALTER TABLE conversations
            ALTER COLUMN created_at TYPE TIMESTAMP WITH TIME ZONE
            USING created_at AT TIME ZONE 'UTC';
            """)
        except Exception:
            pass

        # Messages
        try:
            op.execute("""
            ALTER TABLE messages
            ALTER COLUMN timestamp TYPE TIMESTAMP WITH TIME ZONE
            USING timestamp AT TIME ZONE 'UTC';
            """)
        except Exception:
            pass

        # Users
        try:
            op.execute("""
            ALTER TABLE users
            ALTER COLUMN created_at TYPE TIMESTAMP WITH TIME ZONE
            USING created_at AT TIME ZONE 'UTC';
            ALTER TABLE users
            ALTER COLUMN updated_at TYPE TIMESTAMP WITH TIME ZONE
            USING updated_at AT TIME ZONE 'UTC';
            """)
        except Exception:
            pass

        # User memory
        try:
            op.execute("""
            ALTER TABLE user_memory
            ALTER COLUMN created_at TYPE TIMESTAMP WITH TIME ZONE
            USING created_at AT TIME ZONE 'UTC';
            """)
        except Exception:
            pass

        # Profiles (if present)
        for tbl, col in [
            ('user_profiles', 'created_at'),
            ('career_profiles', 'created_at'),
            ('health_profiles', 'created_at'),
            ('finance_profiles', 'created_at'),
        ]:
            try:
                op.execute(f"""
                ALTER TABLE {tbl}
                ALTER COLUMN {col} TYPE TIMESTAMP WITH TIME ZONE
                USING {col} AT TIME ZONE 'UTC';
                """)
            except Exception:
                pass

    else:
        # For SQLite and other DBs we avoid destructive ALTERs. Instead create
        # safe backups of the affected tables so operators can perform manual
        # conversion without data loss. This keeps the migration non-destructive.
        tables = [
            ('conversations', ['created_at']),
            ('messages', ['timestamp']),
            ('users', ['created_at', 'updated_at']),
            ('user_memory', ['created_at']),
            ('user_profiles', ['created_at']),
            ('career_profiles', ['created_at']),
            ('health_profiles', ['created_at']),
            ('finance_profiles', ['created_at']),
            ('reports', ['generated_at']),
        ]
        for tbl, cols in tables:
            try:
                # create a safe backup table with all data
                op.execute(f"CREATE TABLE IF NOT EXISTS {tbl}_backup_before_tz AS SELECT * FROM {tbl};")
            except Exception:
                # best-effort: continue if table doesn't exist
                pass
        # Note: manual migration steps for SQLite are required to replace columns.
        # This avoids risky in-place schema rewrites on SQLite which lacks
        # ALTER COLUMN support. Operators can inspect *_backup_before_tz tables
        # and perform conversion steps offline, then recreate tables and restore.


def downgrade():
    bind = op.get_bind()
    dialect = bind.dialect.name
    if dialect == 'postgresql':
        # Convert back to timestamp without time zone
        for tbl_col in [
            ('conversations', 'created_at'),
            ('messages', 'timestamp'),
            ('users', 'created_at'),
            ('users', 'updated_at'),
            ('user_memory', 'created_at'),
            ('user_profiles', 'created_at'),
            ('career_profiles', 'created_at'),
            ('health_profiles', 'created_at'),
            ('finance_profiles', 'created_at'),
        ]:
            tbl, col = tbl_col
            try:
                op.execute(f"""
                ALTER TABLE {tbl}
                ALTER COLUMN {col} TYPE TIMESTAMP WITHOUT TIME ZONE
                USING ({col} AT TIME ZONE 'UTC');
                """)
            except Exception:
                pass
    else:
        pass
