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


def request_password_reset(db: Session, email: str) -> None:
    user = db.query(User).filter(User.email == email).first()
    # In development mode, return success for any email address.
    # A real implementation would generate a token and send an email.
    if user:
        # Token generation placeholder; no persistent token storage is implemented.
        token = create_access_token(data={"sub": user.id, "email": user.email})
        print(f"[password reset] token for {email}: {token}")


def change_password(db: Session, user_id: str, current_password: str, new_password: str) -> None:
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not verify_password(current_password, user.password_hash):
        raise ValueError("Current password is incorrect")
    user.password_hash = hash_password(new_password)
    db.add(user)
    db.commit()


def set_user_avatar(db: Session, user_id: str, avatar_url: str) -> User:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise ValueError("User not found")
    user.avatar_url = avatar_url
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def set_two_factor_enabled(db: Session, user_id: str, enabled: bool, current_password: str | None = None) -> User:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise ValueError("User not found")
    if enabled and not current_password:
        raise ValueError("Current password is required to enable two-factor authentication")
    if enabled and not verify_password(current_password, user.password_hash):
        raise ValueError("Current password is incorrect")
    user.two_factor_enabled = enabled
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def issue_token_for_user(user: User) -> str:
    return create_access_token(data={"sub": user.id, "email": user.email})
