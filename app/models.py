from pydantic import BaseModel, EmailStr
from typing import Optional

class TokenData(BaseModel):
    username: Optional[str] = None

class User(BaseModel):
    email: EmailStr
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    disabled: Optional[bool] = False

class AuthToken(BaseModel):
    access_token: str
    token_type: str
    user: User

class UserInDB(User):
    hashed_password: str

class UserCreate(BaseModel):
    email: EmailStr        
    password: str          
    username: Optional[str] = None     
    first_name: Optional[str] = None   
    last_name: Optional[str] = None

class URLProcessRequest(BaseModel):
    url: str

class URLProcessResponse(BaseModel):
    success: Optional[bool] = True
    submitted_url: str
    result: dict
    processed_at: str
    processed_by: str