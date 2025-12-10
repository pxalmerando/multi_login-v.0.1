

from typing import Optional
import redis.asyncio as redis
import logging
from app.services.multilogin.token_serializer import TokenSerializer

logger = logging.getLogger(__name__)

class TokenRepository:

    def __init__(self, redis_client: redis.Redis, serializer: TokenSerializer, prefix: str = "auth:tokens"):
        self.redis_client = redis_client
        self.serializer = serializer
        self.prefix = prefix

    def _make_key(self) -> str:

        return f"{self.prefix}"
    
    async def load(self) -> Optional[dict]:
        key = self._make_key()

        try:
            raw_data = await self.redis_client.get(key)
            logger.debug(f"[TokenRepository] Retrieved data from Redis key!")
        except redis.RedisError as e:
            logger.exception(f"[TokenRepository] Redis error during GET operation: {e}")
        except Exception as e:
            logger.exception(f"[TokenRepository] Unexpected error during Redis GET")
            return None

        tokens = self.serializer.deserialize(raw_data)
        
        if tokens is None:
            logger.warning(f"[TokenRepository] No valid tokens found")
        else:
            logger.info(f"[TokenRepository] Successfully loaded tokens from cache")

        return tokens
    
    async def save(self, tokens: dict) -> None:

        key = self._make_key()

        try:
            serialized_tokens = self.serializer.serialize(tokens)
        except Exception as e:
            logger.exception(f"[TokenRepository] Failed to serialize tokens: {e}") 
            raise

        try:
            await self.redis_client.set(key, serialized_tokens)
            logger.info(
                f"[TokenRepository] Successfully saved tokens to Redis key"
            )
        except redis.RedisError as e:
            logger.error(
                f"[TokenRepository] Redis error during SET operation: {e}"
            )
            raise
        
        except Exception as e:
            logger.exception(
                f"[TokenRepository] Unexpected error during Redis SET"
            )
            raise
    
    async def delete(self) -> bool:
        key = self._make_key()
        
        try:
            result = await self.redis_client.delete(key)
            
            if result > 0:
                logger.info(
                    f"[TokenRepository] Deleted tokens from Redis key"
                )
                return True
            else:
                logger.debug(
                    f"[TokenRepository] No tokens to delete at key"
                )
                return False
                
        except redis.RedisError as e:
            logger.error(
                f"[TokenRepository] Redis error during DELETE operation: {e}"
            )
            return False
            
        except Exception as e:
            logger.exception(
                f"[TokenRepository] Unexpected error during Redis DELETE"
            )
            return False
        
    async def exists(self) -> bool:
        key = self._make_key()
        
        try:
            result = await self.redis_client.exists(key)
            return result > 0
            
        except Exception as e:
            logger.exception(
                f"[TokenRepository] Error checking if key exists {e}"
            )
            return False