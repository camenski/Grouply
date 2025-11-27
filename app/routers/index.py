from fastapi import APIRouter, Request, Depends, Form, HTTPException
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path

from app.dependencies.auth import get_current_user
from app.services.tache import lister_taches_par_utilisateur, list_taches_du_groupe, associer_tache_a_groupe
from app.services.groupe import obtenir_groupes_par_utilisateur, retirer_membre_du_groupe
from app.storage.json_db import obtenir_groupe_par_id
from app.dependencies.auth import get_current_user

router = APIRouter(prefix="/index", tags=["index"])
BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory="templates")

@router.get("/", include_in_schema=False)
async def index(request: Request, current_user: dict = Depends(get_current_user)):
    user = current_user
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


