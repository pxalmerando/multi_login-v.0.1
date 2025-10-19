"""Authentication API endpoints."""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from app.models.models import UserCreate, AuthToken
from app.config import ERROR_INVALID_CREDENTIALS, AUTH_HEADER_NAME
from app.users.service import user_service
from app.auth.service import auth_service


router = APIRouter()


@router.post("/registration", response_model=AuthToken)
def register_user(user: UserCreate):
    """Register a new user and return authentication token."""
    user_in_db = user_service.create_user(user)
    return auth_service.create_auth_response(user_in_db)


@router.post("/login", response_model=AuthToken)
def login_user(form_data: OAuth2PasswordRequestForm = Depends()):
    """Authenticate user and return access token."""
    user = auth_service.authenticate_user(
        email=form_data.username,
        password=form_data.password
    )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ERROR_INVALID_CREDENTIALS,
            headers=AUTH_HEADER_NAME,
        )
    
    return auth_service.create_auth_response(user)