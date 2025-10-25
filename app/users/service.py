"""User service for business logic."""
from fastapi import HTTPException
from app.models.models import UserCreate, UserInDB
from app.security import Security
from app.validators import validate_password_strength
from app.config import STATUS_BAD_REQUEST, ERROR_EMAIL_REGISTERED
from app.users.repository import user_repository


class UserService:
    """Handles user-related business logic."""
    
    def __init__(self, repository):
        self.repository = repository
    
    def create_user(self, user_data: UserCreate) -> UserInDB:
        """Create a new user with validation."""
        # Validate password strength
        validate_password_strength(user_data.password)
        
        # Check if user exists
        if self.repository.email_exists(user_data.email):
            raise HTTPException(
                status_code=STATUS_BAD_REQUEST,
                detail=ERROR_EMAIL_REGISTERED
            )
        
        # Hash password and create user
        hashed_password = Security.hash_password(user_data.password)
        user_in_db = UserInDB(
            email=user_data.email,
            username=user_data.username,
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            hashed_password=hashed_password,
        )
        
        return self.repository.create(user_in_db)


# Singleton instance
user_service = UserService(user_repository)