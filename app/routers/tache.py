from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List

from app.core.security import get_current_user
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

@router.post("/", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
async def create_task(payload: TaskCreate, current_user: dict = Depends(get_current_user)):
    return await creer_nouvelle_tache(
        title=payload.title,
        description=payload.description,
        assigned_to_id=payload.assigned_to_id,
        group_id=payload.group_id,
        due_date=payload.due_date,
        current_user=current_user,
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
