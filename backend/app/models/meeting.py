from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel


# Meeting models
class MeetingCreate(BaseModel):
    title: str
    description: Optional[str] = None
    t1: datetime
    t2: datetime
    lat: float
    long: float
    participants: str  # Comma-separated list of emails


class Meeting(MeetingCreate):
    meeting_id: int


class MeetingIdResponse(BaseModel):
    success: bool = True
    meeting_id: int


class MeetingListResponse(BaseModel):
    meetings: List[int]