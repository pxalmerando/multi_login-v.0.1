"""User service for business logic."""
from fastapi import HTTPException
from app.models.schemas.user_schema import UserCreate, UserInDB
from app.security import Security
from app.validators import validate_password_strength
from app.core.config import STATUS_BAD_REQUEST, ERROR_EMAIL_REGISTERED
from app.database.repository import user_repository


class UserService:
    def __init__(self, repository):
        self.repository = repository
    
    def create_user(self, user_data: UserCreate) -> UserInDB:
        """Create a new user with validation."""
        validate_password_strength(user_data.password)
        
        if self.repository.email_exist(user_data.email):
            raise HTTPException(
                status_code=STATUS_BAD_REQUEST,
                detail=ERROR_EMAIL_REGISTERED
            )
        
        hashed_password = Security.hash_password(user_data.password)
        user_in_db = UserInDB(
            email=user_data.email,
            username=user_data.username,
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            hashed_password=hashed_password,
        )
        
        return self.repository.create_user(user_in_db)


user_service = UserService(user_repository)