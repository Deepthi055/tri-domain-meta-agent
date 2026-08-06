"""
app/routes/auth.py
"""
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from core.database import get_db
from core.security import get_current_user
from models.user import User
from schemas.auth import (
    UserCreate,
    UserOut,
    Token,
    ForgotPasswordRequest,
    ChangePasswordRequest,
    AvatarUploadRequest,
    TwoFactorRequest,
    UserUpdateRequest,
)
from services.auth_service import (
    register_user,
    authenticate_user,
    issue_token_for_user,
    request_password_reset,
    change_password,
    set_user_avatar,
    set_two_factor_enabled,
    update_user_name,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserOut)
def register(user_in: UserCreate, db: Session = Depends(get_db)):
    try:
        user = register_user(db, user_in)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return user


@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    try:
        user = authenticate_user(
            db,
            email=form_data.username,
            password=form_data.password,
        )
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))

    token = issue_token_for_user(user)
    return {"access_token": token, "token_type": "bearer"}


@router.post("/forgot-password")
def forgot_password(payload: ForgotPasswordRequest, db: Session = Depends(get_db)):
    request_password_reset(db, payload.email)
    return {"message": "Password reset link sent successfully"}


@router.post("/change-password")
def change_password_route(
    payload: ChangePasswordRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        change_password(db, current_user.id, payload.current_password, payload.new_password)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"message": "Password changed successfully"}


@router.post("/avatar", response_model=UserOut)
def upload_avatar(
    payload: AvatarUploadRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        user = set_user_avatar(db, current_user.id, payload.avatar_url)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return user


@router.post("/two-factor", response_model=UserOut)
def update_two_factor(
    payload: TwoFactorRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        user = set_two_factor_enabled(
            db,
            current_user.id,
            payload.enabled,
            payload.current_password,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return user


@router.put("/me", response_model=UserOut)
def update_current_user(
    payload: UserUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if payload.name is None:
        return current_user
    try:
        user = update_user_name(db, current_user.id, payload.name)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return user


@router.get("/me", response_model=UserOut)
def me(current_user: User = Depends(get_current_user)):
    # Ensure boolean fields are non-null for response validation (legacy DB rows)
    if getattr(current_user, "two_factor_enabled", None) is None:
        current_user.two_factor_enabled = False
    return current_user
