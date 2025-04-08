from typing import List, Optional
from pydantic import BaseModel, Field


# User models
class UserCreate(BaseModel):
    email: str
    name: str
    age: Optional[int] = None
    gender: Optional[str] = None


class User(UserCreate):
    pass


# Action models
class JoinLeaveRequest(BaseModel):
    email: str


class NearbyMeetingsRequest(BaseModel):
    email: str
    x: float
    y: float


# Response models
class SuccessResponse(BaseModel):
    success: bool = True


class ErrorResponse(BaseModel):
    error: str


class ParticipantListResponse(BaseModel):
    participants: List[str]


class EndMeetingResponse(BaseModel):
    success: bool = True
    timed_out_participants: List[str]