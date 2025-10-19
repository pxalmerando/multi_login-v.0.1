"""Dependency injection functions for FastAPI."""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from app.models.models import UserInDB
from app.config import (
    SECRET_KEY,
    ALGORITHM,
    ERROR_CANNOT_VALIDATE,
    ERROR_INACTIVE_USER,
    AUTH_HEADER_NAME
)
from app.users.repository import user_repository


token_scheme = HTTPBearer()


def _raise_credential_exception() -> None:
    """Raise a credential validation exception."""
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=ERROR_CANNOT_VALIDATE,
        headers=AUTH_HEADER_NAME,
    )


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(token_scheme)
) -> UserInDB:
    """Extract and validate the current user from JWT token."""
    token = credentials.credentials
    
    try:
        payload = jwt.decode(
            token=token,
            key=SECRET_KEY,
            algorithms=[ALGORITHM]
        )
        email: str = payload.get("sub")
        if email is None:
            _raise_credential_exception()
    except JWTError:
        _raise_credential_exception()
    
    user = user_repository.get_by_email(email)
    if user is None:
        _raise_credential_exception()
    
    return user


def get_current_active_user(
    current_user: UserInDB = Depends(get_current_user)
) -> UserInDB:
    """Ensure the current user is active (not disabled)."""
    if current_user.disabled:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=ERROR_INACTIVE_USER
        )
    return current_user