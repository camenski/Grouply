from datetime import datetime, timedelta
from typing import Optional, Dict, Any

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError, ExpiredSignatureError

from app.core.config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES
from app.storage.json_db import (
    trouver_utilisateur_par_email,
    trouver_utilisateur_par_id,
    verifier_mot_de_passe,
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login/oauth")

def creer_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:

    to_encode = data.copy()
    now = datetime.utcnow()
    expire = now + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"iat": int(now.timestamp()), "exp": int(expire.timestamp())})
    token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
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
    if not user:
        return None
    hashed = user.get("hashed_password") or user.get("password") 
    if not hashed or not verifier_mot_de_passe(hashed, password):
        return None
    return user

async def get_current_user(token: str = Depends(oauth2_scheme)) -> Dict[str, Any]:

    payload = decoder_access_token(token)
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Accès non autorisé")
    try:
        user_id_int = int(user_id)
    except (TypeError, ValueError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Identifiant utilisateur invalide dans le token")
    user = await trouver_utilisateur_par_id(user_id_int)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Utilisateur introuvable")
    return user

async def get_current_active_user(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:

    if not current_user.get("is_active", True):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Utilisateur inactif")
    return current_user
