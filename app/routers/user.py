from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from typing import Optional, Dict, Any

from app.services.user import (
    creer_user,
    get_user_by_id,
    update_user,
    delete_user,
)
from app.core.security import get_current_user

router = APIRouter(prefix="/users", tags=["users"])

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: Optional[str] = None

class UserPatch(BaseModel):
    full_name: Optional[str] = None
    is_active: Optional[bool] = None
    password: Optional[str] = None

@router.post("/", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
async def create_user(payload: UserCreate):
    user = await creer_user(payload.email, payload.password, payload.full_name)
    return {k: v for k, v in user.items() if k != "hashed_password"}

@router.get("/{user_id}", response_model=Dict[str, Any])
async def read_user(user_id: int, current_user: dict = Depends(get_current_user)):
    return await get_user_by_id(user_id)

@router.patch("/{user_id}", response_model=Dict[str, Any])
async def patch_user(user_id: int, payload: UserPatch, current_user: dict = Depends(get_current_user)):
    return await update_user(user_id, payload.dict(exclude_unset=True))

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_user(user_id: int, current_user: dict = Depends(get_current_user)):
    await delete_user(user_id)
    return {}
