from fastapi import APIRouter, Depends, Form, HTTPException, status, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from app.schemas.tache import TaskCreate,TaskPatch

from app.dependencies.auth import get_current_user
from app.services.tache import (
    lister_taches_par_utilisateur,
    creer_nouvelle_tache,
    get_tache,
    list_taches_du_groupe,
    update_tache,
    delete_tache,
)

router = APIRouter(prefix="/tasks", tags=["tasks"])
templates = Jinja2Templates(directory="templates")


@router.get("/create", include_in_schema=False)
async def create_task_page(request: Request, current_user: dict = Depends(get_current_user)):
    groups = []
    return templates.TemplateResponse(
        "tasks_create.html",
        {"request": request, "user": current_user, "groups": groups},
    )


@router.post("/create", include_in_schema=False)
async def create_task_from_form(
    request: Request,
    title: str = Form(...),
    description: Optional[str] = Form(None),
    group_id: Optional[str] = Form(None),
    due_date: Optional[str] = Form(None),
    current_user: dict = Depends(get_current_user),
):
    try:
        group = int(group_id) if group_id not in (None, "", "None") else None
    except ValueError:
        group = None

    try:
        new_task = await creer_nouvelle_tache(
            title=title,
            description=description,
            group_id=group,
            due_date=due_date,
            current_user=current_user,
        )
    except Exception as exc:
        message = str(exc) or "Une erreur est survenue lors de la création de la tâche."
        groups = []
        form = {"title": title, "description": description, "group_id": group_id, "due_date": due_date}
        return templates.TemplateResponse(
            "tasks_create.html",
            {"request": request, "message": message, "form": form, "groups": groups, "user": current_user},
            status_code=400,
        )

    task_id = new_task.get("id") if isinstance(new_task, dict) else None
    if task_id:
        return RedirectResponse(url=f"/tasks/success/{task_id}", status_code=303)
    return RedirectResponse(url="/tasks/success", status_code=303)

@router.get("/success/{task_id}", include_in_schema=False)
async def task_created_success(request: Request, task_id: int, current_user: dict = Depends(get_current_user)):
    task = await get_tache(task_id, current_user)
    title = task.get("title") if isinstance(task, dict) else None
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
        "tasks_list.html",
        {
            "request": request,
            "user": current_user,
            "tasks": tasks,
            "groups": groups,
        },
    )

@router.get("/{task_id}", include_in_schema=False)
async def task_detail_page(task_id: int, request: Request, current_user: dict = Depends(get_current_user)):
    task = await get_tache(task_id, current_user)
    if not task:
        raise HTTPException(status_code=404, detail="Tâche introuvable")
    groups = []  
    return templates.TemplateResponse(
        "task_detail.html",
        {"request": request, "user": current_user, "task": task, "groups": groups},
    )

@router.get("/{task_id}/edit", include_in_schema=False)
async def edit_task_page(task_id: int, request: Request, current_user: dict = Depends(get_current_user)):
    task = await get_tache(task_id, current_user)
    if not task:
        raise HTTPException(status_code=404, detail="Tâche introuvable")
    groups = []  
    return templates.TemplateResponse(
        "tasks_edit.html",
        {"request": request, "user": current_user, "task": task, "groups": groups},
    )

@router.post("/{task_id}/edit", include_in_schema=False)
async def edit_task_submit(
    task_id: int,
    title: str = Form(...),
    description: Optional[str] = Form(None),
    status: Optional[str] = Form(None),
    group_id: Optional[str] = Form(None),
    due_date: Optional[str] = Form(None),
    current_user: dict = Depends(get_current_user),
):
    payload = {
        "title": title,
        "description": description,
        "status": status,
        "group_id": int(group_id) if group_id else None,
        "due_date": due_date,
    }
    await update_tache(task_id, {k: v for k, v in payload.items() if v is not None}, current_user)

    return RedirectResponse(url=f"/tasks/success/edit/{task_id}", status_code=303)

@router.get("/success/edit/{task_id}", include_in_schema=False)
async def task_edit_success(request: Request, task_id: int, current_user: dict = Depends(get_current_user)):
    task = await get_tache(task_id, current_user)
    title = task.get("title") if isinstance(task, dict) else None
    return templates.TemplateResponse(
        "tasks_success_edit.html",
        {"request": request, "user": current_user, "task_id": task_id, "task_title": title},
    )



@router.post("/{task_id}/delete", include_in_schema=False)
async def delete_task(task_id: int, current_user: dict = Depends(get_current_user)):
    await delete_tache(task_id, current_user)
    return RedirectResponse(url="/tasks/list", status_code=303)

@router.post("/{task_id}/associate", include_in_schema=False)
async def associate_task_to_group(
    task_id: int,
    group_id: Optional[str] = Form(None),
    current_user: dict = Depends(get_current_user),
):
    group = int(group_id) if group_id else None
    await update_tache(task_id, {"group_id": group}, current_user)
    return RedirectResponse(url=f"/tasks/{task_id}", status_code=303)

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
