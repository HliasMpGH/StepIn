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
        self.user_joined_meeting = "user_joined_meeting:"  # Prefix for user's joined meeting

    def activate_meeting(self, meeting_id, title, description, lat, long, participants, t2):
        """Activate a meeting in Redis"""
        print(f"Activating meeting in Redis: ID={meeting_id}, title={title}")

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

        # Add to active meetings set - convert meeting_id to string for Redis
        meeting_id_str = str(meeting_id)
        self.redis_client.sadd(self.active_meetings_key, meeting_id_str)

        # Initialize participants set
        participants_key = f"{self.participants_prefix}{meeting_id}"
        for email in participants.split(","):
            email_clean = email.strip()
            if email_clean:  # Skip empty emails
                self.redis_client.sadd(participants_key, email_clean)

        # Initialize joined participants set
        joined_key = f"{self.joined_prefix}{meeting_id}"
        self.redis_client.delete(joined_key)  # Ensure it's empty

        # Initialize chat list
        chat_key = f"{self.chat_prefix}{meeting_id}"
        self.redis_client.delete(chat_key)  # Ensure it's empty

        # Verify the meeting was added
        is_active = self.redis_client.sismember(self.active_meetings_key, meeting_id_str)
        print(f"Meeting {meeting_id} active status in Redis: {is_active}")

        return True

    def deactivate_meeting(self, meeting_id):
        """Deactivate a meeting in Redis"""
        # Convert to string for Redis
        meeting_id_str = str(meeting_id)

        # Remove from active meetings set
        self.redis_client.srem(self.active_meetings_key, meeting_id_str)

        # Get list of joined participants for timeout logging
        joined_key = f"{self.joined_prefix}{meeting_id}"
        joined_participants = self.redis_client.smembers(joined_key)

        # Clean up Redis keys
        meeting_key = f"{self.meeting_prefix}{meeting_id}"
        participants_key = f"{self.participants_prefix}{meeting_id}"
        chat_key = f"{self.chat_prefix}{meeting_id}"

        # For each joined user, remove this meeting from their active meetings
        for email in joined_participants:
            user_meetings_key = f"{self.user_joined_meeting}{email}"
            self.redis_client.delete(user_meetings_key)

        # Delete all keys related to this meeting
        self.redis_client.delete(meeting_key, participants_key, joined_key, chat_key)

        print(f"Deactivated meeting {meeting_id} from Redis")
        return list(joined_participants)

    def get_active_meetings(self):
        """Get list of all active meeting IDs"""
        meetings = self.redis_client.smembers(self.active_meetings_key)
        print(f"Raw Redis active meetings: {meetings}")

        # Convert string IDs to integers
        result = [int(m) for m in meetings] if meetings else []
        print(f"Converted Redis active meetings: {result}")
        return result

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

        # Check if user is on other meeting
        user_meetings_key = f"{self.user_joined_meeting}{email}"
        if self.redis_client.get(user_meetings_key) is not None:
            print(f"{email} is already in other meeting ({self.redis_client.get(user_meetings_key)})")
            return False

        # Check if meeting is active
        if not self.redis_client.sismember(self.active_meetings_key, meeting_id):
            print(f"{meeting_id} is not active")
            return False

        # Check if user is in participants list
        participants_key = f"{self.participants_prefix}{meeting_id}"
        if not self.redis_client.sismember(participants_key, email):
            print(f"{email} not member of {meeting_id}")
            return False

        # Add user to joined participants
        joined_key = f"{self.joined_prefix}{meeting_id}"
        self.redis_client.sadd(joined_key, email)

        print(f"{email} joined meeting {meeting_id}")
        # Set meeting to user's joined meeting

        self.redis_client.set(user_meetings_key, meeting_id)
        print(f"all good. User joined meeting: {self.redis_client.get(user_meetings_key)}")
        return True

    def leave_meeting(self, email, meeting_id):
        """User leaves a meeting"""

        # Check if user is in the meeting
        user_meetings_key = f"{self.user_joined_meeting}{email}"
        if self.redis_client.get(user_meetings_key) != str(meeting_id):
            print(f"{email} is not joined in meeting {self.redis_client.get(user_meetings_key)}")
            return False

        # Check if meeting is active
        if not self.redis_client.sismember(self.active_meetings_key, meeting_id):
            print(f"{meeting_id} is not active")
            return False

        # Remove user from joined participants
        joined_key = f"{self.joined_prefix}{meeting_id}"
        result = self.redis_client.srem(joined_key, email)
        print(f"removed from list")

        # Delete meeting from user's joined meeting
        self.redis_client.delete(user_meetings_key)
        print(f"all good. User joined meeting: {self.redis_client.get(user_meetings_key)}")

        return result > 0

    def get_joined_participants(self, meeting_id):
        """Get list of emails of participants who have joined the meeting"""
        joined_key = f"{self.joined_prefix}{meeting_id}"
        return list(self.redis_client.smembers(joined_key))

    def post_message(self, email, message):
        """User posts a message to a meeting chat"""

        # Get the meeting the user is joined in
        meeting_id = self.get_user_joined_meeting(email)
        if not meeting_id:
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
        # If meeting_id not provided, get it from user's joined meeting
        if not meeting_id:
            meeting_id = self.get_user_joined_meeting(email)
            if not meeting_id:
                return []

        # check if meeting is active
        active_meetings_key = f"{self.active_meetings_key}{meeting_id}"
        if not self.redis_client.sismember(active_meetings_key, meeting_id):
            return [] # inactive meeting

        # check if user is a participant of the meeting
        participants_key = f"{self.participants_prefix}{meeting_id}"
        if not self.redis_client.sismember(participants_key, email):
            return [] # user is not a participant of the meeting

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
        user_meeting_key = f"{self.user_joined_meeting}{email}"
        meeting_id = self.redis_client.get(user_meeting_key)
        return meeting_id


# Redis manager singleton
_redis_instance = None

def get_redis_manager():
    """Get or create the Redis manager instance"""
    global _redis_instance
    if _redis_instance is None:
        _redis_instance = RedisManager()
    return _redis_instance