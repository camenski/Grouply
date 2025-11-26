import json
from pathlib import Path
from typing import Any, Dict, List, Optional
import asyncio
import bcrypt
import secrets
from datetime import datetime, timedelta

from app.core.config import DATABASE_JSON_PATH

_lock = asyncio.Lock()

def _ensure_file(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        initial = {
            "users": [],
            "groups": [],
            "tasks": [],
            "invites": [],
            "next_ids": {"users": 1, "groups": 1, "tasks": 1, "invites": 1},
        }
        path.write_text(json.dumps(initial, ensure_ascii=False, indent=2), encoding="utf-8")

async def _lire_brut(path: Path) -> Dict[str, Any]:
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, lambda: json.loads(path.read_text(encoding="utf-8")))

async def _ecrire_brut(path: Path, data: Dict[str, Any]) -> None:
    loop = asyncio.get_running_loop()
    def _write():
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    await loop.run_in_executor(None, _write)

async def charger_db() -> Dict[str, Any]:
    _ensure_file(DATABASE_JSON_PATH)
    async with _lock:
        return await _lire_brut(DATABASE_JSON_PATH)

async def sauvegarder_db(data: Dict[str, Any]) -> None:
    _ensure_file(DATABASE_JSON_PATH)
    async with _lock:
        await _ecrire_brut(DATABASE_JSON_PATH, data)

async def obtenir_prochain_id(kind: str) -> int:
    data = await charger_db()
    nid = data.setdefault("next_ids", {}).get(kind, 1)
    data["next_ids"][kind] = nid + 1
    await sauvegarder_db(data)
    return nid

async def trouver_utilisateur_par_email(email: str) -> Optional[Dict[str, Any]]:
    data = await charger_db()
    for u in data.get("users", []):
        if u.get("email") == email:
            return u
    return None

async def trouver_utilisateur_par_id(user_id: int) -> Optional[Dict[str, Any]]:
    data = await charger_db()
    for u in data.get("users", []):
        if u.get("id") == user_id:
            return u
    return None

async def ajouter_utilisateur(user_obj: Dict[str, Any]) -> Dict[str, Any]:
    data = await charger_db()
    user_obj["id"] = await obtenir_prochain_id("users")
    data.setdefault("users", []).append(user_obj)
    await sauvegarder_db(data)
    return user_obj

async def ajouter_groupe(group_obj: Dict[str, Any]) -> Dict[str, Any]:
    data = await charger_db()
    group_obj["id"] = await obtenir_prochain_id("groups")
    group_obj.setdefault("members", [])
    data.setdefault("groups", []).append(group_obj)
    await sauvegarder_db(data)
    return group_obj

async def obtenir_groupe_par_id(group_id: int) -> Optional[Dict[str, Any]]:
    data = await charger_db()
    for g in data.get("groups", []):
        if g.get("id") == group_id:
            return g
    return None

async def ajouter_membre_au_groupe(group_id: int, user_id: int) -> None:
    data = await charger_db()
    for g in data.get("groups", []):
        if g.get("id") == group_id:
            if user_id not in g.setdefault("members", []):
                g["members"].append(user_id)
                await sauvegarder_db(data)
            return

async def retirer_membre_du_groupe(group_id: int, user_id: int) -> None:
    data = await charger_db()
    for g in data.get("groups", []):
        if g.get("id") == group_id:
            members = g.get("members", [])
            if user_id in members:
                members.remove(user_id)
                await sauvegarder_db(data)
            return

async def creer_tache(title: str, description: Optional[str] = None,
                      assigned_to_id: Optional[int] = None,
                      group_id: Optional[int] = None,
                      due_date: Optional[str] = None) -> Dict[str, Any]:
    data = await charger_db()
    nid = data.setdefault("next_ids", {}).get("tasks", 1)
    task = {
        "id": nid,
        "title": title,
        "description": description,
        "status": "todo",
        "assigned_to_id": assigned_to_id,
        "group_id": group_id,
        "due_date": due_date,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
    }
    data.setdefault("tasks", []).append(task)
    data["next_ids"]["tasks"] = nid + 1
    await sauvegarder_db(data)
    return task

async def recuperer_tache(task_id: int) -> Optional[Dict[str, Any]]:
    data = await charger_db()
    for t in data.get("tasks", []):
        if t.get("id") == task_id:
            return t
    return None

async def lister_taches_par_groupe(group_id: int) -> List[Dict[str, Any]]:
    data = await charger_db()
    return [t for t in data.get("tasks", []) if t.get("group_id") == group_id]

async def mettre_a_jour_tache(task_id: int, patch: Dict[str, Any]) -> Dict[str, Any]:
    data = await charger_db()
    for t in data.get("tasks", []):
        if t.get("id") == task_id:
            if "title" in patch:
                t["title"] = patch["title"]
            if "description" in patch:
                t["description"] = patch["description"]
            if "status" in patch:
                t["status"] = patch["status"]
            if "assigned_to_id" in patch:
                t["assigned_to_id"] = patch["assigned_to_id"]
            if "group_id" in patch:
                t["group_id"] = patch["group_id"]
            if "due_date" in patch:
                t["due_date"] = patch["due_date"]
            t["updated_at"] = datetime.utcnow().isoformat()
            await sauvegarder_db(data)
            return t
    raise KeyError("Tâche introuvable")

