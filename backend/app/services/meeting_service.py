from app.db.database import get_database
from app.services.redis_service import get_redis_manager
from app.core.constants import JOIN_MEETING, LEAVE_MEETING, TIME_OUT
from datetime import datetime

class MeetingService:
    def __init__(self):
        self.db = get_database()
        self.redis_mgr = get_redis_manager()
    
    def create_meeting(self, title, description, t1, t2, lat, long, participants):
        """Create a new meeting"""
        # Add to database
        meeting_id = self.db.add_meeting(title, description, t1, t2, lat, long, participants)
        
        # Also activate in Redis for real-time operations
        if meeting_id:
            # Check if this is a current/future meeting (not past)
            now = datetime.now().isoformat()
            if t2 > now:
                # Activate in Redis
                self.redis_mgr.activate_meeting(
                    meeting_id,
                    title,
                    description,
                    lat,
                    long,
                    participants,
                    t2
                )
                print(f"Meeting {meeting_id} created and activated in Redis")
        
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
        if result:
            # Log the action
            self.db.log_action(email, meeting_id, JOIN_MEETING)
            return {"success": True}
        else:
            return {"error": "Failed to join meeting"}
    
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
        # Check if we need to sync meetings from DB to Redis
        db_meetings = self._get_active_meetings_from_db()
        redis_meetings = self.redis_mgr.get_active_meetings()
        
        # If no meetings in Redis but we have meetings in the DB, sync them
        if len(redis_meetings) == 0 and len(db_meetings) > 0:
            print(f"Syncing {len(db_meetings)} meetings from DB to Redis")
            for meeting_id in db_meetings:
                self._activate_meeting_in_redis(meeting_id)
            # Get updated list after sync
            redis_meetings = self.redis_mgr.get_active_meetings()
        
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
    
    def end_meeting(self, meeting_id):
        """End a meeting and log timeouts for remaining participants"""
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