from app.db.database import get_database
from app.services.redis_service import get_redis_manager

class ChatService:
    def __init__(self):
        self.db = get_database()
        self.redis_mgr = get_redis_manager()

    def post_message(self, email, text):
        """Post a message to a meeting chat"""
        # Check if user exists
        user = self.db.get_user(email)
        if not user:
            return {"error": "User not found"}

        # Post message to Redis
        result = self.redis_mgr.post_message(email, text)
        if isinstance(result, dict) and "error" in result:
            return result # error message
