from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel


# Meeting models
class MeetingBase(BaseModel):
    title: str
    description: Optional[str] = None
    t1: datetime
    t2: datetime
    lat: float
    long: float

"""The meeting model that gets sent to the backend upon meeting creation"""
class MeetingCreate(MeetingBase):
    participants: str  # Comma-separated list of emails

"""The meeting model of the meetings that are returned from the backend"""
class MeetingResponse(MeetingBase):
    meeting_id: int
    participants: set[str] # Set of string emails

class MeetingIdResponse(BaseModel):
    success: bool = True
    meeting_id: int


class MeetingListResponse(BaseModel):
    meetings: List[int]