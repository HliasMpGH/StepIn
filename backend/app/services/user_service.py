from app.db.database import get_database

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