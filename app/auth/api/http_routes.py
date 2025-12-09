"""Authentication API endpoints."""
from app.auth.schemas import AuthToken
from app.auth.schemas import UserCreate
from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from app.auth.exceptions import InvalidCredentialsError
from app.auth.services.user_service import user_service
from app.auth.services.auth_services import auth_service
from app.core.config import ERROR_INVALID_CREDENTIALS, AUTH_HEADER_NAME


router = APIRouter(
    prefix="/auth",
    tags=["authentication"],
)


@router.post("/register", response_model=AuthToken)
def register_user(user: UserCreate):
    """
    Register a new user and immediately authenticate them.

    Flow:
    - Validate input as UserCreate (email, password, optional profile fields)
    - Create user in the database via user_service.create_user
    - Issue an access token and return AuthToken with user info
    
    """
    user_in_db = user_service.create_user(user)
    return auth_service.create_auth_response(user_in_db)


@router.post("/login", response_model=AuthToken)
def login_user(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Authenticate a user via OAuth2 password flow.

    Flow:
    - Validate credentials using AuthService.authenticate_user
    - On success, return AuthToken with access_token and basic user info
    - On failure, return HTTP 401 with a generic error
    
    """
    user = auth_service.authenticate_user(
        email=form_data.username,
        password=form_data.password
    )
    
    if user is None:
        raise InvalidCredentialsError(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ERROR_INVALID_CREDENTIALS,
            headers=AUTH_HEADER_NAME,
        )
    
    return auth_service.create_auth_response(user)