async def supprimer_tache(task_id: int) -> None:
    data = await charger_db()
    tasks = data.get("tasks", [])
    new_tasks = [t for t in tasks if t.get("id") != task_id]
    if len(new_tasks) == len(tasks):
        raise KeyError("Tâche introuvable")
    data["tasks"] = new_tasks
    await sauvegarder_db(data)

async def creer_invitation(group_id: int, created_by: int, expires_in_days: int = 7, max_uses: int = 1) -> Dict[str, Any]:
    data = await charger_db()
    group = next((g for g in data.get("groups", []) if g["id"] == group_id), None)
    if not group:
        raise KeyError("Groupe introuvable")
    nid = data.setdefault("next_ids", {}).get("invites", 1)
    token = secrets.token_urlsafe(32)
    expires_at = (datetime.utcnow() + timedelta(days=expires_in_days)).isoformat()
    invite = {
        "id": nid,
        "token": token,
        "group_id": group_id,
        "created_by": created_by,
        "expires_at": expires_at,
        "max_uses": max_uses,
        "uses": 0,
        "revoked": False,
        "created_at": datetime.utcnow().isoformat(),
    }
    data.setdefault("invites", []).append(invite)
    data["next_ids"]["invites"] = nid + 1
    await sauvegarder_db(data)
    return invite

async def obtenir_invite_par_token(token: str) -> Optional[Dict[str, Any]]:
    data = await charger_db()
    for inv in data.get("invites", []):
        if inv.get("token") == token:
            return inv
    return None

async def utiliser_invite(token: str, user_id: int) -> Dict[str, Any]:
    data = await charger_db()
    for inv in data.get("invites", []):
        if inv.get("token") == token:
            if inv.get("revoked"):
                raise ValueError("Invitation révoquée")
            if inv.get("uses", 0) >= inv.get("max_uses", 1):
                raise ValueError("Invitation déjà utilisée")
            if inv.get("expires_at"):
                try:
                    exp = datetime.fromisoformat(inv["expires_at"])
                except Exception:
                    exp = None
                if exp and exp < datetime.utcnow():
                    raise ValueError("Invitation expirée")

            for g in data.get("groups", []):
                if g.get("id") == inv["group_id"]:
                    if user_id not in g.setdefault("members", []):
                        g["members"].append(user_id)
                    break
            inv["uses"] = inv.get("uses", 0) + 1

            if inv["uses"] >= inv.get("max_uses", 1):
                inv["revoked"] = True
            await sauvegarder_db(data)
            return inv
    raise KeyError("Invitation introuvable")

async def revoke_invite(invite_id: int) -> None:
    data = await charger_db()
    for inv in data.get("invites", []):
        if inv.get("id") == invite_id:
            inv["revoked"] = True
            await sauvegarder_db(data)
            return
    raise KeyError("Invitation introuvable")

def hacher_mot_de_passe(password: str) -> str:
    hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
    return hashed.decode("utf-8")

def verifier_mot_de_passe(hashed: str, password: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))

async def seed_db(force: bool = False) -> None:

    _ensure_file(DATABASE_JSON_PATH)
    async with _lock:
        loop = asyncio.get_running_loop()
        data = await loop.run_in_executor(None, lambda: json.loads(DATABASE_JSON_PATH.read_text(encoding="utf-8")))
        if data.get("users") and not force:
            return

        def _hash(pw: str) -> str:
            return bcrypt.hashpw(pw.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

        users: List[Dict[str, Any]] = [
            {"id": 1, "email": "alice@example.com", "hashed_password": _hash("password1"), "full_name": "Alice"},
            {"id": 2, "email": "bob@example.com", "hashed_password": _hash("password2"), "full_name": "Bob"},
            {"id": 3, "email": "carol@example.com", "hashed_password": _hash("password3"), "full_name": "Carol"},
        ]

        groups: List[Dict[str, Any]] = [
            {"id": 1, "name": "Groupe de test", "description": "Groupe initial", "owner_id": 1, "members": [1, 2]},
            {"id": 2, "name": "Admins", "description": "Groupe des administrateurs", "owner_id": 2, "members": [2]},
        ]

        tasks: List[Dict[str, Any]] = [
            {
                "id": 1,
                "title": "Préparer la démo",
                "description": "Rédiger slides et préparer la démo technique",
                "status": "in_progress",
                "assigned_to_id": 1,
                "group_id": 1,
                "due_date": (datetime.utcnow() + timedelta(days=7)).isoformat(),
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
            },
            {
                "id": 2,
                "title": "Nettoyer la base",
                "description": "Supprimer les données de test obsolètes",
                "status": "todo",
                "assigned_to_id": 2,
                "group_id": None,
                "due_date": None,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
            },
        ]

        invites: List[Dict[str, Any]] = [
            {
                "id": 1,
                "token": secrets.token_urlsafe(32),
                "group_id": 1,
                "created_by": 1,
                "expires_at": (datetime.utcnow() + timedelta(days=7)).isoformat(),
                "max_uses": 1,
                "uses": 0,
                "revoked": False,
                "created_at": datetime.utcnow().isoformat(),
            }
        ]

        new_data = {
            "users": users,
            "groups": groups,
            "tasks": tasks,
            "invites": invites,
            "next_ids": {"users": 4, "groups": 3, "tasks": 3, "invites": 2},
        }
        await loop.run_in_executor(None, lambda: DATABASE_JSON_PATH.write_text(json.dumps(new_data, ensure_ascii=False, indent=2), encoding="utf-8"))
