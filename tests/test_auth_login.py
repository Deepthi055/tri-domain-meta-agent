from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from core.database import Base
from core.security import hash_password
from models.user import User
from services.auth_service import authenticate_user


def test_authenticate_user_accepts_name_as_login_identifier():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()

    try:
        password = "secret123"
        user = User(
            name="raksha",
            email="raksha@example.com",
            password_hash=hash_password(password),
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        authenticated = authenticate_user(db, "raksha", password)

        assert authenticated.id == user.id
        assert authenticated.email == "raksha@example.com"
    finally:
        db.close()
