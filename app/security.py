from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import jwt
from passlib.context import CryptContext

from decouple import config

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class Security:
    def verify_password(plain_password, hashed_password) -> bool:
        return pwd_context.verify(plain_password, hashed_password)

    def hash_password(password) -> str:
        return pwd_context.hash(password)

    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
        to_encode = data.copy()
        if expires_delta:
            expires = datetime.now(timezone.utc) + expires_delta
        else:
            expires = datetime.now(timezone.utc) + timedelta(minutes=config("ACCESS_TOKEN_EXPIRE_MINUTES", cast=float))
        to_encode.update({"exp": expires})
        encoded_jwt = jwt.encode(to_encode, config("SECRET_KEY"), algorithm=config("ALGORITHM"))
        return encoded_jwt
