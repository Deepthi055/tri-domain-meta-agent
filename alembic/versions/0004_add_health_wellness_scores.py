"""add mood, stress, and anxiety scores to health profiles

Revision ID: 0004
Revises: 0003
Create Date: 2026-09-16 00:00:00
"""
from alembic import op
import sqlalchemy as sa


revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("health_profiles", sa.Column("mood_score", sa.Integer(), nullable=True))
    op.add_column("health_profiles", sa.Column("stress_level", sa.Integer(), nullable=True))
    op.add_column("health_profiles", sa.Column("anxiety_level", sa.Integer(), nullable=True))
    op.add_column("health_profiles", sa.Column("active_days_per_week", sa.Integer(), nullable=True))


def downgrade():
    op.drop_column("health_profiles", "anxiety_level")
    op.drop_column("health_profiles", "stress_level")
    op.drop_column("health_profiles", "mood_score")
    op.drop_column("health_profiles", "active_days_per_week")