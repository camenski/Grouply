# app/main.py (extrait)
from fastapi import FastAPI
from app.storage.json_db import seed_db
from app.routers import auth as auth_router, user as users_router, groupe as groups_router, tache as tasks_router
app = FastAPI()

@app.on_event("startup")
async def on_startup():
    await seed_db()  


app.include_router(auth_router.router)
app.include_router(users_router.router)
app.include_router(groups_router.router)
app.include_router(tasks_router.router)