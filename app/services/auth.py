from typing import Optional, Dict, Any
from datetime import timedelta

from fastapi import HTTPException, status

from app.core.security import creer_access_token, authentifier_utilisateur
from app.storage.json_db import trouver_utilisateur_par_id, hacher_mot_de_passe

ACCESS_TOKEN_EXPIRE_MINUTES = 30 

async def connexion(email: str, password: str) -> Dict[str, Any]:
    """
    Vérifie les identifiants et retourne un dict contenant access_token et user.
    Lève HTTPException en cas d'échec.
    """
    user = await authentifier_utilisateur(email, password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Identifiants invalides")
    token_data = {"sub": str(user["id"])}
    token = creer_access_token(token_data, expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    return {"access_token": token, "token_type": "bearer", "user": user}

async def inscrire_utilisateur(email: str, password: str, full_name: Optional[str] = None) -> Dict[str, Any]:
    """
    Crée un nouvel utilisateur. Retourne l'utilisateur créé.
    Utilise le hachage de mot de passe fourni par json_db.
    """
    from app.crud.user import creer_utilisateur 
    try:
        user = await creer_utilisateur(email=email, password=password, full_name=full_name)
        return user
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

async def recuperer_profil(user_id: int) -> Dict[str, Any]:
    user = await trouver_utilisateur_par_id(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Utilisateur introuvable")
    # Ne pas renvoyer le hashed_password dans la réponse publique
    safe = {k: v for k, v in user.items() if k != "hashed_password"}
    return safe
