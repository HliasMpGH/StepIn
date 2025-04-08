from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel


# Message models
class MessageCreate(BaseModel):
    email: str
    text: str
    meeting_id: Optional[int] = None


class Message(BaseModel):
    email: str
    message: str
    timestamp: datetime
    meeting_id: Optional[int] = None


class MessageListResponse(BaseModel):
    messages: List[Message]