from fastapi import APIRouter, Depends, status
from pydantic import BaseModel
from typing import Dict, Any

from app.core.security import get_current_user
from app.services.invite_service import generer_invitation, rejoindre_via_invite

router = APIRouter(prefix="/invites", tags=["invites"])

class InviteCreate(BaseModel):
    group_id: int
    expires_in_days: int = 7
    max_uses: int = 1

@router.post("/", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
async def create_invite(payload: InviteCreate, current_user: dict = Depends(get_current_user)):
    invite = await generer_invitation(payload.group_id, current_user, payload.expires_in_days, payload.max_uses)
    return invite

@router.post("/join", response_model=Dict[str, Any])
async def join_invite(payload: dict, current_user: dict = Depends(get_current_user)):
    token = payload.get("token")
    if not isinstance(token, str):
        raise ValueError("Invalid token: must be a non-empty string.")
    return await rejoindre_via_invite(token, current_user)
