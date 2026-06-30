"""
app/routes/auth.py
"""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from core.database import get_db
from schemas.auth import UserCreate, UserOut, Token
from services.auth_service import register_user, authenticate_user, issue_token_for_user

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
    # OAuth2PasswordRequestForm uses "username" as the field name — we treat it as email
    try:
        user = authenticate_user(db, email=form_data.username, password=form_data.password)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))

    token = issue_token_for_user(user)
    return {"access_token": token, "token_type": "bearer"}
