from fastapi import APIRouter, Depends, HTTPException, status, Request, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
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
templates = Jinja2Templates(directory="templates")


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


@router.get("/create", include_in_schema=False)
async def create_group_page(request: Request, current_user: dict = Depends(get_current_user)):

    return templates.TemplateResponse(
        "groups_create.html",
        {"request": request, "user": current_user, "message": None, "form": {}},
    )


@router.post("/create", include_in_schema=False)
async def create_group_from_form(
    request: Request,
    name: str = Form(...),
    description: Optional[str] = Form(None),
    owner_id: Optional[str] = Form(None),
    current_user: dict = Depends(get_current_user),
):

    try:
        owner = int(owner_id) if owner_id not in (None, "", "None") else None
    except ValueError:
        owner = None

    try:
        new_group = await creer_nouveau_groupe(name=name, description=description, owner_id=owner)
    except Exception as exc:
        message = str(exc) or "Une erreur est survenue lors de la création du groupe."
        form = {"name": name, "description": description, "owner_id": owner_id}
        return templates.TemplateResponse(
            "groups_create.html",
            {"request": request, "message": message, "form": form, "user": current_user},
            status_code=400,
        )

    group_id = new_group.get("id") if isinstance(new_group, dict) else None
    if group_id:
        return RedirectResponse(url=f"/groups/{group_id}", status_code=303)
    return RedirectResponse(url="/groups/", status_code=303)


@router.get("/success", include_in_schema=False)
async def group_created_success(request: Request, current_user: dict = Depends(get_current_user)):

    return templates.TemplateResponse(
        "groups_success.html",
        {"request": request, "user": current_user},
    )


@router.get("/list", include_in_schema=False)
async def groups_list_page(request: Request, current_user: dict = Depends(get_current_user)):

    try:
        groupes = await list_all_groupes()
    except Exception:
        groupes = []
    return templates.TemplateResponse(
        "groups_index.html",
        {"request": request, "user": current_user, "groups": groupes},
    )
