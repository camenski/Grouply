from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import json

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError, ExpiredSignatureError

from app.core.config import SECRET_KEY, ALGORITHM
from app.storage.json_db import (
    trouver_utilisateur_par_email,
    trouver_utilisateur_par_id,
    verifier_mot_de_passe,
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login/oauth")

def creer_access_token(data: Dict[str, Any]) -> str:

    print("payload:",data)

    payload = {
        "iat": datetime.now(),
        "exp": datetime.now() + timedelta(hours=24),
        "sub": json.dumps(data)
    }
    token = jwt.encode(payload, SECRET_KEY, ALGORITHM)
    return token

def decoder_access_token(token: str) -> Dict[str, Any]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expiré")
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token invalide")

async def authentifier_utilisateur(email: str, password: str) -> Optional[Dict[str, Any]]:

    user = await trouver_utilisateur_par_email(email)
    print("\nuser:",user)
    if not user:
        return None
    hashed = user.get("hashed_password", "")  
    print(verifier_mot_de_passe(hashed, password))
    if not verifier_mot_de_passe(hashed, password):
        return None
    return user

async def get_current_user(request: Request) -> Dict[str, Any]:

    token: Optional[str] = request.cookies.get("access_token")
    if not token:
        auth = request.headers.get("authorization")
        if auth and auth.lower().startswith("bearer "):
            token = auth.split(" ", 1)[1]

    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Accès non autorisé")

    try:
        payload = decoder_access_token(token) 
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token invalide")

    user_id = payload.get("sub")
    id = user_id["sub"] # type: ignore
    if id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Accès non autorisé")


    user = await trouver_utilisateur_par_id(id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Utilisateur introuvable")

    return user

async def get_current_active_user(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:

    if not current_user.get("is_active", True):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Utilisateur inactif")
    return current_user
