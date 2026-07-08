"""
app/services/auth_service.py
"""
from sqlalchemy.orm import Session

from core.security import hash_password, verify_password, create_access_token
from models.user import User
from schemas.auth import UserCreate


def register_user(db: Session, user_in: UserCreate) -> User:
    existing = db.query(User).filter(User.email == user_in.email).first()
    if existing:
        raise ValueError("Email already registered")

    user = User(
        name=user_in.name,
        email=user_in.email,
        password_hash=hash_password(user_in.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, email: str, password: str) -> User:
    user = (
        db.query(User)
        .filter((User.email == email) | (User.name == email))
        .first()
    )
    if not user or not verify_password(password, user.password_hash):
        raise ValueError("Invalid email or password")
    return user


def issue_token_for_user(user: User) -> str:
    return create_access_token(data={"sub": user.id, "email": user.email})
