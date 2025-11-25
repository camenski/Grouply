# app/routers/auth.py
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from typing import Dict, Any

from app.services.auth import connexion, inscrire_utilisateur
from app.core.security import oauth2_scheme, get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])

class LoginIn(BaseModel):
    email: EmailStr
    password: str

class TokenOut(BaseModel):
    access_token: str
    token_type: str
    user: Dict[str, Any]

class RegisterIn(BaseModel):
    email: EmailStr
    password: str
    full_name: str | None = None

@router.post("/login", response_model=TokenOut)
async def login(payload: LoginIn):
    return await connexion(payload.email, payload.password)

@router.post("/register", response_model=dict)
async def register(payload: RegisterIn):
    user = await inscrire_utilisateur(payload.email, payload.password, payload.full_name)
    # ne pas renvoyer hashed_password côté client
    user_safe = {k: v for k, v in user.items() if k != "hashed_password"}
    return user_safe

@router.get("/me", response_model=dict)
async def me(current_user: dict = Depends(get_current_user)):
    user_safe = {k: v for k, v in current_user.items() if k != "hashed_password"}
    return user_safe
