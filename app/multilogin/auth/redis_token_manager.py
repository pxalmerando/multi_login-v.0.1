import logging
from typing import Optional
import redis.asyncio as redis

from app.multilogin.auth.auth_service import UserAuth
from app.multilogin.auth.token_repository import TokenRepository
from app.multilogin.auth.token_serializer import TokenSerializer
from app.multilogin.auth.token_service import TokenService
from app.multilogin.auth.token_validator import TokenValidator


logger = logging.getLogger(__name__)

class RedisTokenManager:
    """
    High-level manager for authentication tokens stored in Redis.

    Wraps TokenService and provides:
        - token retrieval (cached or fresh)
        - token validation
        - token persistence
    """

    def __init__(self, user_auth: UserAuth, redis_client: redis.Redis, prefix="auth:tokens"):
        serializer = TokenSerializer()
        validator = TokenValidator()
        repository = TokenRepository(redis_client, serializer, prefix)
        self.service = TokenService(repository, validator, user_auth)
        logger.info(f"[RedisTokenManager] Initialized with prefix {prefix}")

    async def get_tokens(self) -> dict:
        """
        Get valid tokens. Will load from Redis if valid, else re-authenticate.
        """
        return await self.service.get_tokens()

    async def load_tokens(self) -> Optional[dict]:
        """
        Load cached tokens only if they are valid. Does NOT authenticate.
        """
        return await self.service.get_cached_tokens_if_valid()

    async def save(self, tokens: dict) -> None:
        """
        Save tokens to Redis. Raises on failure.
        """
        await self.service.repository.save(tokens)