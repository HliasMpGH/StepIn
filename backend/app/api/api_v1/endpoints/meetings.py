from fastapi import APIRouter, HTTPException, Depends

from app.models.meeting import MeetingCreate, Meeting, MeetingIdResponse, MeetingListResponse
from app.models.user import JoinLeaveRequest, SuccessResponse, ErrorResponse, ParticipantListResponse, EndMeetingResponse
from app.models.message import MessageListResponse
from app.services.meeting_service import MeetingService

router = APIRouter()
meeting_service = MeetingService()


@router.post("", response_model=MeetingIdResponse, responses={400: {"model": ErrorResponse}})
async def create_meeting(meeting: MeetingCreate):
    try:
        meeting_id = meeting_service.create_meeting(
            meeting.title,
            meeting.description,
            meeting.t1,
            meeting.t2,
            meeting.lat,
            meeting.long,
            meeting.participants
        )
        return MeetingIdResponse(meeting_id=meeting_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/active", response_model=MeetingListResponse)
async def active_meetings():
    try:
        meetings = meeting_service.get_active_meetings()
        if meetings is None:
            meetings = []
        return MeetingListResponse(meetings=meetings)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/nearby", response_model=MeetingListResponse)
async def nearby_meetings(email: str, x: float, y: float):
    try:
        # Convert string parameters to appropriate types
        x_float = float(x)
        y_float = float(y)
        
        result = meeting_service.find_nearby_meetings(email, x_float, y_float)
        if isinstance(result, dict) and "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        if result is None:
            result = []
        return MeetingListResponse(meetings=result)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid latitude or longitude values")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{meeting_id}", response_model=Meeting, responses={404: {"model": ErrorResponse}})
async def get_meeting(meeting_id: int):
    meeting = meeting_service.get_meeting(meeting_id)
    if meeting is None:
        raise HTTPException(status_code=404, detail="Meeting not found")
    return meeting


@router.post("/{meeting_id}/join", response_model=SuccessResponse, responses={400: {"model": ErrorResponse}})
async def join_meeting(meeting_id: int, request: JoinLeaveRequest):
    result = meeting_service.join_meeting(request.email, meeting_id)
    if isinstance(result, dict) and "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return SuccessResponse()


@router.post("/{meeting_id}/leave", response_model=SuccessResponse, responses={400: {"model": ErrorResponse}})
async def leave_meeting(meeting_id: int, request: JoinLeaveRequest):
    result = meeting_service.leave_meeting(request.email, meeting_id)
    if isinstance(result, dict) and "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return SuccessResponse()


@router.get("/{meeting_id}/participants", response_model=ParticipantListResponse)
async def meeting_participants(meeting_id: int):
    participants = meeting_service.get_meeting_participants(meeting_id)
    return ParticipantListResponse(participants=participants)


@router.post("/{meeting_id}/end", response_model=EndMeetingResponse)
async def end_meeting(meeting_id: int):
    result = meeting_service.end_meeting(meeting_id)
    if isinstance(result, dict) and "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return EndMeetingResponse(
        success=result["success"],
        timed_out_participants=result["timed_out_participants"]
    )


@router.get("/{meeting_id}/messages", response_model=MessageListResponse)
async def meeting_messages(meeting_id: int):
    messages = meeting_service.get_meeting_messages(meeting_id)
    return MessageListResponse(messages=messages)