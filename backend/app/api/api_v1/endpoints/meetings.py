from fastapi import APIRouter, HTTPException, Depends

from app.models.meeting import MeetingCreate, MeetingResponse, MeetingIdResponse, MeetingListResponse
from app.models.user import JoinLeaveRequest, SuccessResponse, ErrorResponse, ParticipantListResponse, EndMeetingResponse
from app.models.message import MessageListResponse
from app.services.meeting_service import MeetingService

router = APIRouter()
meeting_service = MeetingService()


@router.post("", response_model=MeetingIdResponse, responses={400: {"model": ErrorResponse}})
async def create_meeting(meeting: MeetingCreate):
    try:
        result = meeting_service.create_meeting(
            meeting.title,
            meeting.description,
            meeting.t1,
            meeting.t2,
            meeting.lat,
            meeting.long,
            meeting.participants
        )

        # Force refresh the active meetings list to ensure new meeting is included
        # This step will sync the DB and Redis after a new meeting is created
        # meeting_service.get_active_meetings()
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to create meeting")

    if isinstance(result, dict) and "error" in result:
        raise HTTPException(status_code=400, detail=f"Error while creating meeting: {result['error']}")
    return MeetingIdResponse(meeting_id=result)

@router.delete("/{meeting_id}", response_model=SuccessResponse, responses={404: {"model": ErrorResponse}})
async def delete_meeting(meeting_id: int, email: str = None):
    try:
        if email:
            result = meeting_service.delete_meeting(meeting_id, email)
        else:
            result = meeting_service.delete_meeting(meeting_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete meeting: {str(e)}")

    if result is None:
        raise HTTPException(status_code=404, detail="Meeting not found")

    if isinstance(result, dict) and "error" in result:
        raise HTTPException(status_code=400, detail=f"Failed to delete meeting: {result['error']}")

    return SuccessResponse()

@router.get("/{email}/meetings", response_model=MeetingListResponse)
async def get_user_meetings(email: str):
    """
    Retrieve all meetings created by a specific user.
    """
    try:
        meetings = meeting_service.get_meetings_by_user(email)
        if meetings is None:
            meetings = []
        return MeetingListResponse(meetings=meetings)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to retrieve user meetings")

@router.delete("/meetings/{meeting_id}", response_model=MeetingListResponse)
async def delete_user_meeting(meeting_id: int, email: str):
    """
    Delete a meeting created by the user and return the updated list.
    """
    try:
        # Ensure the user is the creator of the meeting
        result = meeting_service.delete_meeting(meeting_id, email)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to delete meeting")

    if isinstance(result, dict) and "error" in result:
        raise HTTPException(status_code=400, detail=f"Failed to delete meeting: {result['error']}")

    # After deletion, return the updated list
    try:
        meetings = meeting_service.get_meetings_by_user(email)
        if meetings is None:
            meetings = []
    except Exception:
        meetings = []

    return MeetingListResponse(meetings=meetings)

@router.get("/active", response_model=MeetingListResponse)
async def active_meetings():
    try:
        meetings = meeting_service.get_active_meetings()
        if meetings is None:
            meetings = []
        return MeetingListResponse(meetings=meetings)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to retrieve active meetings")


@router.get("/nearby", response_model=MeetingListResponse)
async def nearby_meetings(email: str, x: float, y: float):
    try:
        # Convert string parameters to appropriate types
        x_float = float(x)
        y_float = float(y)

        result = meeting_service.find_nearby_meetings(email, x_float, y_float)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Failed to retrieve nearby meetings: Invalid latitude or longitude values"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to retrieve nearby meetings")

    if isinstance(result, dict) and "error" in result:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to retrieve nearby meetings: {result['error']}"
        )
    if result is None:
        result = []
    return MeetingListResponse(meetings=result)


