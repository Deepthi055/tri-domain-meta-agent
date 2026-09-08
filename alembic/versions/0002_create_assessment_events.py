"""create assessment events

Revision ID: 0002_create_assessment_events
Revises: 0001_convert_timestamps_to_timestamptz
Create Date: 2026-09-04 13:08:00
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "0002_create_assessment_events"
down_revision = "0001_convert_timestamps_to_timestamptz"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "assessment_events",
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=False),
            nullable=False,

        sa.Column("domain", sa.String(length=20), nullable=False),
        sa.Column("assessment_type", sa.String(length=50), nullable=False),
        sa.Column("value", sa.Float(), nullable=False),
        sa.Column("value_kind", sa.String(length=20), nullable=False),
        sa.Column("target_role", sa.String(length=120), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column("source", sa.String(length=100), nullable=False),
        sa.Column("calculation_version", sa.String(length=50), nullable=False),
        sa.Column("details", sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade():
    op.drop_table("assessment_events")
