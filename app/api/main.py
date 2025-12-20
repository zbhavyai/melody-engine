from fastapi import APIRouter

from app.api.routes import ping_router

api_router = APIRouter()
api_router.include_router(ping_router.router, prefix="/ping", tags=["ping"])
