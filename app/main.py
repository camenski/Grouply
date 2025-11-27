from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path
from app.storage.json_db import seed_db
from app.routers import auth as auth_router, user as users_router, groupe as groups_router, tache as tasks_router, index as index_router
from fastapi.openapi.utils import get_openapi
from fastapi.staticfiles import StaticFiles
from app.dependencies.auth import get_current_user
from app.services.groupe import obtenir_groupes_par_utilisateur
from app.routers import auth as auth_router 
from app.services.auth import inscrire_utilisateur
from app.services.tache import lister_taches_par_utilisateur, list_taches_du_groupe






BASE_DIR = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"


app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

@app.get("/", include_in_schema=False)
async def root(request: Request):
    try:
        current_user = await get_current_user(request)
    except HTTPException:
        current_user = None

    if not current_user:
        return templates.TemplateResponse("accueil.html", {"request": request})

    user_safe = {k: v for k, v in current_user.items() if k != "hashed_password"}
    raw_id = user_safe.get("id")
    if raw_id is None:
        return RedirectResponse(url="/login", status_code=303)

    user_id = int(raw_id)  
    personal_tasks = await lister_taches_par_utilisateur(user_id)
    groups = await obtenir_groupes_par_utilisateur(user_id)
    return templates.TemplateResponse("index.html", {"request": request, "user": user_safe, "tasks": personal_tasks, "groups": groups})


@app.get("/register", include_in_schema=False)
async def register_get(request: Request):
    return templates.TemplateResponse("register.html", {"request": request, "message": None})

@app.post("/register", include_in_schema=False)
async def register_post(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    full_name: str | None = Form(None),
):
    try:
        user = await inscrire_utilisateur(email, password, full_name)
    except Exception as e:
        return templates.TemplateResponse("register.html", {"request": request, "message": str(e)})

    return RedirectResponse(url="/login", status_code=303)

@app.get("/login", include_in_schema=False)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request, "message": None})


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(title=app.title, version="1.0.0", routes=app.routes)
    comps = openapi_schema.setdefault("components", {})
    schemes = comps.setdefault("securitySchemes", {})

    for name, scheme in schemes.items():
        if scheme.get("type") == "oauth2" and "flows" in scheme and "password" in scheme["flows"]:
            note = "Remarque : entrez votre adresse email dans le champ 'username' du formulaire OAuth2."
            scheme["description"] = (scheme.get("description", "") + "\n\n" + note).strip()
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi


@app.on_event("startup")
async def on_startup():
    await seed_db()  


app.include_router(auth_router.router)
app.include_router(users_router.router)
app.include_router(groups_router.router)
app.include_router(tasks_router.router)
app.include_router(index_router.router)