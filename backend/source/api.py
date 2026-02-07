from fastapi import FastAPI
from source.routes.user_prompts import router as user_prompts_router
from source.routes.user import router as user_router
from source.routes.super_admin import router as super_admin_router
from source.routes.admin import router as admin_router

def register_routes(app:FastAPI):
    app.include_router(user_prompts_router)
    app.include_router(user_router)
    app.include_router(super_admin_router)
    app.include_router(admin_router)