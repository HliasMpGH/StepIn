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

        # Try to join meeting in Redis
        result = self.redis_mgr.join_meeting(email, meeting_id)
        if isinstance(result, dict) and "error" in result:
            return {"error": f"Failed to join meeting: {result['error']}"}

        # Log the action
        self.db.log_action(email, meeting_id, JOIN_MEETING)

    def leave_meeting(self, email, meeting_id):
        """User leaves a meeting"""
        # Check if user exists
        user = self.db.get_user(email)
        if not user:
            return {"error": "User not found"}

        # Try to leave meeting in Redis
        result = self.redis_mgr.leave_meeting(email, meeting_id)
        if result:
            # Log the action
            self.db.log_action(email, meeting_id, LEAVE_MEETING)
            return {"success": True}
        else:
            return {"error": "Failed to leave meeting"}

    def get_meeting_participants(self, meeting_id):
        """Get participants who have joined a meeting"""
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
        if meeting:
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
            return True
        return False

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
                success = self._activate_meeting_in_redis(meeting_id)
                print(f"Activated meeting {meeting_id} in Redis: {success}")

        # also do a sync to remove inactive meetings from redis
        meetings_to_remove = redis_meeting_ids - db_meeting_ids
        if meetings_to_remove:
            print(f"Removing {len(meetings_to_remove)} meetings from Redis: {meetings_to_remove}")
            for meeting_id in meetings_to_remove:
                success = self.end_meeting(meeting_id)
                print(f"Deactivated meeting {meeting_id} in Redis: {success}")

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

        return {
            "success": True,
            "timed_out_participants": remaining_participants
        }

    def get_meeting_messages(self, meeting_id):
        """Get all messages from a meeting chat"""
        return self.redis_mgr.get_meeting_messages(meeting_id)