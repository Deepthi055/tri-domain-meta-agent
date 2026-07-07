from sqlalchemy import JSON

from models.profile import CareerProfile


def test_career_profile_skills_use_json_for_sqlite_compatibility():
    column_type = CareerProfile.__table__.c.current_skills.type
    assert isinstance(column_type, JSON)
