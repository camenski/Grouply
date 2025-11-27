from fastapi import APIRouter, Depends, HTTPException, status,Request,Form
from typing import Dict, Any, List,Optional
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from fastapi.templating import Jinja2Templates
from app.dependencies.auth import get_current_user
from app.schemas.groupe import GroupCreate,GroupUpdate
from app.schemas.tache import TaskCreate
from app.crud.user import recuperer_utilisateur_par_id
from app.services.groupe import (
    creer_nouveau_groupe,
    modifier_groupe,
    supprimer_groupe_si_createur,
    retirer_membre_du_groupe,
    creer_tache_dans_groupe,
    supprimer_tache_du_groupe,
    lister_taches_du_groupe,
    generer_invitation_simple,
    rejoindre_via_invite_simple,
    obtenir_groupes_par_utilisateur
)


router = APIRouter(prefix="/groups", tags=["groups"])
templates = Jinja2Templates(directory="templates")



class InviteJoin(BaseModel):
    token: str


@router.get("/list", include_in_schema=False)
async def list_groups_page(request: Request, current_user: dict = Depends(get_current_user)):
    raw_id = current_user.get("id")
    if raw_id is None:
        raise HTTPException(status_code=400, detail="Utilisateur invalide ou id manquant")
    try:
        user_id = int(raw_id)
    except (ValueError, TypeError):
        raise HTTPException(status_code=400, detail="Identifiant utilisateur invalide")

    groups = await obtenir_groupes_par_utilisateur(user_id)
    return templates.TemplateResponse("groups_list.html", {"request": request, "user": current_user, "groups": groups})

@router.get("/create", include_in_schema=False)
async def create_group_page(request: Request, current_user: dict = Depends(get_current_user)):
    return templates.TemplateResponse("group_create.html", {"request": request, "user": current_user})

@router.post("/create", include_in_schema=False)
async def create_group_from_form(
    request: Request,
    name: str = Form(...),
    description: Optional[str] = Form(None),
    current_user: dict = Depends(get_current_user),
):
    new_group = await creer_nouveau_groupe(name, description, None, current_user)
    return RedirectResponse(url=f"/groups/{new_group['id']}", status_code=303)

@router.get("/{group_id}", include_in_schema=False)
async def group_detail_page(
    group_id: int,
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    group = await modifier_groupe(group_id, {}, current_user)
    if not group:
        raise HTTPException(status_code=404, detail="Groupe introuvable")

    tasks = await lister_taches_du_groupe(group_id, current_user)

    owner_id = group.get("owner_id")
    owner = None
    if owner_id:
        owner = await recuperer_utilisateur_par_id(owner_id)

    members = group.get("members", [])
    member_count = len(members)

    context = {
        "request": request,
        "user": current_user,
        "group": group,
        "tasks": tasks,
        "owner": owner,
        "members": members,
        "member_count": member_count,
    }

    return templates.TemplateResponse("group_detail.html", context)


@router.get("/{group_id}/invite", include_in_schema=False)
async def group_invite_page(group_id: int, request: Request, current_user: dict = Depends(get_current_user)):
    invite = await generer_invitation_simple(group_id, current_user)
    return templates.TemplateResponse("group_invite.html", {"request": request, "user": current_user, "invite": invite})


@router.post("/", response_model=Dict[str, Any])
async def create_group(payload: GroupCreate, current_user: dict = Depends(get_current_user)):
    return await creer_nouveau_groupe(payload.name, payload.description, payload.owner_id, current_user)

@router.patch("/{group_id}", response_model=Dict[str, Any])
async def update_group(group_id: int, payload: GroupUpdate, current_user: dict = Depends(get_current_user)):
    return await modifier_groupe(group_id, payload.dict(exclude_unset=True), current_user)

@router.delete("/{group_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_group(group_id: int, current_user: dict = Depends(get_current_user)):
    await supprimer_groupe_si_createur(group_id, current_user)
    return {}

@router.delete("/{group_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_member(group_id: int, user_id: int, current_user: dict = Depends(get_current_user)):
    await retirer_membre_du_groupe(group_id, user_id, current_user)
    return {}

@router.post("/{group_id}/tasks", response_model=Dict[str, Any])
async def create_task_in_group(
    group_id: int,
    payload: TaskCreate,
    current_user: dict = Depends(get_current_user)
):

    return await creer_tache_dans_groupe(
        group_id=group_id,
        title=payload.title,
        description=payload.description,
        due_date=payload.due_date,
        current_user=current_user
    )

@router.delete("/{group_id}/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task_in_group(group_id: int, task_id: int, current_user: dict = Depends(get_current_user)):
    await supprimer_tache_du_groupe(group_id, task_id, current_user)
    return {}

@router.get("/{group_id}/tasks", response_model=List[Dict[str, Any]])
async def list_tasks_in_group(group_id: int, current_user: dict = Depends(get_current_user)):
    return await lister_taches_du_groupe(group_id, current_user)

@router.post("/{group_id}/invite", response_model=Dict[str, Any])
async def create_invite(group_id: int, current_user: dict = Depends(get_current_user)):
    return await generer_invitation_simple(group_id, current_user)

@router.post("/invite/join", response_model=Dict[str, Any])
async def join_group_via_invite(payload: InviteJoin, current_user: dict = Depends(get_current_user)):
    result = await rejoindre_via_invite_simple(payload.token, current_user)
    if result.get("status") != "joined":
        raise HTTPException(status_code=400, detail=result.get("reason", "Erreur"))
    return result

@router.get("/my-groups", response_model=List[Dict[str, Any]])
async def list_my_groups(current_user: dict = Depends(get_current_user)):
    raw_id = current_user.get("id")
    if raw_id is None:
        raise HTTPException(status_code=400, detail="Utilisateur invalide ou id manquant")
    try:
        user_id = int(raw_id)
    except (ValueError, TypeError):
        raise HTTPException(status_code=400, detail="Identifiant utilisateur invalide")

    return await obtenir_groupes_par_utilisateur(user_id)