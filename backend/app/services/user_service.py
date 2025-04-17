from app.db.database import get_database

class UserService:
    def __init__(self):
        self.db = get_database()

    def create_user(self, email, name, age, gender):
        """Create a new user"""
        return self.db.add_user(email, name, age, gender)

    def get_user(self, email):
        """Get user details by email"""
        return self.db.get_user(email)