from typing import Dict, Any, List, Optional
from fastapi import HTTPException, status

from app.crud.tache import (
    creer_tache,
    recuperer_tache,
    lister_taches_par_groupe,
    mettre_a_jour_tache,
    supprimer_tache,
    assigner_tache,
    changer_statut,
)
from app.crud.groupe import recuperer_groupe
from app.crud.user import recuperer_utilisateur_par_id

async def creer_nouvelle_tache(title: str, description: Optional[str] = None,
                                assigned_to_id: Optional[int] = None,
                                group_id: Optional[int] = None,
                                due_date: Optional[str] = None) -> Dict[str, Any]:
    # validations simples
    if assigned_to_id is not None:
        user = await recuperer_utilisateur_par_id(assigned_to_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Utilisateur assigné introuvable")
    if group_id is not None:
        group = await recuperer_groupe(group_id)
        if not group:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Groupe introuvable")
    return await creer_tache(title=title, description=description, assigned_to_id=assigned_to_id, group_id=group_id, due_date=due_date)

async def get_tache(task_id: int) -> Dict[str, Any]:
    t = await recuperer_tache(task_id)
    if not t:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tâche introuvable")
    return t

async def list_taches_du_groupe(group_id: int) -> List[Dict[str, Any]]:
    # vérifier que le groupe existe
    group = await recuperer_groupe(group_id)
    if not group:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Groupe introuvable")
    return await lister_taches_par_groupe(group_id)

async def update_tache(task_id: int, patch: Dict[str, Any]) -> Dict[str, Any]:
    # validations optionnelles
    if "assigned_to_id" in patch and patch["assigned_to_id"] is not None:
        user = await recuperer_utilisateur_par_id(patch["assigned_to_id"])
        if not user:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Utilisateur assigné introuvable")
    if "group_id" in patch and patch["group_id"] is not None:
        group = await recuperer_groupe(patch["group_id"])
        if not group:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Groupe introuvable")
    try:
        return await mettre_a_jour_tache(task_id, patch)
    except KeyError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tâche introuvable")

async def delete_tache(task_id: int) -> None:
    try:
        await supprimer_tache(task_id)
    except KeyError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tâche introuvable")

async def assigner(task_id: int, user_id: Optional[int]) -> Dict[str, Any]:
    if user_id is not None:
        user = await recuperer_utilisateur_par_id(user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Utilisateur introuvable")
    try:
        return await assigner_tache(task_id, user_id)
    except KeyError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tâche introuvable")

async def changer_statut_tache(task_id: int, statut: str) -> Dict[str, Any]:
    # valider statut simple
    if statut not in {"todo", "in_progress", "done"}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Statut invalide")
    try:
        return await changer_statut(task_id, statut)
    except KeyError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tâche introuvable")
