"""Authentication service for business logic."""
from typing import Optional
from datetime import timedelta
from app.models.models import User, UserInDB, AuthToken
from app.security import Security
from app.config import ACCESS_TOKEN_EXPIRE_MINUTES
from app.users.repository import user_repository


class AuthService:
    """Handles authentication-related business logic."""
    
    def __init__(self, repository):
        self.repository = repository
    
    def authenticate_user(self, email: str, password: str) -> Optional[UserInDB]:
        """Authenticate a user with email and password."""
        user = self.repository.get_by_email(email)
        if not user:
            return None
        if not Security.verify_password(password, user.hashed_password):
            return None
        return user
    
    def create_auth_response(self, user: UserInDB) -> AuthToken:
        """Create an authentication response with access token."""
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = Security.create_access_token(
            data={"sub": user.email},
            expires_delta=access_token_expires
        )
        
        user_data = User(
            email=user.email,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name,
        )
        
        return AuthToken(
            access_token=access_token,
            token_type="bearer",
            user=user_data,
        )


# Singleton instance
auth_service = AuthService(user_repository)