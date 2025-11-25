# app/crud/tasks.py
from typing import Dict, Any, List, Optional
from datetime import datetime
from app.storage.json_db import charger_db, sauvegarder_db

async def creer_tache(title: str, description: Optional[str] = None,
                      assigned_to_id: Optional[int] = None,
                      group_id: Optional[int] = None,
                      due_date: Optional[str] = None) -> Dict[str, Any]:
    """
    Crée une tâche. due_date attendu en ISO string (optionnel).
    """
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

async def assigner_tache(task_id: int, user_id: Optional[int]) -> Dict[str, Any]:
    return await mettre_a_jour_tache(task_id, {"assigned_to_id": user_id})

async def changer_statut(task_id: int, statut: str) -> Dict[str, Any]:
    return await mettre_a_jour_tache(task_id, {"status": statut})
