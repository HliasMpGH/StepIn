import json
import redis
import fakeredis
from geopy.distance import geodesic
from datetime import datetime

from app.core.config import settings

class RedisManager:
    def __init__(self, fake=None):
        # Determine if using fake Redis based on settings or override parameter
        use_fake = fake if fake is not None else settings.USE_FAKE_REDIS
        
        if use_fake:
            self.redis_client = fakeredis.FakeStrictRedis(decode_responses=True)
        else:
            self.redis_client = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=settings.REDIS_DB,
                decode_responses=True
            )
        
        # Redis keys
        self.active_meetings_key = "active_meetings"  # Set of active meeting IDs
        self.meeting_prefix = "meeting:"  # Prefix for meeting hash
        self.participants_prefix = "participants:"  # Prefix for participants set
        self.joined_prefix = "joined:"  # Prefix for joined participants set
        self.chat_prefix = "chat:"  # Prefix for chat list
        self.user_meetings_prefix = "user_meetings:"  # Prefix for user's joined meetings
    
    def activate_meeting(self, meeting_id, title, description, lat, long, participants, t2):
        """Activate a meeting in Redis"""
        # Store meeting details
        meeting_key = f"{self.meeting_prefix}{meeting_id}"
        meeting_data = {
            "id": meeting_id,
            "title": title,
            "description": description,
            "lat": lat,
            "long": long,
            "participants": participants,
            "t2": t2.isoformat() if isinstance(t2, datetime) else t2
        }
        self.redis_client.hset(meeting_key, mapping=meeting_data)
        
        # Add to active meetings set
        self.redis_client.sadd(self.active_meetings_key, meeting_id)
        
        # Initialize participants set
        participants_key = f"{self.participants_prefix}{meeting_id}"
        for email in participants.split(","):
            self.redis_client.sadd(participants_key, email.strip())
        
        # Initialize joined participants set
        joined_key = f"{self.joined_prefix}{meeting_id}"
        self.redis_client.delete(joined_key)  # Ensure it's empty
        
        # Initialize chat list
        chat_key = f"{self.chat_prefix}{meeting_id}"
        self.redis_client.delete(chat_key)  # Ensure it's empty
        
        return True
    
    def deactivate_meeting(self, meeting_id):
        """Deactivate a meeting in Redis"""
        # Remove from active meetings set
        self.redis_client.srem(self.active_meetings_key, meeting_id)
        
        # Get list of joined participants for timeout logging
        joined_key = f"{self.joined_prefix}{meeting_id}"
        joined_participants = self.redis_client.smembers(joined_key)
        
        # Clean up Redis keys
        meeting_key = f"{self.meeting_prefix}{meeting_id}"
        participants_key = f"{self.participants_prefix}{meeting_id}"
        chat_key = f"{self.chat_prefix}{meeting_id}"
        
        # For each joined user, remove this meeting from their active meetings
        for email in joined_participants:
            user_meetings_key = f"{self.user_meetings_prefix}{email}"
            self.redis_client.srem(user_meetings_key, meeting_id)
        
        # Delete all keys related to this meeting
        self.redis_client.delete(meeting_key, participants_key, joined_key, chat_key)
        
        return list(joined_participants)
    
    def get_active_meetings(self):
        """Get list of all active meeting IDs"""
        meetings = self.redis_client.smembers(self.active_meetings_key)
        return [int(m) for m in meetings] if meetings else []
    
    def get_nearby_meetings_for_user(self, email, x, y, max_distance=100):
        """Get active meetings near user's location where user is a participant"""
        active_meetings = self.get_active_meetings()
        nearby_meetings = []
        
        for meeting_id in active_meetings:
            # Check if user is in participants list
            participants_key = f"{self.participants_prefix}{meeting_id}"
            if not self.redis_client.sismember(participants_key, email):
                continue
            
            # Get meeting details
            meeting_key = f"{self.meeting_prefix}{meeting_id}"
            meeting = self.redis_client.hgetall(meeting_key)
            
            if not meeting:
                continue
            
            # Calculate distance
            meeting_location = (float(meeting["lat"]), float(meeting["long"]))
            user_location = (float(x), float(y))
            distance = geodesic(meeting_location, user_location).meters
            
            if distance <= max_distance:
                nearby_meetings.append(int(meeting_id))
        
        return nearby_meetings
    
    def join_meeting(self, email, meeting_id):
        """User joins a meeting"""
        # Check if meeting is active
        if not self.redis_client.sismember(self.active_meetings_key, meeting_id):
            return False
        
        # Check if user is in participants list
        participants_key = f"{self.participants_prefix}{meeting_id}"
        if not self.redis_client.sismember(participants_key, email):
            return False
        
        # Add user to joined participants
        joined_key = f"{self.joined_prefix}{meeting_id}"
        self.redis_client.sadd(joined_key, email)
        
        # Add meeting to user's joined meetings
        user_meetings_key = f"{self.user_meetings_prefix}{email}"
        self.redis_client.sadd(user_meetings_key, meeting_id)
        
        return True
    
    def leave_meeting(self, email, meeting_id):
        """User leaves a meeting"""
        # Check if meeting is active
        if not self.redis_client.sismember(self.active_meetings_key, meeting_id):
            return False
        
        # Remove user from joined participants
        joined_key = f"{self.joined_prefix}{meeting_id}"
        result = self.redis_client.srem(joined_key, email)
        
        # Remove meeting from user's joined meetings
        user_meetings_key = f"{self.user_meetings_prefix}{email}"
        self.redis_client.srem(user_meetings_key, meeting_id)
        
        return result > 0
    
    def get_joined_participants(self, meeting_id):
        """Get list of emails of participants who have joined the meeting"""
        joined_key = f"{self.joined_prefix}{meeting_id}"
        return list(self.redis_client.smembers(joined_key))
    
    def post_message(self, email, message, meeting_id=None):
        """User posts a message to a meeting chat"""
        # If meeting_id not provided, get it from user's joined meetings
        if not meeting_id:
            user_meetings_key = f"{self.user_meetings_prefix}{email}"
            user_meetings = list(self.redis_client.smembers(user_meetings_key))
            if not user_meetings:
                return False
            # Assuming user can only join one meeting at a time
            meeting_id = user_meetings[0]
        
        # Check if user has joined the meeting
        joined_key = f"{self.joined_prefix}{meeting_id}"
        if not self.redis_client.sismember(joined_key, email):
            return False
        
        # Create message object
        chat_message = {
            "email": email,
            "message": message,
            "timestamp": datetime.now().isoformat()
        }
        
        # Add message to chat list
        chat_key = f"{self.chat_prefix}{meeting_id}"
        self.redis_client.rpush(chat_key, json.dumps(chat_message))
        
        return True
    
    def get_meeting_messages(self, meeting_id):
        """Get all messages from a meeting chat in chronological order"""
        chat_key = f"{self.chat_prefix}{meeting_id}"
        messages = self.redis_client.lrange(chat_key, 0, -1)
        return [json.loads(msg) for msg in messages]
    
    def get_user_meeting_messages(self, email, meeting_id=None):
        """Get all messages posted by a user in a meeting"""
        # If meeting_id not provided, get it from user's joined meetings
        if not meeting_id:
            user_meetings_key = f"{self.user_meetings_prefix}{email}"
            user_meetings = list(self.redis_client.smembers(user_meetings_key))
            if not user_meetings:
                return []
            # Assuming user can only join one meeting at a time
            meeting_id = user_meetings[0]
        
        chat_key = f"{self.chat_prefix}{meeting_id}"
        all_messages = self.redis_client.lrange(chat_key, 0, -1)
        
        # Filter messages by email
        user_messages = []
        for msg_str in all_messages:
            msg = json.loads(msg_str)
            if msg["email"] == email:
                user_messages.append(msg)
        
        return user_messages
    
    def get_user_joined_meeting(self, email):
        """Get the meeting ID that a user has joined (if any)"""
        user_meetings_key = f"{self.user_meetings_prefix}{email}"
        user_meetings = list(self.redis_client.smembers(user_meetings_key))
        return user_meetings[0] if user_meetings else None


# Redis manager singleton
_redis_instance = None

def get_redis_manager():
    """Get or create the Redis manager instance"""
    global _redis_instance
    if _redis_instance is None:
        _redis_instance = RedisManager()
    return _redis_instance