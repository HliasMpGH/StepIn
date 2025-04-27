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
        self.meeting_positions_key = "meeting_positions" # Key for meetings geospatials
        self.participants_prefix = "participants:"  # Prefix for participants set
        self.joined_prefix = "joined:"  # Prefix for joined participants set
        self.chat_prefix = "chat:"  # Prefix for chat list of meetings
        self.user_joined_meeting = "user_joined_meeting:"  # Prefix for user's joined meeting
        self.user_participate_meetings = "user_participate_meetings:"  # Prefix for all meetings the user is a participant

    def activate_meeting(self, meeting_id, title, description, lat, long, participants, t1, t2):
        """Activate a meeting in Redis"""
        print(f"Activating meeting in Redis: ID={meeting_id}, title={title}")

        # Store meeting details
        meeting_key = f"{self.meeting_prefix}{meeting_id}"
        meeting_data = {
            # "id": meeting_id,
            "title": title,
            "description": description,
            # "lat": lat,
            # "long": long,
            # "participants": participants,
            "t1": t1.isoformat() if isinstance(t1, datetime) else t1,
            "t2": t2.isoformat() if isinstance(t2, datetime) else t2
        }
        self.redis_client.hset(meeting_key, mapping=meeting_data)

        # Add geoposition of meeting
        self.redis_client.geoadd(self.meeting_positions_key, [lat, long, meeting_id])

        print(f"ADDED GEOSPATIAL")
        print(self.redis_client.zrange(self.meeting_positions_key, 0, -1))

        # Add to active meetings set - convert meeting_id to string for Redis
        meeting_id_str = str(meeting_id)
        self.redis_client.sadd(self.active_meetings_key, meeting_id_str)

        # Initialize participants set
        participants_key = f"{self.participants_prefix}{meeting_id}"
        for email in participants.split(","):
            email_clean = email.strip()
            if email_clean:  # Skip empty emails
                # add user to participant of meeting
                self.redis_client.sadd(participants_key, email_clean)

                # add meeting to the participated meetings of user (secondary index)
                user_participate_key = f"{self.user_participate_meetings}{email_clean}"
                self.redis_client.sadd(user_participate_key, meeting_id)

                print(f"{email_clean} participated meetings: {self.redis_client.smembers(user_participate_key)}")

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

        # Remove from geopositions
        self.redis_client.zrem(self.meeting_positions_key, meeting_id_str)

        print(f"REMOVED GEOSPATIAL")
        print(self.redis_client.zrange(self.meeting_positions_key, 0, -1))

        # Get list of joined participants for timeout logging
        joined_key = f"{self.joined_prefix}{meeting_id}"
        joined_participants = self.redis_client.smembers(joined_key)

        # Clean up Redis keys
        meeting_key = f"{self.meeting_prefix}{meeting_id}"
        participants_key = f"{self.participants_prefix}{meeting_id}"
        chat_key = f"{self.chat_prefix}{meeting_id}"

        # For each joined user, remove this meeting from their active meeting
        for email in joined_participants:
            user_meetings_key = f"{self.user_joined_meeting}{email}"
            self.redis_client.delete(user_meetings_key)

        # For each participant, remove this meeting from their participated meetings, and chats
        for email in self.redis_client.smembers(participants_key):
            user_participate_key = f"{self.user_participate_meetings}{email}"
            self.redis_client.srem(user_participate_key, meeting_id)
            self.redis_client.delete(f"{chat_key}:{email}") # remove messages indices of user
            print(f"removed {meeting_id} from {email}")
            print(f"{email} participated meetings: {self.redis_client.smembers(user_participate_key)}")

        # Delete all keys related to this meeting
        self.redis_client.delete(meeting_key, participants_key, joined_key, chat_key)

        print(f"Deactivated meeting {meeting_id} from Redis")
        return list(joined_participants)

    def get_meeting_by_id(self, meeting_id):
        """Get meeting attributes from a given a meeting id"""
        # get the basic meeting attributes
        meeting_key = f"{self.meeting_prefix}{meeting_id}"
        meeting = self.redis_client.hgetall(meeting_key)

        if not meeting:
            return None

        # get the position of the meeting
        long, lat = self.redis_client.geopos(self.meeting_positions_key, meeting_id)[0]

        # get the participants of the meeting
        meeting_participants_key = f"{self.participants_prefix}{meeting_id}"
        participants = self.redis_client.smembers(meeting_participants_key)

        # add all the attributes together
        meeting["meeting_id"] = meeting_id
        meeting["long"] = long
        meeting["lat"] = lat
        meeting["participants"] = participants

        return meeting

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

        # get all nearby meetings of (x, y) using meters
        nearby_meetings = self.redis_client.geosearch(
            self.meeting_positions_key,
            longitude=x,
            latitude=y,
            radius=max_distance,
            unit="m"
        )


        user_participate_key = f"{self.user_participate_meetings}{email}"
        meetings_participate = self.redis_client.smembers(user_participate_key)


        # Convert to consistent type
        nearby_meetings_str = set(str(m) for m in nearby_meetings)

        # the intersection of these sets are the nearby meetings the user can join
        return nearby_meetings_str & meetings_participate

    def join_meeting(self, email, meeting_id):
        """User joins a meeting"""

        # Check if user is on other meeting
        user_meetings_key = f"{self.user_joined_meeting}{email}"
        if self.redis_client.get(user_meetings_key) is not None:
            print(f"{email} is already in other meeting ({self.redis_client.get(user_meetings_key)})")
            return {"error": "You are already joined in another meeting"}

        # Check if meeting is active
        if not self.redis_client.sismember(self.active_meetings_key, meeting_id):
            print(f"{meeting_id} is not active")
            return {"error": f"Meeting {meeting_id} is not active"}

        # Check if user is in participants list
        participants_key = f"{self.participants_prefix}{meeting_id}"
        if not self.redis_client.sismember(participants_key, email):
            print(f"{email} not member of {meeting_id}")
            return {"error": "You are not a participant of the meeting"}

        # Add user to joined participants
        joined_key = f"{self.joined_prefix}{meeting_id}"
        self.redis_client.sadd(joined_key, email)

        print(f"{email} joined meeting {meeting_id}")
        # Set meeting to user's joined meeting

        self.redis_client.set(user_meetings_key, meeting_id)
        print(f"all good. User joined meeting: {self.redis_client.get(user_meetings_key)}")

    def leave_meeting(self, email, meeting_id):
        """User leaves a meeting"""

        # Check if user is in the meeting
        user_meetings_key = f"{self.user_joined_meeting}{email}"
        if self.redis_client.get(user_meetings_key) != str(meeting_id):
            print(f"{email} is not joined in meeting {self.redis_client.get(user_meetings_key)}")
            return {"error": "You are not joined in the meeting"}

        # Check if meeting is active
        if not self.redis_client.sismember(self.active_meetings_key, meeting_id):
            print(f"{meeting_id} is not active")
            return {"error": f"Meeting {meeting_id} is not active"}

        # Remove user from joined participants
        joined_key = f"{self.joined_prefix}{meeting_id}"
        result = self.redis_client.srem(joined_key, email)
        print(f"removed from list")

        # Delete meeting from user's joined meeting
        self.redis_client.delete(user_meetings_key)
        print(f"all good. User joined meeting: {self.redis_client.get(user_meetings_key)}")

        if result <= 0:
            return {"error": f"User not part of joined participants"}

    def get_joined_participants(self, meeting_id):
        """Get list of emails of participants who have joined the meeting"""
        joined_key = f"{self.joined_prefix}{meeting_id}"
        return list(self.redis_client.smembers(joined_key))

    def post_message(self, email, message):
        """User posts a message to a meeting chat"""

        # Get the meeting the user is joined in
        meeting_id = self.get_user_joined_meeting(email)
        if not meeting_id:
            return {"error": "User not joined in any meeting"}

        # Create message object
        chat_message = {
            "email": email,
            "message": message,
            "timestamp": datetime.now().isoformat()
        }

        # Add message to chat list of meeting
        chat_key = f"{self.chat_prefix}{meeting_id}"
        position = self.redis_client.rpush(chat_key, json.dumps(chat_message)) - 1

        # Add message index to chat list of user
        user_chat_key = f"{chat_key}:{email}"
        self.redis_client.rpush(user_chat_key, position)

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
        if not self.redis_client.sismember(self.active_meetings_key, meeting_id):
            return [] # inactive meeting

        # check if user is a participant of the meeting
        participants_key = f"{self.participants_prefix}{meeting_id}"
        if not self.redis_client.sismember(participants_key, email):
            return [] # user is not a participant of the meeting

        meeting_chat_key = f"{self.chat_prefix}{meeting_id}"

        # get the messages positions of the user in the meeting
        user_chat_key = f"{meeting_chat_key}:{email}"
        user_messages_positions = self.redis_client.lrange(user_chat_key, 0, -1)

        print(f"msgs positions: {user_messages_positions}")

        # get the final messages from the indices
        user_messages = [
            # parse each messages into a json
            json.loads(self.redis_client.lindex(meeting_chat_key, msg_position))
            for msg_position in user_messages_positions
        ]

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