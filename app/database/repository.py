"""Database repository for user management operations."""
from typing import Optional, Dict
from app.models.schemas.user_schema import UserInDB


class UserRepository:
    """Repository for managing user data in memory."""

    def __init__(self):
        """Initialize the user repository with an empty user database."""
        self.user_db: Dict[str, dict] = {}

    def get_user_by_email(self, email: str) -> Optional[dict]:
        """Retrieve a user by their email address.

        Args:
            email (str): The email address of the user.

        Returns:
            Optional[UserInDB]: The user object if found, None otherwise.
        """
        if email in self.user_db:
            user_dict = self.user_db[email]
            return UserInDB(**user_dict)
        return None


    def create_user(self, user: UserInDB) -> UserInDB:
        """Create a new user in the repository.

        Args:
            user (UserInDB): The user object to create.

        Returns:
            UserInDB: The created user object.
        """
        self.user_db[user.email] = user.model_dump()
        return user

    def email_exist(self, email: str) -> bool:
        """Check if a user with the given email exists.

        Args:
            email (str): The email address to check.

        Returns:
            bool: True if the email exists, False otherwise.
        """
        return email in self.user_db

    def get_all_users(self) -> Dict[str, dict]:
        """Retrieve all users in the repository.

        Returns:
            Dict[str, dict]: A dictionary of all users keyed by email.
        """
        return self.user_db
    
user_repository = UserRepository()