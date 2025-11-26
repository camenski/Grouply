from typing import Dict, Any, List, Optional
from fastapi import HTTPException, status
from datetime import datetime

from app.crud.tache import (
    creer_tache,
    recuperer_tache,
    lister_taches_par_groupe,
    mettre_a_jour_tache,
    supprimer_tache,
)
from app.crud.groupe import obtenir_groupe_par_id
from app.crud.user import recuperer_utilisateur_par_id

VALID_STATUSES = {"En attente", "En cours", "Terminé"}

async def creer_nouvelle_tache(title: str, description: Optional[str] = None,
                                assigned_to_id: Optional[int] = None,
                                group_id: Optional[int] = None,
                                due_date: Optional[str] = None,
                                current_user: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    if assigned_to_id is None and current_user is not None:
        assigned_to_id = current_user["id"]

    if assigned_to_id is not None:
        user = await recuperer_utilisateur_par_id(assigned_to_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Utilisateur assigné introuvable")

    if group_id is not None:
        group = await obtenir_groupe_par_id(group_id)
        if not group:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Groupe introuvable")
        if current_user and current_user["id"] not in group.get("members", []):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Vous n'appartenez pas à ce groupe")

    return await creer_tache(title=title, description=description, assigned_to_id=assigned_to_id, group_id=group_id, due_date=due_date)

async def get_tache(task_id: int, current_user: Dict[str, Any]) -> Dict[str, Any]:
    t = await recuperer_tache(task_id)
    if not t:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tâche introuvable")
    if t.get("group_id"):
        group = await obtenir_groupe_par_id(t["group_id"])
        if group and current_user["id"] not in group.get("members", []):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Accès refusé à cette tâche de groupe")
    else:
        if t.get("assigned_to_id") != current_user["id"]:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Vous ne pouvez voir que vos tâches non groupées")
    return t

async def list_taches_du_groupe(group_id: int, current_user: Dict[str, Any]) -> List[Dict[str, Any]]:
    group = await obtenir_groupe_par_id(group_id)
    if not group:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Groupe introuvable")
    if current_user["id"] not in group.get("members", []):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Vous n'êtes pas membre de ce groupe")
    return await lister_taches_par_groupe(group_id)

async def update_tache(task_id: int, patch: Dict[str, Any], current_user: Dict[str, Any]) -> Dict[str, Any]:
    t = await recuperer_tache(task_id)
    if not t:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tâche introuvable")
    if t.get("assigned_to_id") != current_user["id"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Vous ne pouvez modifier que vos propres tâches")

    if "status" in patch and patch["status"] not in VALID_STATUSES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Statut invalide")
    if "group_id" in patch and patch["group_id"] is not None:
        group = await obtenir_groupe_par_id(patch["group_id"])
        if not group:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Groupe introuvable")
        if current_user["id"] not in group.get("members", []):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Vous n'appartenez pas au groupe ciblé")

    try:
        return await mettre_a_jour_tache(task_id, patch)
    except KeyError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tâche introuvable")

async def delete_tache(task_id: int, current_user: Dict[str, Any]) -> None:
    t = await recuperer_tache(task_id)
    if not t:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tâche introuvable")
    if t.get("assigned_to_id") != current_user["id"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Vous ne pouvez supprimer que vos propres tâches")
    await supprimer_tache(task_id)


async def lister_taches_par_utilisateur(user_id: int) -> List[Dict[str, Any]]:

    try:
        from app.crud.tache import lister_taches_par_utilisateur as crud_lister
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Fonction CRUD 'lister_taches_par_utilisateur' manquante. Implémentez-la dans app.crud.tache."
        )

    tasks = await crud_lister(user_id)

    visible: List[Dict[str, Any]] = []
    for t in tasks:
        group_id = t.get("group_id")
        if group_id:
            group = await obtenir_groupe_par_id(group_id)
            if group and user_id in group.get("members", []):
                visible.append(t)
        else:
            if t.get("assigned_to_id") == user_id:
                visible.append(t)

    return visible

async def associer_tache_a_groupe(task_id: int, group_id: int, current_user: Dict[str, Any]) -> Dict[str, Any]:

    t = await recuperer_tache(task_id)
    if not t:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tâche introuvable")

    if t.get("assigned_to_id") != current_user.get("id"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Vous ne pouvez associer que vos propres tâches")

    group = await obtenir_groupe_par_id(group_id)
    if not group:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Groupe introuvable")

    if current_user.get("id") not in group.get("members", []):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Vous devez être membre du groupe pour y associer une tâche")

    patch = {"group_id": group_id}
    updated = await mettre_a_jour_tache(task_id, patch)
    return updated