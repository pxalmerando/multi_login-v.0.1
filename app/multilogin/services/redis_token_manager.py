import logging
from .auth_service import UserAuth
from typing import Optional
import redis.asyncio as redis
from .token_service import TokenService
from .token_validator import TokenValidator
from .token_repository import TokenRepository
from .token_serializer import TokenSerializer


logger = logging.getLogger(__name__)

class RedisTokenManager:

    def __init__(self, user_auth: UserAuth, redis_client: redis.Redis, prefix="auth:tokens"):
        serializer = TokenSerializer()
        validator = TokenValidator()
        repository = TokenRepository(redis_client, serializer, prefix)
        self.service = TokenService(repository, validator, user_auth)


    async def get_tokens(self) -> dict:
        return await self.service.get_tokens()
    
    async def load_tokens(self) -> Optional[dict]:
        return await self.service.get_cached_tokens_if_valid()
    
    async def save(self, tokens: dict) -> None:

        return await self.service.repository.save(tokens)