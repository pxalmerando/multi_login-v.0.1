from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm, HTTPBearer, HTTPAuthorizationCredentials
from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
from typing import Optional
from app.security import Security
from decouple import config
from app.validators import validate_password_strength
from app.models import (
    User,
    UserCreate,
    UserInDB,
    AuthToken,
    URLProcessResponse,
    URLProcessRequest
)

STATUS_BAD_REQUEST = 400
ERROR_INVALID_CREDENTIALS = "Incorrect username or password"
AUTH_HEADER_NAME = {"WWW-Authenticate": "Bearer"}
ERROR_EMAIL_REGISTERED = "Email already registered"
ERROR_USERNAME_REGISTERED = "Username already registered"
ERROR_CANNOT_VALIDATE = "Could not validate credentials"
ERROR_INACTIVE_USER = "Inactive user"
app = FastAPI()
token_scheme = HTTPBearer()
user_db = {}
def get_user(db, email: str) -> Optional[UserInDB]:
    if email in db:
        user_dict = db[email]
        return UserInDB(**user_dict)
    return None
def _raise_credential_exception() -> None:
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=ERROR_CANNOT_VALIDATE,
        headers=AUTH_HEADER_NAME,
    )
def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(token_scheme)):
    token = credentials.credentials
    try:
        payload = jwt.decode(token=token, key=config("SECRET_KEY"), algorithms=[config("ALGORITHM")])
        email: str = payload.get("sub")
        if email is None:
            raise _raise_credential_exception
    except JWTError:
        raise _raise_credential_exception
    
    user = get_user(user_db, email=email)
    if user is None:
        raise _raise_credential_exception
    return user
def get_current_active_user(current_user: User = Depends(get_current_user)) -> UserInDB:
    if current_user.disabled:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=ERROR_INACTIVE_USER)
    return current_user
def authenticate_user(db, email: str, password: str) -> Optional[UserInDB]:
    user = get_user(db, email)
    if not user:
        return None
    if not Security.verify_password(password, user.hashed_password):
        return None
    return user
def _create_auth_response(user: UserInDB) -> AuthToken:
    access_token_expires = timedelta(minutes=config("ACCESS_TOKEN_EXPIRE_MINUTES", cast=float))
    access_token = Security.create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    user = User(
        email=user.email,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name,
    )
    return AuthToken(
        access_token=access_token,
        token_type="bearer",
        user=user,
    )
def _check_user_exists(email: str) -> None:
    for db_user in user_db.values():
        if db_user["email"] == email:
            raise HTTPException(
                status_code=STATUS_BAD_REQUEST, 
                detail=ERROR_EMAIL_REGISTERED
            )

@app.post("/registration", response_model=AuthToken)
def create_user(user: UserCreate):
    validate_password_strength(user.password)
    _check_user_exists(user.email)
    hashed_password = Security.hash_password(user.password)
    db_key = user.email
    user_in_db = UserInDB(
        email=user.email,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name,
        hashed_password=hashed_password,
    )
    user_db[db_key] = user_in_db.model_dump()
    return _create_auth_response(user_in_db) 
@app.post("/login", response_model=AuthToken)
def login_user(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(
        db=user_db, 
        email=form_data.username, 
        password=form_data.password
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ERROR_INVALID_CREDENTIALS,
            headers=AUTH_HEADER_NAME,
        )
    return _create_auth_response(user)
    
@app.post("/process_url", response_model=URLProcessResponse)
def process_url(url: URLProcessRequest, user: User = Depends(get_current_active_user)):
    return URLProcessResponse(
        success=True,
        submitted_url=url.url,
        result={"status": "success"},
        processed_at=datetime.now(timezone.utc).isoformat(),
        processed_by=user.email,
    )