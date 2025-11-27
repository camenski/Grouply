from typing import Dict, Any, Optional
from fastapi import HTTPException, status

from app.crud.user import (
    recuperer_utilisateur_par_id,
    recuperer_utilisateur_par_email,
    mettre_a_jour_utilisateur,
    supprimer_utilisateur,
    creer_utilisateur,
)

async def creer_user(email: str, password: str, full_name: Optional[str] = None) -> Dict[str, Any]:
    try:
        return await creer_utilisateur(email=email, password=password, full_name=full_name)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

async def get_user_by_id(user_id: int) -> Dict[str, Any]:
    user = await recuperer_utilisateur_par_id(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Utilisateur introuvable")
    return user

async def update_user(user_id: int, patch: Dict[str, Any]) -> Dict[str, Any]:
    try:
        return await mettre_a_jour_utilisateur(user_id, patch)
    except KeyError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Utilisateur introuvable")

async def delete_user(user_id: int) -> None:
    try:
        await supprimer_utilisateur(user_id)
    except KeyError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Utilisateur introuvable")
