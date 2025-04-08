from fastapi import APIRouter, HTTPException, Depends

from app.models.user import UserCreate, User, SuccessResponse, ErrorResponse
from app.services.user_service import UserService

router = APIRouter()
user_service = UserService()


@router.post("", response_model=SuccessResponse, responses={400: {"model": ErrorResponse}})
async def create_user(user: UserCreate):
    try:
        user_service.create_user(user.email, user.name, user.age, user.gender)
        return SuccessResponse()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{email}", response_model=User, responses={404: {"model": ErrorResponse}})
async def get_user(email: str):
    user = user_service.get_user(email)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user