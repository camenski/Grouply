from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path
import json
from app.storage.json_db import (
    charger_db,
    sauvegarder_db,
    ajouter_groupe,
    obtenir_groupe_par_id,
)

async def creer_groupe(name: str, description: Optional[str], owner_id: Optional[int]) -> Dict[str, Any]:
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

async def lister_groupes_par_utilisateur(user_id: int) -> List[Dict[str, Any]]:

    try:
        db = await charger_db()
        groupes = db.get("groups") or db.get("groupes") or db.get("groups_list") or []
    except Exception:
        possible_paths = [
            Path(__file__).resolve().parent.parent / "db.json",
            Path(__file__).resolve().parent.parent / "data" / "db.json",
            Path.cwd() / "db.json",
            Path.cwd() / "data" / "db.json",
        ]
        groupes = []
        for p in possible_paths:
            if p.exists():
                try:
                    with p.open("r", encoding="utf-8") as f:
                        db = json.load(f)
                        groupes = db.get("groups") or db.get("groupes") or db.get("groups_list") or []
                        break
                except Exception:
                    continue

    result: List[Dict[str, Any]] = []
    for g in groupes:
        members = g.get("members", [])
        try:
            if int(user_id) in [int(m) for m in members]:
                g_copy = dict(g)
                g_copy["member_count"] = len(members)
                result.append(g_copy)
        except Exception:
            if str(user_id) in [str(m) for m in members]:
                g_copy = dict(g)
                g_copy["member_count"] = len(members)
                result.append(g_copy)

    return result



async def creer_invitation(group_id: int, token: str, created_by: Optional[int], expires_at: Optional[str]) -> Dict[str, Any]:

    data = await charger_db()
    invite = {
        "id": len(data.get("invites", [])) + 1,
        "group_id": group_id,
        "token": token,
        "created_by": created_by,
        "created_at": datetime.now().isoformat(),
        "expires_at": expires_at,
        "uses_count": 0,
        "max_uses": 1,
        "is_active": True,
    }
    data.setdefault("invites", []).append(invite)
    await sauvegarder_db(data)
    return invite


async def obtenir_invitation_par_token(token: str) -> Optional[Dict[str, Any]]:

    data = await charger_db()
    for inv in data.get("invites", []):
        if inv.get("token") == token:
            return inv
    return None


async def incrementer_utilisation_invite(token: str) -> bool:

    data = await charger_db()
    invites = data.get("invites", [])
    for inv in invites:
        if inv.get("token") == token:
            inv["uses_count"] = inv.get("uses_count", 0) + 1
            if inv["uses_count"] >= inv.get("max_uses", 1):
                inv["is_active"] = False
            await sauvegarder_db(data)
            return True
    return False





