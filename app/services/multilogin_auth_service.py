import logging
from decouple import config
import redis.asyncio as redis
from app.services.multilogin.auth_service import UserAuth
from app.services.multilogin.redis_token_manager import RedisTokenManager
from app.services.multilogin.exceptions import MultiLoginServiceError

logger = logging.getLogger(__name__)


class MultiLoginAuthService:
    """
    Responsible for MultiLogin API authentication and token management.
    
    Note: This is different from app.services.auth_service.AuthService
    which handles FastAPI user authentication.
    """
    
    def __init__(self, email: str = None, password: str = None, 
                 base_url: str = None, http_client = None,
                 token_manager: RedisTokenManager = None):
        
        if token_manager:
            self.token_manager = token_manager
        else:
            self.token_manager = self._create_token_manager(
                email, password, base_url, http_client
            )
    
    def _create_token_manager(self, email: str, password: str, 
                            base_url: str, http_client) -> RedisTokenManager:
        """Create a token manager with the given credentials"""
        email = email or config("EMAIL")
        password = password or config("PASSWORD")
        
        user_auth = UserAuth(
            email=email,
            password=password,
            base_url=base_url,
            http_client=http_client
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