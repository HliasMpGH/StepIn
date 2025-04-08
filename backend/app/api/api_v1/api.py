from fastapi import APIRouter

from app.api.api_v1.endpoints import users, meetings, chat

api_router = APIRouter()
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(meetings.router, prefix="/meetings", tags=["meetings"])
api_router.include_router(chat.router, prefix="/chat", tags=["chat"])