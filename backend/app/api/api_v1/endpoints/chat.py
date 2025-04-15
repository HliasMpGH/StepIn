from fastapi import APIRouter, HTTPException, Depends

from app.models.message import MessageCreate, MessageListResponse
from app.models.user import SuccessResponse, ErrorResponse
from app.services.chat_service import ChatService

router = APIRouter()
chat_service = ChatService()


@router.post("/post", response_model=SuccessResponse, responses={400: {"model": ErrorResponse}})
async def post_message(message: MessageCreate):
    result = chat_service.post_message(message.email, message.text)
    if isinstance(result, dict) and "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return SuccessResponse()