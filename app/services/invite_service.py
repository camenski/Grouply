# app/services/invite_service.py
from fastapi import HTTPException, status
from datetime import datetime
from typing import Dict, Any

from app.storage.json_db import (
    creer_invitation,
    obtenir_invite_par_token,
    utiliser_invite,
)
from app.crud.groupe import obtenir_groupe_par_id
from app.crud.user import recuperer_utilisateur_par_id

async def generer_invitation(group_id: int, current_user: Dict[str, Any], expires_in_days: int = 7, max_uses: int = 1) -> Dict[str, Any]:
    group = await obtenir_groupe_par_id(group_id)
    if not group:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Groupe introuvable")
    if group.get("owner_id") != current_user["id"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Seul le propriétaire peut créer une invitation")
    return await creer_invitation(group_id=group_id, created_by=current_user["id"], expires_in_days=expires_in_days, max_uses=max_uses)

async def rejoindre_via_invite(token: str, current_user: Dict[str, Any]) -> Dict[str, Any]:
    inv = await obtenir_invite_par_token(token)
    if not inv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invitation introuvable")
    if inv.get("revoked"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invitation révoquée")
    if inv.get("expires_at") and datetime.fromisoformat(inv["expires_at"]) < datetime.utcnow():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invitation expirée")
    try:
        return await utiliser_invite(token, current_user["id"])
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
