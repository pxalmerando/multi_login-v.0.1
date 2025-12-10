from typing import Optional
from decouple import config
import redis.asyncio as redis
from app.multilogin.exceptions import MultiLoginServiceError
from app.utils.http_client import HttpClient
from app.multilogin.auth.auth_service import UserAuth
from app.multilogin.auth.redis_token_manager import RedisTokenManager


class MultiLoginAuthService:
    """
    Responsible for MultiLogin API authentication and token management.
    
    Note: This is different from app.services.auth_service.AuthService
    which handles FastAPI user authentication.
    """
    
    def __init__(
            self, 
            base_url: str, 
            http_client: HttpClient,
            token_manager: Optional[RedisTokenManager] = None
        ):

        self.base_url = base_url
        self.http_client = http_client
        self.email = str(config("EMAIL"))
        self.password = str(config("PASSWORD"))
        if token_manager:
            self.token_manager = token_manager
        else:
            self.token_manager = self._create_token_manager()
    
    def _create_token_manager(
            self,
        ) -> RedisTokenManager:
        """Create a token manager with the given credentials"""
        
        user_auth = UserAuth(
            base_url=self.base_url,
            email=self.email,
            password=self.password,
            http_client=self.http_client
        )
        
        redis_client = redis.from_url("redis://127.0.0.1:6379", decode_responses=True)
        return RedisTokenManager(user_auth, redis_client)
    
    async def get_access_token(self) -> str:
        """Get authentication token"""
        try:
            results = await self.token_manager.get_tokens()
            access_token = results.get("access_token")
            if not access_token:
                raise MultiLoginServiceError("Unable to obtain access token")
            return access_token
        except Exception as e:
            raise MultiLoginServiceError(f"Authentication failed: {e}")