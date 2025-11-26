from fastapi import APIRouter, Request, Depends, Form, HTTPException
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path

from app.dependencies.auth import get_current_user
from app.services.tache import lister_taches_par_utilisateur, list_taches_du_groupe, associer_tache_a_groupe
from app.services.groupe import obtenir_groupes_par_utilisateur, retirer_membre_du_groupe
# from app.services.invite_service import generer_invitation
from app.storage.json_db import obtenir_groupe_par_id
from app.dependencies.auth import get_current_user

router = APIRouter(prefix="/index", tags=["index"])
BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory="templates")

@router.get("/", include_in_schema=False)
async def index(request: Request, current_user: dict = Depends(get_current_user)):
    user = current_user
    print("kkhjgfjhgfjhfkhjfkjhfkjhgkjhgkjhgkjhgkjhgkjgjgkjhgkjhgkjgkkgkjhgkjhgkjgkjhgkjhgkjhgkjhgkjhgkjhgkkghj",user)
    user_id = user["id"]
    personal_tasks = await lister_taches_par_utilisateur(user_id)
    groups = await obtenir_groupes_par_utilisateur(user_id)
    group_tasks = []
    for g in groups:
        tasks_for_group = await list_taches_du_groupe(g["id"], current_user)
        for t in tasks_for_group:
            t["_group"] = {"id": g["id"], "name": g["name"]}
        group_tasks.extend(tasks_for_group)

    tasks = personal_tasks + group_tasks
    return templates.TemplateResponse("index.html", {"request": request, "user": user, "tasks": tasks, "groups": groups})

@router.post("/tasks/{task_id}/associate", include_in_schema=False)
async def associate_task(task_id: int, group_id: int = Form(...), current_user: dict = Depends(get_current_user)):
    if not group_id:
        raise HTTPException(status_code=400, detail="group_id requis")
    await associer_tache_a_groupe(task_id, group_id, current_user)
    return RedirectResponse(url="/", status_code=303)

# @router.post("/groups/{group_id}/invite", include_in_schema=False)
# async def invite_link(group_id: int, current_user: dict = Depends(get_current_user)):
#     group = await obtenir_groupe_par_id(group_id)
#     if not group:
#         raise HTTPException(status_code=404, detail="Groupe introuvable")
#     if group.get("creator_id") != current_user["id"]:
#         raise HTTPException(status_code=403, detail="Accès refusé")
#     token = await generer_invitation(group_id, current_user["id"])
#     invite_url = f"/groups/join/{token}"
#     return JSONResponse({"invite_url": invite_url})

@router.get("/groups/{group_id}/manage", include_in_schema=False)
async def manage_group(request: Request, group_id: int, current_user: dict = Depends(get_current_user)):
    group = await obtenir_groupe_par_id(group_id)
    if not group or group.get("creator_id") != current_user["id"]:
        raise HTTPException(status_code=403, detail="Accès refusé")
    return templates.TemplateResponse("manage_group.html", {"request": request, "group": group})

@router.post("/groups/{group_id}/remove_member", include_in_schema=False)
async def remove_member(group_id: int, member_id: int = Form(...), current_user: dict = Depends(get_current_user)):
    group = await obtenir_groupe_par_id(group_id)
    if not group or group.get("creator_id") != current_user["id"]:
        raise HTTPException(status_code=403, detail="Accès refusé")
    await retirer_membre_du_groupe(group_id, member_id)
    return RedirectResponse(url=f"/groups/{group_id}/manage", status_code=303)
