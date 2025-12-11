"""User service for business logic."""
from app.security.hashing import AuthSecurity
from app.auth.repository import user_repository
from app.auth.schemas import UserCreate, UserInDB
from app.security.password_policy import validate_password_strength
from app.auth.exceptions import EmailAlreadyRegisteredError
from app.core.config import STATUS_BAD_REQUEST, ERROR_EMAIL_REGISTERED

class UserService:
    def __init__(self, repository):
        self.repository = repository
        self.security = AuthSecurity()

    def create_user(self, user_data: UserCreate) -> UserInDB:
        """Create a new user with validation."""

        validate_password_strength(user_data.password)
        
        if self.repository.email_exist(user_data.email):
            raise EmailAlreadyRegisteredError(
                status_code=STATUS_BAD_REQUEST,
                detail=ERROR_EMAIL_REGISTERED
            )
        
        hashed_password = self.security.hash_password(user_data.password)
        user_in_db = UserInDB(
            email=user_data.email,
            username=user_data.username,
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            hashed_password=hashed_password,
        )
        
        return self.repository.create_user(user_in_db)


user_service = UserService(user_repository)