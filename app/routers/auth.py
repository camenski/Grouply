from fastapi import APIRouter, Depends, Request, Form
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import RedirectResponse, Response
from pydantic import BaseModel, EmailStr
from typing import Dict, Any
from fastapi.templating import Jinja2Templates
from pathlib import Path
from datetime import timedelta

from app.services.auth import connexion, inscrire_utilisateur
from app.core.security import get_current_user 

router = APIRouter(prefix="/auth", tags=["auth"])
BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

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

COOKIE_MAX_AGE = int(timedelta(minutes=30).total_seconds())

@router.get("/login", include_in_schema=False)
async def login_get(request: Request):
    return templates.TemplateResponse("login.html", {"request": request, "message": None})

@router.get("/register", include_in_schema=False)
async def register_get(request: Request):
    return templates.TemplateResponse("register.html", {"request": request, "message": None})

@router.post("/login", include_in_schema=False)
async def login_form(request: Request, email: str = Form(...), password: str = Form(...)):
    try:
        result = await connexion(email, password)
    except Exception as e:
        return templates.TemplateResponse("login.html", {"request": request, "message": str(e)})

    token = result.get("access_token")
    if not token:
        return templates.TemplateResponse("login.html", {"request": request, "message": "Erreur d'authentification : token manquant."})

    token_str: str = str(token) 
    response = RedirectResponse(url="/", status_code=303)
    response.set_cookie("access_token", token_str, httponly=True, max_age=COOKIE_MAX_AGE, samesite="lax")
    return response


@router.post("/login/oauth", response_model=TokenOut)
async def login_oauth(form_data: OAuth2PasswordRequestForm = Depends()):
    email = form_data.username
    password = form_data.password
    return await connexion(email, password)

@router.post("/register", include_in_schema=False)
async def register_form(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    full_name: str | None = Form(None),
):
    if len(password) < 8:
        return templates.TemplateResponse("register.html", {"request": request, "message": "Le mot de passe doit contenir au moins 8 caractères."})

    try:
        user = await inscrire_utilisateur(email, password, full_name)
    except Exception as e:
        return templates.TemplateResponse("register.html", {"request": request, "message": str(e)})

    try:
        result = await connexion(email, password)
        token = result.get("access_token")
        if not token:
            return templates.TemplateResponse("register.html", {"request": request, "message": "Inscription réussie mais impossible de créer la session."})

        token_str: str = str(token)
        response = RedirectResponse(url="/", status_code=303)
        response.set_cookie("access_token", token_str, httponly=True, max_age=COOKIE_MAX_AGE, samesite="lax")
        return response
    except Exception:
        return RedirectResponse(url="/login", status_code=303)


@router.post("/logout", include_in_schema=False)
async def logout(request: Request):
    response = RedirectResponse(url="/", status_code=303)
    response.delete_cookie("access_token")
    return response

@router.get("/me", include_in_schema=False)
async def me_page(request: Request, current_user: dict = Depends(get_current_user)):
    user_safe = {k: v for k, v in current_user.items() if k != "hashed_password"}
    return templates.TemplateResponse("me.html", {"request": request, "user": user_safe})
