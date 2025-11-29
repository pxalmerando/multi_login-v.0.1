from pydantic import BaseModel
from app.models.schemas.user_schema import UserBase

class AuthToken(BaseModel):
    access_token: str
    token_type: str
    user: UserBase