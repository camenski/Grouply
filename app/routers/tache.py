from fastapi import APIRouter, Depends, Form, HTTPException, status
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from fastapi import Request, Depends
from fastapi.templating import Jinja2Templates
from pathlib import Path
from app.services.tache import lister_taches_par_utilisateur

from app.dependencies.auth import get_current_user
from app.services.tache import (
    creer_nouvelle_tache,
    get_tache,
    list_taches_du_groupe,
    update_tache,
    delete_tache,
)

router = APIRouter(prefix="/tasks", tags=["tasks"])

class TaskCreate(BaseModel):
    title: str = Field(..., min_length=1)
    description: Optional[str] = None
    assigned_to_id: Optional[int] = None
    group_id: Optional[int] = None
    due_date: Optional[str] = None 

class TaskPatch(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    assigned_to_id: Optional[int] = None
    group_id: Optional[int] = None
    due_date: Optional[str] = None

BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory="templates")


@router.get("/create", include_in_schema=False)
async def create_task_page(request: Request, current_user: dict = Depends(get_current_user)):

    groups = []   
    members = []  
    return templates.TemplateResponse(
        "tasks_create.html",
        {"request": request, "user": current_user, "groups": groups, "members": members},
    )

@router.post("/create", include_in_schema=False)
async def create_task_from_form(
    request: Request,
    title: str = Form(...),
    description: Optional[str] = Form(None),
    assigned_to_id: Optional[str] = Form(None),
    group_id: Optional[str] = Form(None),
    due_date: Optional[str] = Form(None),
    current_user: dict = Depends(get_current_user),
):

    try:
        assigned_to = int(assigned_to_id) if assigned_to_id not in (None, "", "None") else None
    except ValueError:
        assigned_to = None

    try:
        group = int(group_id) if group_id not in (None, "", "None") else None
    except ValueError:
        group = None

    try:
        new_task = await creer_nouvelle_tache(
            title=title,
            description=description,
            assigned_to_id=assigned_to,
            group_id=group,
            due_date=due_date,
            current_user=current_user,
        )
    except Exception as exc:
        message = str(exc) or "Une erreur est survenue lors de la création de la tâche."
        groups = []
        members = []
        form = {"title": title, "description": description, "assigned_to_id": assigned_to_id, "group_id": group_id, "due_date": due_date}
        return templates.TemplateResponse(
            "tasks_create.html",
            {"request": request, "message": message, "form": form, "groups": groups, "members": members, "user": current_user},
            status_code=400,
        )

    task_id = new_task.get("id") if isinstance(new_task, dict) else None
    if task_id:
        return RedirectResponse(url=f"/tasks/success/{task_id}", status_code=303)
    return RedirectResponse(url="/tasks/success", status_code=303)

@router.get("/success/{task_id}", include_in_schema=False)
async def task_created_success(request: Request, task_id: int, current_user: dict = Depends(get_current_user)):
    try:
        task = await get_tache(task_id, current_user)
        title = task.get("title") if isinstance(task, dict) else None
    except Exception:
        title = None

    return templates.TemplateResponse(
        "tasks_success.html",
        {"request": request, "user": current_user, "task_id": task_id, "task_title": title},
    )

@router.get("/success", include_in_schema=False)
async def task_created_success_generic(request: Request, current_user: dict = Depends(get_current_user)):
    return templates.TemplateResponse(
        "tasks_success.html",
        {"request": request, "user": current_user, "task_id": None, "task_title": None},
    )



@router.get("/{task_id}", response_model=Dict[str, Any])
async def read_task(task_id: int, current_user: dict = Depends(get_current_user)):
    return await get_tache(task_id, current_user)

@router.get("/group/{group_id}", response_model=List[Dict[str, Any]])
async def tasks_by_group(group_id: int, current_user: dict = Depends(get_current_user)):
    return await list_taches_du_groupe(group_id, current_user)

@router.patch("/{task_id}", response_model=Dict[str, Any])
async def patch_task(task_id: int, payload: TaskPatch, current_user: dict = Depends(get_current_user)):
    return await update_tache(task_id, payload.dict(exclude_unset=True), current_user)

@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_task(task_id: int, current_user: dict = Depends(get_current_user)):
    await delete_tache(task_id, current_user)
    return {}


@router.get("/", include_in_schema=False)
async def list_my_tasks_page(request: Request, current_user: dict = Depends(get_current_user)):
    user_id_raw = current_user.get("id")

    if user_id_raw is None:
        raise HTTPException(status_code=400, detail="Utilisateur invalide ou id manquant")

    try:
        user_id = int(user_id_raw)
    except (ValueError, TypeError):
        raise HTTPException(status_code=400, detail="Identifiant utilisateur invalide")

    tasks = await lister_taches_par_utilisateur(user_id)

    groups = []
    return templates.TemplateResponse(
        "tasks_index.html",
        {"request": request, "user": current_user, "tasks": tasks, "groups": groups},
    )


