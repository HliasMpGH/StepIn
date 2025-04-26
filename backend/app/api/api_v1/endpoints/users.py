from fastapi import APIRouter, HTTPException, Depends

from app.models.user import UserCreate, User, SuccessResponse, ErrorResponse
from app.services.user_service import UserService

router = APIRouter()
user_service = UserService()


@router.post("", response_model=SuccessResponse, responses={400: {"model": ErrorResponse}})
async def create_user(user: UserCreate):
    try:
        result = user_service.create_user(user.email, user.name, user.age, user.gender)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create user")

    if isinstance(result, dict) and "error" in result:
        raise HTTPException(status_code=400, detail=f"Failed to create user: {result['error']}")
    return SuccessResponse()

@router.get("/{email}", response_model=User, responses={404: {"model": ErrorResponse}})
async def get_user(email: str):
    try:
        user = user_service.get_user(email)
    except:
        raise HTTPException(status_code=500, detail="Failed to retrieve user")

    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.delete("/{email}", response_model=SuccessResponse, responses={404: {"model": ErrorResponse}})
async def delete_user(email: str):
    try:
        result = user_service.delete_user(email)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to delete user")

    if result is None:
        raise HTTPException(status_code=404, detail="User not found")

    if isinstance(result, dict) and "error" in result:
        raise HTTPException(status_code=400, detail=f"Failed to delete user: {result['error']}")

    return SuccessResponse()