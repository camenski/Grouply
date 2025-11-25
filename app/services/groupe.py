from typing import Dict, Any, List, Optional
from fastapi import HTTPException, status

from app.crud.groupe import (
    creer_groupe,
    recuperer_groupe,
    lister_groupes,
    mettre_a_jour_groupe,
    supprimer_groupe,
    ajouter_membre,
    retirer_membre,
)
from app.crud.user import recuperer_utilisateur_par_id

async def creer_nouveau_groupe(name: str, description: Optional[str], owner_id: Optional[int]) -> Dict[str, Any]:
    # si owner_id fourni, vérifier qu'il existe
    if owner_id is not None:
        owner = await recuperer_utilisateur_par_id(owner_id)
        if not owner:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Propriétaire introuvable")
    try:
        return await creer_groupe(name=name, description=description, owner_id=owner_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

async def get_groupe(group_id: int) -> Dict[str, Any]:
    g = await recuperer_groupe(group_id)
    if not g:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Groupe introuvable")
    return g

async def list_all_groupes() -> List[Dict[str, Any]]:
    return await lister_groupes()

async def update_groupe(group_id: int, patch: Dict[str, Any]) -> Dict[str, Any]:
    try:
        return await mettre_a_jour_groupe(group_id, patch)
    except KeyError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Groupe introuvable")

async def delete_groupe(group_id: int) -> None:
    try:
        await supprimer_groupe(group_id)
    except KeyError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Groupe introuvable")

async def ajouter_membre_au_groupe(group_id: int, user_id: int) -> None:
    # vérifier existence utilisateur
    user = await recuperer_utilisateur_par_id(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Utilisateur introuvable")
    try:
        await ajouter_membre(group_id, user_id)
    except KeyError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Groupe introuvable")

async def retirer_membre_du_groupe(group_id: int, user_id: int) -> None:
    try:
        await retirer_membre(group_id, user_id)
    except KeyError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Groupe introuvable")
