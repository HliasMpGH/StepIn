from app.db.database import get_database
from app.services.redis_service import get_redis_manager

class ChatService:
    def __init__(self):
        self.db = get_database()
        self.redis_mgr = get_redis_manager()
    
    def post_message(self, email, text, meeting_id=None):
        """Post a message to a meeting chat"""
        # Check if user exists
        user = self.db.get_user(email)
        if not user:
            return {"error": "User not found"}
        
        # Post message to Redis
        result = self.redis_mgr.post_message(email, text, meeting_id)
        if result:
            # If successful, also store in the database for persistence
            if not meeting_id:
                meeting_id = self.redis_mgr.get_user_joined_meeting(email)
            
            if meeting_id:
                self.db.save_chat_message(meeting_id, email, text)
                return {"success": True}
        
        return {"error": "Failed to post message"}
    
    def get_user_messages(self, email, meeting_id=None):
        """Get all messages posted by a user"""
        # Check if user exists
        user = self.db.get_user(email)
        if not user:
            return {"error": "User not found"}
        
        return self.redis_mgr.get_user_meeting_messages(email, meeting_id)