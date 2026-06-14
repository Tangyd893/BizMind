from app.api.v1 import admin, auth, chat, documents, eval, health, threads
from fastapi import APIRouter

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(admin.router)
api_router.include_router(documents.router)
api_router.include_router(threads.router)
api_router.include_router(chat.router)
api_router.include_router(eval.router)
