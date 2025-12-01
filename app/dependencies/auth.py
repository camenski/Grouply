from typing import Optional, Dict, Any
from fastapi import Request, HTTPException, status, Depends
from app.core.security import decoder_access_token 
from app.services.auth import recuperer_profil
import json
from fastapi import Request

async def get_token_from_request(request: Request) -> Optional[str]:

    token = request.cookies.get("access_token")
    if token:
        return token

    auth = request.headers.get("authorization")
    if auth and auth.lower().startswith("bearer "):
        return auth.split(" ", 1)[1]

    return None

async def get_current_user(request: Request) -> Dict[str, Any]:
    token = await get_token_from_request(request)
    print("DEBUG token:", token)
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Non authentifié")

    try:
        payload = decoder_access_token(token) 
    except Exception as e:
        print("DEBUG token decode error:", e)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token invalide")

    sub = json.loads(payload.get("sub")) # type: ignore
    print("\n\n\n\n", sub["sub"]) # type: ignore
    if sub is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token invalide: 'sub' manquant")

    try:
        user_id = int(sub["sub"])
    except (TypeError, ValueError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Identifiant utilisateur invalide dans le token")

    user = await recuperer_profil(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Utilisateur introuvable")

    return user



async def get_current_user_optional(request: Request):
    try:
        return await get_current_user(request)
    except Exception:
        return None