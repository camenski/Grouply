from typing import Dict, Any, Optional
from app.storage.json_db import (
    charger_db,
    sauvegarder_db,
    trouver_utilisateur_par_email,
    trouver_utilisateur_par_id,
    ajouter_utilisateur,
    hacher_mot_de_passe,
)

async def creer_utilisateur(email: str, password: str, full_name: Optional[str] = None) -> Dict[str, Any]:
    """Crée un utilisateur (vérifie l'unicité de l'email)."""
    existing = await trouver_utilisateur_par_email(email)
    if existing:
        raise ValueError("Email déjà utilisé")
    user_obj = {
        "email": email,
        "hashed_password": hacher_mot_de_passe(password),
        "full_name": full_name,
        "is_active": True,
    }
    return await ajouter_utilisateur(user_obj)

async def recuperer_utilisateur_par_id(user_id: int) -> Optional[Dict[str, Any]]:
    return await trouver_utilisateur_par_id(user_id)

async def recuperer_utilisateur_par_email(email: str) -> Optional[Dict[str, Any]]:
    return await trouver_utilisateur_par_email(email)

async def mettre_a_jour_utilisateur(user_id: int, patch: Dict[str, Any]) -> Dict[str, Any]:
    """
    Met à jour un utilisateur. patch peut contenir full_name, is_active, password.
    Si password est présent, il est haché.
    """
    data = await charger_db()
    for u in data.get("users", []):
        if u.get("id") == user_id:
            if "full_name" in patch:
                u["full_name"] = patch["full_name"]
            if "is_active" in patch:
                u["is_active"] = bool(patch["is_active"])
            if "password" in patch and patch["password"]:
                u["hashed_password"] = hacher_mot_de_passe(patch["password"])
            await sauvegarder_db(data)
            return u
    raise KeyError("Utilisateur introuvable")

async def supprimer_utilisateur(user_id: int) -> None:
    data = await charger_db()
    users = data.get("users", [])
    new_users = [u for u in users if u.get("id") != user_id]
    if len(new_users) == len(users):
        raise KeyError("Utilisateur introuvable")
    data["users"] = new_users
    
    for g in data.get("groups", []):
        members = g.get("members", [])
        if user_id in members:
            members.remove(user_id)
    for t in data.get("tasks", []):
        if t.get("assigned_to_id") == user_id:
            t["assigned_to_id"] = None
    await sauvegarder_db(data)
