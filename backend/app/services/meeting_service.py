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

        try:
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

            # Process meeting in Redis based on time
            now = datetime.now(timezone.utc)

            # Always attempt to activate in Redis (it will handle categorization)
            result = self.redis_mgr.activate_meeting(
                meeting_id,
                title,
                description,
                lat,
                long,
                participants,
                t1_datetime,
                t2_datetime
            )

            # Force a sync to make sure Redis is updated
            self.sync_meetings()
            return meeting_id
        except Exception as e:
            return {"error": f"Failed to create meeting: {str(e)}"}

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
        # try to find in cache
        meeting = self.redis_mgr.get_meeting_by_id(meeting_id)

        if not meeting:
            print("getting from db")
            # cache miss, retrieve from db
            meeting = self.db.get_meeting(meeting_id)
            # cast the stringified participants into a list
            # to be consistent with the return type
            meeting["participants"] = map(
                lambda email: email.strip(),
                meeting["participants"].split(",")
            )
        else:
            print("got from cache")

        return meeting

    def find_nearby_meetings(self, email, x, y):
        """Find nearby active meetings that the user can join"""
        # Retrieve nearby active meetings for the user from Redis
        result = self.redis_mgr.get_nearby_meetings_for_user(email, x, y)
        # If no meetings found or empty set, return empty list
        if not result:
            return []
        # Convert meeting IDs to integers
        try:
            return [int(mid) for mid in result]
        except Exception:
            return []

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
        return redis_meetings

    def get_upcoming_meetings(self):
        """Get all upcoming meetings"""
        # Sync meetings to make sure Redis is up to date
        self.sync_meetings()
        redis_meetings = self.redis_mgr.get_upcoming_meetings()
        print(f"Updated Redis upcoming meetings: {redis_meetings}")
        return redis_meetings

    def _get_active_meetings_from_db(self):
        """Get active meetings directly from the database"""
        return self.db.get_active_meetings()

    def _get_upcoming_meetings_from_db(self):
        """Get upcoming meetings directly from the database"""
        return self.db.get_upcoming_meetings()

    def _activate_meeting_in_redis(self, meeting_id):
        """Activate a meeting in Redis from the database"""
        meeting = self.db.get_meeting(meeting_id)
        if not meeting:
            return {"error": "Could not find meeting"}

        # Activate meeting in Redis
        return self.redis_mgr.activate_meeting(
            meeting_id,
            meeting["title"],
            meeting["description"],
            meeting["lat"],
            meeting["long"],
            meeting["participants"],
            meeting["t1"],
            meeting["t2"]
        )


    def sync_meetings(self):
        """Force a sync to make sure Redis and DB are in sync"""
        try:
            # Get current active and upcoming meetings from database
            db_active_meetings = self._get_active_meetings_from_db()
            db_upcoming_meetings = self._get_upcoming_meetings_from_db()

            # Get active and upcoming meetings in redis
            redis_active_meetings = self.redis_mgr.get_active_meetings()
            redis_upcoming_meetings = self.redis_mgr.get_upcoming_meetings()

            # Find meetings in DB but not in Redis
            db_active_ids = set(str(mid) for mid in db_active_meetings)
            db_upcoming_ids = set(str(mid) for mid in db_upcoming_meetings)
            redis_active_ids = set(str(mid) for mid in redis_active_meetings)
            redis_upcoming_ids = set(str(mid) for mid in redis_upcoming_meetings)

            # Log current state
            print(f"DB active meetings: {db_active_ids}")
            print(f"DB upcoming meetings: {db_upcoming_ids}")
            print(f"Redis active meetings: {redis_active_ids}")
            print(f"Redis upcoming meetings: {redis_upcoming_ids}")

            meetings_to_end = self.redis_mgr.sync_meeting_status()
            for meeting_id in meetings_to_end:
                result = self.end_meeting(int(meeting_id))
                print(f"Meeting {meeting_id} ended during sync: {result}")

            # Meetings to add to Redis (in DB but not in Redis)
            db_all_meeting_ids = db_active_ids.union(db_upcoming_ids)
            redis_all_meeting_ids = redis_active_ids.union(redis_upcoming_ids)
            meetings_to_add = db_all_meeting_ids - redis_all_meeting_ids

            if meetings_to_add:
                print(f"Syncing {len(meetings_to_add)} meetings from DB to Redis: {meetings_to_add}")
                for meeting_id in meetings_to_add:
                    result = self._activate_meeting_in_redis(int(meeting_id))
                    if isinstance(result, dict) and "error" in result:
                        print(f"Error while activating meeting: {result['error']}")
                    else:
                        print(f"Activated meeting {meeting_id} in Redis")

            # Meetings to remove from Redis (in Redis but not in DB)
            meetings_to_remove = redis_all_meeting_ids - db_all_meeting_ids
            if meetings_to_remove:
                print(f"Removing {len(meetings_to_remove)} meetings from Redis: {meetings_to_remove}")
                for meeting_id in meetings_to_remove:
                    result = self.end_meeting(int(meeting_id))
                    if isinstance(result, dict) and "error" in result:
                        print(f"Error while deactivating meeting: {result['error']}")
                    else:
                        print(f"Deactivated meeting {meeting_id} in Redis: {result}")

            return True
        except Exception as e:
            print(f"Error in sync_meetings: {e}")
            return False

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

    def get_meetings_by_user(self, email: str):
        """
        Retrieve all meetings where the given email is listed as a participant.
        """
        # Query DB for meetings matching the user
        meetings = self.db.get_meetings_by_user(email)

        # Return meeting IDs only
        if meetings:
            # Convert to integer IDs
            meeting_ids = [meeting.get('meeting_id') for meeting in meetings]
            print(f"Returning meeting IDs: {meeting_ids}")
            return meeting_ids
        return []

    def delete_meeting(self, meeting_id: int, email: str = None):
        """
        Delete a meeting. If email is provided, ensure the user is authorized.
        """
        # Fetch meeting
        meeting = self.get_meeting(meeting_id)
        if not meeting:
            return None

        # If email is provided, ensure user is creator/participant
        if email and email not in meeting.get("participants", ""):
            return {"error": "Not authorized to delete this meeting"}

        # Deactivate in Redis if active
        if self.redis_mgr.redis_client.sismember(self.redis_mgr.active_meetings_key, str(meeting_id)):
            self.redis_mgr.deactivate_meeting(meeting_id)

        # Delete in DB
        result = self.db.delete_meeting(meeting_id)
        return result