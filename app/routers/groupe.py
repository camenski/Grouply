from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Optional, Dict, Any, List

from app.services.groupe import (
    creer_nouveau_groupe,
    get_groupe,
    list_all_groupes,
    update_groupe,
    delete_groupe,
    ajouter_membre_au_groupe,
    retirer_membre_du_groupe,
)
from app.dependencies.auth import get_current_user

router = APIRouter(prefix="/groups", tags=["groups"])

class GroupCreate(BaseModel):
    name: str
    description: Optional[str] = None
    owner_id: Optional[int] = None

class GroupPatch(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    owner_id: Optional[int] = None




@router.post("/", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
async def create_group(payload: GroupCreate, current_user: dict = Depends(get_current_user)):
    return await creer_nouveau_groupe(payload.name, payload.description, payload.owner_id)

@router.get("/", response_model=List[Dict[str, Any]])
async def list_groups(current_user: dict = Depends(get_current_user)):
    return await list_all_groupes()

@router.get("/{group_id}", response_model=Dict[str, Any])
async def read_group(group_id: int, current_user: dict = Depends(get_current_user)):
    return await get_groupe(group_id)

@router.patch("/{group_id}", response_model=Dict[str, Any])
async def patch_group(group_id: int, payload: GroupPatch, current_user: dict = Depends(get_current_user)):
    return await update_groupe(group_id, payload.dict(exclude_unset=True))

@router.delete("/{group_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_group(group_id: int, current_user: dict = Depends(get_current_user)):
    await delete_groupe(group_id)
    return {}

@router.post("/{group_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def add_member(group_id: int, user_id: int, current_user: dict = Depends(get_current_user)):
    await ajouter_membre_au_groupe(group_id, user_id)
    return {}

@router.delete("/{group_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_member(group_id: int, user_id: int, current_user: dict = Depends(get_current_user)):
    await retirer_membre_du_groupe(group_id, user_id)
    return {}
