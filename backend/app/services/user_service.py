from app.db.database import get_database
from app.services.meeting_service import MeetingService

class UserService:
    def __init__(self):
        self.db = get_database()

    def create_user(self, email, name, age, gender):
        """Create a new user"""

        # check if given attributes are valid
        errors = self.get_attribute_errors(email, name, age, gender)
        if errors:
            # invalid attributes
            return {"error": ". ".join(errors)}

        # check if email already exists
        user = self.get_user(email)
        if user:
            # email already exists
            return {"error": f"Email '{email}' already exists"}

        # create the user
        self.db.add_user(email, name, age, gender)

    def get_attribute_errors(self, email, name, age, gender):
        """Collect and return all error messages of the given user inputs"""
        errors_messages = []

        if not isinstance(email, str) or not email.strip():
            errors_messages.append("Please provide a valid email")

        if not isinstance(name, str) or not name.strip():
            errors_messages.append("Please provide a valid name")

        if not isinstance(age, int) or age <= 0:
            errors_messages.append("Please provide a valid age")

        if not isinstance(gender, str) or not gender.strip():
            errors_messages.append("Please provide a valid gender")

        return errors_messages

    def get_user(self, email):
        """Get user details by email"""
        return self.db.get_user(email)

    def delete_user(self, email):
        """Delete a user and all meetings created by them"""

        # Check if user exists
        user = self.get_user(email)
        if not user:
            return None

        # Get all meetings created by this user
        user_meetings = self.db.get_meetings_by_user(email)
        meeting_service = MeetingService()

        # Delete each meeting
        if user_meetings:
            for meeting in user_meetings:
                meeting_id = meeting.get('meeting_id')
                if meeting_id:
                    # Delete the meeting
                    meeting_service.delete_meeting(meeting_id)

        # Delete the user
        result = self.db.delete_user(email)

        if isinstance(result, dict) and "error" in result:
            return result  # Return error message

        return result  # Return True for success or None for not found