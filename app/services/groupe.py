from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from fastapi import HTTPException, status
import secrets

from app.crud.groupe import (
    creer_groupe,
    recuperer_groupe,
    mettre_a_jour_groupe,
    supprimer_groupe,
    ajouter_membre,
    retirer_membre,
    creer_invitation,
    obtenir_invitation_par_token,
    incrementer_utilisation_invite,lister_groupes_par_utilisateur
)
from app.crud.tache import (
    creer_tache,
    supprimer_tache,
    lister_taches_par_groupe
)
from app.crud.user import recuperer_utilisateur_par_id
from app.storage.json_db import charger_db, sauvegarder_db

async def creer_nouveau_groupe(
    name: str,
    description: Optional[str],
    owner_id: Optional[int],
    current_user: dict
) -> Dict[str, Any]:
    if owner_id is None:
        owner_id = current_user.get("id")
        if not owner_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Utilisateur invalide"
            )

    db = await charger_db()

    new_id = max([g["id"] for g in db.get("groups", [])] or [0]) + 1

    owner = await recuperer_utilisateur_par_id(owner_id)
    owner_name = owner.get("full_name") if owner else None

    new_group = {
        "id": new_id,
        "name": name,
        "description": description,
        "owner_id": owner_id,
        "owner_name": owner_name,
        "members": [owner_id],
        "tasks": []
    }

    db.setdefault("groups", []).append(new_group)
    await sauvegarder_db(db)

    return new_group


async def modifier_groupe(group_id: int, patch: Dict[str, Any], current_user: dict) -> Dict[str, Any]:
    group = await recuperer_groupe(group_id)
    if not group:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Groupe introuvable")
    if group.get("owner_id") != current_user.get("id"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Seul le créateur peut modifier le groupe")
    return await mettre_a_jour_groupe(group_id, patch)


async def supprimer_groupe_si_createur(group_id: int, current_user: dict) -> None:
    group = await recuperer_groupe(group_id)
    if not group:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Groupe introuvable")
    if group.get("owner_id") != current_user.get("id"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Seul le créateur peut supprimer le groupe")
    await supprimer_groupe(group_id)


async def retirer_membre_du_groupe(group_id: int, user_id: int, current_user: dict) -> None:
    group = await recuperer_groupe(group_id)
    if not group:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Groupe introuvable")
    if group.get("owner_id") != current_user.get("id"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Seul le créateur peut retirer des membres")
    await retirer_membre(group_id, user_id)


async def creer_tache_dans_groupe(
    group_id: int,
    title: str,
    description: Optional[str],
    due_date: Optional[str],
    current_user: dict
) -> Dict[str, Any]:
    group = await recuperer_groupe(group_id)
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Groupe introuvable"
        )

    return await creer_tache(
        title=title,
        description=description,
        group_id=group_id,
        due_date=due_date,
     )


async def supprimer_tache_du_groupe(group_id: int, task_id: int, current_user: dict) -> None:
    group = await recuperer_groupe(group_id)
    if not group:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Groupe introuvable")
    if group.get("owner_id") != current_user.get("id"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Seul le créateur peut supprimer les tâches du groupe")
    await supprimer_tache(task_id)


async def lister_taches_du_groupe(group_id: int, current_user: dict) -> List[Dict[str, Any]]:
    group = await recuperer_groupe(group_id)
    if not group:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Groupe introuvable")
    return await lister_taches_par_groupe(group_id)

async def generer_invitation_simple(group_id: int, current_user: dict, base_url: str = "http://localhost:8000") -> dict:
    token = secrets.token_urlsafe(16)
    expires_at = (datetime.now() + timedelta(days=7)).isoformat()
    invite = await creer_invitation(group_id, token, current_user.get("id"), expires_at)
    return {
        "url": f"{base_url}/groups/invite/{token}",
        "invite": invite,
    }

async def rejoindre_via_invite_simple(token: str, current_user: dict) -> dict:
    invite = await obtenir_invitation_par_token(token)
    if not invite or not invite.get("is_active", True):
        return {"status": "error", "reason": "invite_invalid"}
    
    if invite.get("expires_at") and datetime.fromisoformat(invite["expires_at"]) < datetime.utcnow():
        return {"status": "error", "reason": "invite_expired"}
    
    user_id_raw = current_user.get("id")
    if user_id_raw is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Utilisateur invalide ou id manquant")
    try:
        user_id = int(user_id_raw)
    except (ValueError, TypeError):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Identifiant utilisateur invalide")
    
    await ajouter_membre(invite["group_id"], user_id)
    await incrementer_utilisation_invite(token)
    
    return {"status": "joined", "group_id": invite["group_id"], "user_id": user_id}

async def obtenir_groupes_par_utilisateur(user_id: int) -> List[Dict[str, Any]]:
    groupes = await lister_groupes_par_utilisateur(user_id)
    normalized = []
    for g in groupes:
        normalized.append({
            "id": g.get("id"),
            "name": g.get("name"),
            "description": g.get("description"),
            "owner_id": g.get("owner_id"),
            "members": g.get("members", []),
            "member_count": g.get("member_count", len(g.get("members", []))),
        })
    return normalized