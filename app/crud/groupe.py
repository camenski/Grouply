# app/crud/groups.py
from typing import Dict, Any, List, Optional
from app.storage.json_db import (
    charger_db,
    sauvegarder_db,
    ajouter_groupe,
    obtenir_groupe_par_id,
)

async def creer_groupe(name: str, description: Optional[str], owner_id: Optional[int]) -> Dict[str, Any]:
    """Crée un groupe (vérifie unicité du nom)."""
    data = await charger_db()
    for g in data.get("groups", []):
        if g.get("name") == name:
            raise ValueError("Nom de groupe déjà utilisé")
    group_obj = {"name": name, "description": description, "owner_id": owner_id}
    return await ajouter_groupe(group_obj)

async def recuperer_groupe(group_id: int) -> Optional[Dict[str, Any]]:
    return await obtenir_groupe_par_id(group_id)

async def lister_groupes() -> List[Dict[str, Any]]:
    data = await charger_db()
    return data.get("groups", [])

async def mettre_a_jour_groupe(group_id: int, patch: Dict[str, Any]) -> Dict[str, Any]:
    data = await charger_db()
    for g in data.get("groups", []):
        if g.get("id") == group_id:
            if "name" in patch:
                g["name"] = patch["name"]
            if "description" in patch:
                g["description"] = patch["description"]
            if "owner_id" in patch:
                g["owner_id"] = patch["owner_id"]
            await sauvegarder_db(data)
            return g
    raise KeyError("Groupe introuvable")

async def supprimer_groupe(group_id: int) -> None:
    data = await charger_db()
    groups = data.get("groups", [])
    new_groups = [g for g in groups if g.get("id") != group_id]
    if len(new_groups) == len(groups):
        raise KeyError("Groupe introuvable")
    data["groups"] = new_groups
    # supprimer les tâches liées au groupe
    data["tasks"] = [t for t in data.get("tasks", []) if t.get("group_id") != group_id]
    await sauvegarder_db(data)

async def ajouter_membre(group_id: int, user_id: int) -> None:
    data = await charger_db()
    for g in data.get("groups", []):
        if g.get("id") == group_id:
            if user_id not in g.setdefault("members", []):
                g["members"].append(user_id)
                await sauvegarder_db(data)
            return
    raise KeyError("Groupe introuvable")

async def retirer_membre(group_id: int, user_id: int) -> None:
    data = await charger_db()
    for g in data.get("groups", []):
        if g.get("id") == group_id:
            members = g.get("members", [])
            if user_id in members:
                members.remove(user_id)
                await sauvegarder_db(data)
            return
    raise KeyError("Groupe introuvable")
