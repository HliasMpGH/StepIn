from app.db.database import get_database
from app.services.redis_service import get_redis_manager
from app.core.constants import JOIN_MEETING, LEAVE_MEETING, TIME_OUT
from datetime import datetime, timezone

class MeetingService:
    def __init__(self):
        self.db = get_database()
        self.redis_mgr = get_redis_manager()

    def create_meeting(self, title, description, t1, t2, lat, long, participants):
        """Create a new meeting"""

        # Check if the passed meeting attributes are valid
        errors = self.get_attribute_errors(title, t1, t2, lat, long, participants)
        if errors:
            # invalid meeting attributes
            return {"error": ". ".join(errors)}

        # Convert datetime strings to datetime objects if needed
        if isinstance(t1, str):
            t1_datetime = datetime.fromisoformat(t1.replace('Z', '+00:00'))
        else:
            t1_datetime = t1

        if isinstance(t2, str):
            t2_datetime = datetime.fromisoformat(t2.replace('Z', '+00:00'))
        else:
            t2_datetime = t2

        # Add to database
        meeting_id = self.db.add_meeting(title, description, t1_datetime, t2_datetime, lat, long, participants)

        if not meeting_id:
            return {"error": "Could not load meeting in memory, after persistence"}

        # Also activate in Redis for real-time operations
        # Get current time in UTC
        now = datetime.now(timezone.utc)
        print(f"Current time: {now}, Meeting end time: {t2_datetime}")

        # Check if this is a current meeting
        if t1_datetime < now < t2_datetime:
            # Activate in Redis
            result = self.redis_mgr.activate_meeting(
                meeting_id,
                title,
                description,
                lat,
                long,
                participants,
                t2_datetime
            )
            print(f"Meeting {meeting_id} created and activated in Redis: {result}")
        else:
            print(f"Meeting {meeting_id} created but not activated in Redis")

        return meeting_id

    def get_attribute_errors(self, title, t1, t2, lat, long, participants):
        """Collect and return all error messages of the given user inputs"""
        errors_messages = []

        if not isinstance(title, str) or not title.strip():
            errors_messages.append("Please provide a valid title")

        if not t1 or not t2:
            errors_messages.append("Please provide a valid time range")

        if not isinstance(lat, float) or not isinstance(long, float):
            errors_messages.append("Please provide a valid location")

        if not isinstance(participants, str) or not participants.strip():
            errors_messages.append("Please provide a valid list of participants")

        return errors_messages

    def get_meeting(self, meeting_id):
        """Get meeting details by ID"""
        return self.db.get_meeting(meeting_id)

    def find_nearby_meetings(self, email, x, y):
        """Find nearby active meetings that the user can join"""
        # Check if user exists
        user = self.db.get_user(email)
        if not user:
            return {"error": "User not found"}

        result = self.redis_mgr.get_nearby_meetings_for_user(email, x, y)
        if result is None:
            return []
        return result

    def join_meeting(self, email, meeting_id):
        """User joins a meeting"""
        # Check if user exists
        user = self.db.get_user(email)
        if not user:
            return {"error": "User not found"}

        # Check if meeting exists
        meeting = self.db.get_meeting(meeting_id)
        if not meeting:
            return {"error": "Meeting not found"}

        # Try to join meeting in Redis
        result = self.redis_mgr.join_meeting(email, meeting_id)
        if isinstance(result, dict) and "error" in result:
            return result # error message

        # Log the action
        self.db.log_action(email, meeting_id, JOIN_MEETING)

    def leave_meeting(self, email, meeting_id):
        """User leaves a meeting"""
        # Check if user exists
        user = self.db.get_user(email)
        if not user:
            return {"error": "User not found"}

        # Check if meeting exists
        meeting = self.db.get_meeting(meeting_id)
        if not meeting:
            return {"error": "Meeting not found"}

        # Try to leave meeting in Redis
        result = self.redis_mgr.leave_meeting(email, meeting_id)
        if isinstance(result, dict) and "error" in result:
            return result # error message

        # Log the action
        self.db.log_action(email, meeting_id, LEAVE_MEETING)

    def get_meeting_participants(self, meeting_id):
        """Get participants who have joined a meeting"""
        # Check if the meeting exists
        meeting = self.db.get_meeting(meeting_id)
        if not meeting:
            return {"error": "Could not find meeting"}

        return self.redis_mgr.get_joined_participants(meeting_id)

    def get_active_meetings(self):
        """Get all active meetings"""

        # sync active meetings in redis to have the most recent state in-memory
        self.sync_meetings()

        redis_meetings = self.redis_mgr.get_active_meetings()
        print(f"Updated Redis active meetings: {redis_meetings}")

        # # Extra validation - return all active meetings from DB if Redis is empty after sync
        # if not redis_meetings and db_meetings:
        #     print("Warning: Redis still has no meetings after sync, returning DB meetings")
        #     return db_meetings

        return redis_meetings

    def _get_active_meetings_from_db(self):
        """Get active meetings directly from the database"""
        return self.db.get_active_meetings()

    def _activate_meeting_in_redis(self, meeting_id):
        """Activate a meeting in Redis from the database"""
        meeting = self.db.get_meeting(meeting_id)
        if not meeting:
            return {"error": "Could not find meeting"}

        # Activate meeting in Redis
        self.redis_mgr.activate_meeting(
            meeting_id,
            meeting["title"],
            meeting["description"],
            meeting["lat"],
            meeting["long"],
            meeting["participants"],
            meeting["t2"]
        )

    def sync_meetings(self):
        """Force a sync to make sure Redis and DB are in sync"""

        # Get current active meetings from database
        db_meetings = self._get_active_meetings_from_db()
        # Get active meetings in redis
        redis_meetings = self.redis_mgr.get_active_meetings()

        # Find meetings in DB but not in Redis
        db_meeting_ids = set(db_meetings)
        redis_meeting_ids = set(redis_meetings)

        # Log current state
        print(f"DB active meetings: {db_meeting_ids}")
        print(f"Redis active meetings: {redis_meeting_ids}")

        # Meetings to add to Redis
        meetings_to_add = db_meeting_ids - redis_meeting_ids
        if meetings_to_add:
            print(f"Syncing {len(meetings_to_add)} meetings from DB to Redis: {meetings_to_add}")
            for meeting_id in meetings_to_add:
                result = self._activate_meeting_in_redis(meeting_id)
                if isinstance(result, dict) and "error" in result:
                    raise ValueError(f"Error while activating meeting: {result['error']}")
                print(f"Activated meeting {meeting_id} in Redis")

        # also do a sync to remove inactive meetings from redis
        meetings_to_remove = redis_meeting_ids - db_meeting_ids
        if meetings_to_remove:
            print(f"Removing {len(meetings_to_remove)} meetings from Redis: {meetings_to_remove}")
            for meeting_id in meetings_to_remove:
                result = self.end_meeting(meeting_id)
                if isinstance(result, dict) and "error" in result:
                    raise ValueError(f"Error while deactivating meeting: {result['error']}")
                print(f"Deactivated meeting {meeting_id} in Redis: {result}")

    def end_meeting(self, meeting_id):
        """End a meeting and log timeouts for remaining participants"""
        # Check if the meeting exists
        meeting = self.db.get_meeting(meeting_id)
        if not meeting:
            return {"error": "Could not find meeting"}

        # Deactivate meeting and get remaining participants
        remaining_participants = self.redis_mgr.deactivate_meeting(meeting_id)

        # Log timeout for remaining participants
        for email in remaining_participants:
            self.db.log_action(email, meeting_id, TIME_OUT)

        return remaining_participants

    def get_meeting_messages(self, meeting_id):
        """Get all messages from a meeting chat"""
        # Check if the meeting exists
        meeting = self.db.get_meeting(meeting_id)
        if not meeting:
            return {"error": "Could not find meeting"}

        return self.redis_mgr.get_meeting_messages(meeting_id)

    def get_user_messages(self, email, meeting_id=None):
        """Get all messages posted by a user"""
        # Check if the meeting exists
        if meeting_id:
            meeting = self.db.get_meeting(meeting_id)
            if not meeting:
                return {"error": "Could not find meeting"}

        # Check if user exists
        user = self.db.get_user(email)
        if not user:
            return {"error": "User not found"}

        return self.redis_mgr.get_user_meeting_messages(email, meeting_id)

    def delete_meeting(self, meeting_id):
        """Delete a meeting"""

        # Check if meeting exists
        meeting = self.get_meeting(meeting_id)
        if not meeting:
            return None

        # Check if meeting is active in Redis - deactivate first
        if self.redis_mgr.redis_client.sismember(self.redis_mgr.active_meetings_key, str(meeting_id)):
            # Deactivate meeting in Redis first
            self.redis_mgr.deactivate_meeting(meeting_id)

        # Delete the meeting from the database
        result = self.db.delete_meeting(meeting_id)

        if isinstance(result, dict) and "error" in result:
            return result  # Return error message

        return result  # Return True for success or None for not found

    def get_meetings_by_user(self, email: str):
        """
        Retrieve all meetings where the given email is listed as a participant.
        """
        # Query DB for meetings matching the user
        meetings = self.db.get_meetings_by_user(email)
        return meetings or []

    # Modify delete_meeting signature to enforce creator check:
    def delete_meeting(self, meeting_id: int, email: str):
        """
        Delete a meeting only if the given email is among its participants (assumed creator).
        """
        # Fetch meeting
        meeting = self.db.get_meeting(meeting_id)
        if not meeting:
            return None
        # Ensure user is creator/participant
        if email not in meeting.get("participants", ""):
            return {"error": "Not authorized to delete this meeting"}
        # Deactivate in Redis if active
        if self.redis_mgr.redis_client.sismember(self.redis_mgr.active_meetings_key, str(meeting_id)):
            self.redis_mgr.deactivate_meeting(meeting_id)
        # Delete in DB
        result = self.db.delete_meeting(meeting_id)
        return result