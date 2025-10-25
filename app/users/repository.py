"""User repository for database operations."""
from typing import Optional, Dict
from app.models.models import UserInDB


class UserRepository:
    """Handles all user database operations."""
    
    def __init__(self):
        self._db: Dict[str, dict] = {}
    
    def get_by_email(self, email: str) -> Optional[UserInDB]:
        """Retrieve a user by email."""
        if email in self._db:
            user_dict = self._db[email]
            return UserInDB(**user_dict)
        return None
    
    def email_exists(self, email: str) -> bool:
        """Check if an email is already registered."""
        return any(user["email"] == email for user in self._db.values())
    
    def create(self, user: UserInDB) -> UserInDB:
        """Create a new user in the database."""
        self._db[user.email] = user.model_dump()
        return user
    
    def get_all(self) -> Dict[str, dict]:
        """Get all users (for compatibility with existing code)."""
        return self._db


# Singleton instance
user_repository = UserRepository()