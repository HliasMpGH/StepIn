from app.db.database import get_database
from app.services.redis_service import get_redis_manager
from app.core.constants import LEAVE_MEETING

class UserService:
    def __init__(self):
        self.db = get_database()
        self.redis_mgr = get_redis_manager()

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
        """Delete a user"""

        # delete user from cache
        user_joined_meeting = self.redis_mgr.delete_user(email)

        # if user was on a meeting, log a leave action
        if user_joined_meeting:
            self.db.log_action(email, user_joined_meeting, LEAVE_MEETING)

        # delete user from db
        result = self.db.delete_user(email)

        if isinstance(result, dict) and "error" in result:
            return result  # Return error message

        return result  # Return True for success or None for not found