@router.get("/{meeting_id}", response_model=MeetingResponse, responses={404: {"model": ErrorResponse}})
async def get_meeting(meeting_id: int):
    try:
        meeting = meeting_service.get_meeting(meeting_id)
    except:
        raise HTTPException(status_code=500, detail="Failed to retrieve meeting")

    if meeting is None:
        raise HTTPException(status_code=404, detail="Failed to retrieve meeting: Meeting not found")
    return meeting


@router.post("/{meeting_id}/join", response_model=SuccessResponse, responses={400: {"model": ErrorResponse}})
async def join_meeting(meeting_id: int, request: JoinLeaveRequest):
    try:
        result = meeting_service.join_meeting(request.email, meeting_id)
    except:
        raise HTTPException(status_code=500, detail="Failed to join meeting")

    if isinstance(result, dict) and "error" in result:
        raise HTTPException(status_code=400, detail=f"Failed to join meeting: {result['error']}")
    return SuccessResponse()


@router.post("/{meeting_id}/leave", response_model=SuccessResponse, responses={400: {"model": ErrorResponse}})
async def leave_meeting(meeting_id: int, request: JoinLeaveRequest):
    try:
        result = meeting_service.leave_meeting(request.email, meeting_id)
    except:
        raise HTTPException(status_code=500, detail="Failed to leave meeting")

    if isinstance(result, dict) and "error" in result:
        raise HTTPException(status_code=400, detail=f"Failed to leave meeting: {result['error']}")
    return SuccessResponse()


@router.get("/upcoming", response_model=None)  # Αφαιρώ το response_model προσωρινά
async def upcoming_meetings():
    try:
        meetings = meeting_service.get_upcoming_meetings()
        if meetings is None:
            meetings = []

        return {"meetings": meetings}
    except Exception as e:
        print(f"Error in upcoming_meetings: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve upcoming meetings")

    try:

        meetings = meeting_service.get_upcoming_meetings()

        if meetings is None:
            meetings_list = []
        elif isinstance(meetings, set):
            meetings_list = [int(m) for m in meetings]
        elif isinstance(meetings, list):

            meetings_list = [int(m) if isinstance(m, str) else m for m in meetings]
        else:

            meetings_list = list(meetings)

        print(f"Final meetings list: {meetings_list}, type: {type(meetings_list)}")

        result = {"meetings": meetings_list}
        print(f"Final JSON result: {result}")

        return result
    except Exception as e:
        import traceback
        print(f"Error in upcoming_meetings: {str(e)}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to retrieve upcoming meetings: {str(e)}")

@router.get("/{meeting_id}/participants", response_model=ParticipantListResponse)
async def meeting_participants(meeting_id: int):
    try:
        result = meeting_service.get_meeting_participants(meeting_id)
    except:
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve meeting joined participants"
        )

    if isinstance(result, dict) and "error" in result:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to retrieve meeting joined participants: {result['error']}"
        )
    return ParticipantListResponse(participants=result)


@router.post("/{meeting_id}/end", response_model=EndMeetingResponse)
async def end_meeting(meeting_id: int):
    try:
        result = meeting_service.end_meeting(meeting_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to end meeting")

    if isinstance(result, dict) and "error" in result:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to end meeting: {result['error']}"
        )
    return EndMeetingResponse(
        success=True,
        timed_out_participants=result
    )


@router.get("/{meeting_id}/messages", response_model=MessageListResponse)
async def meeting_messages(meeting_id: int):
    try:
        result = meeting_service.get_meeting_messages(meeting_id)
    except:
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve messages of meeting"
        )

    if isinstance(result, dict) and "error" in result:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to retrieve messages of meeting: {result['error']}"
        )
    return MessageListResponse(messages=result)


@router.get("/{meeting_id}/messages/{email}", response_model=MessageListResponse)
async def user_messages(meeting_id: int, email: str):
    try:
        result = meeting_service.get_user_messages(email, meeting_id)
    except:
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve messages of user"
        )

    if isinstance(result, dict) and "error" in result:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to retrieve messages of user: {result['error']}"
        )
    return MessageListResponse(messages=result)