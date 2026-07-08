"""
app/routes/auth.py
"""
from typing import Annotated

from fastapi import APIRouter, Depends, Form, HTTPException
from sqlalchemy.orm import Session

from core.database import get_db
from schemas.auth import UserCreate, UserOut, Token
from services.auth_service import register_user, authenticate_user, issue_token_for_user

router = APIRouter(prefix="/auth", tags=["auth"])


def login_form(
    email: Annotated[str | None, Form()] = None,
    username: Annotated[str | None, Form()] = None,
    password: Annotated[str | None, Form()] = None,
):
    login_value = email or username
    if not login_value:
        raise HTTPException(status_code=422, detail="Email or username is required")
    if not password:
        raise HTTPException(status_code=422, detail="Password is required")
    return {"email": login_value, "password": password}


@router.post("/register", response_model=UserOut)
def register(user_in: UserCreate, db: Session = Depends(get_db)):
    try:
        user = register_user(db, user_in)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return user


@router.post("/login", response_model=Token)
def login(form_data: dict = Depends(login_form), db: Session = Depends(get_db)):
    try:
        user = authenticate_user(
            db,
            email=form_data["email"],
            password=form_data["password"],
        )
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))

    token = issue_token_for_user(user)
    return {"access_token": token, "token_type": "bearer"}
