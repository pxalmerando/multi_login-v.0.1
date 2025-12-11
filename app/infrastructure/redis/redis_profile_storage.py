import logging
from typing import List, Optional
import redis.asyncio as redis

from app.infrastructure.redis.redis_key_manager import RedisKeyManager
from app.infrastructure.redis.redis_profile_operation import RedisProfileOperations
from app.infrastructure.redis.redis_profile_reporter import RedisProfileStatusReporter
from app.infrastructure.redis.redis_script_manager import RedisScriptManager

logger = logging.getLogger(__name__)

class RedisProfileStorage:

    def __init__(self, url: str = "redis://127.0.0.1:6379", prefix: str = "profiles"):
        self.client = redis.from_url(url=url, decode_responses=True)
        
        self.key_manager = RedisKeyManager(prefix=prefix)
        self.script_manager = RedisScriptManager(self.client)
        self.operations = RedisProfileOperations(self.script_manager, self.key_manager)
        self.reporter = RedisProfileStatusReporter(self.client, self.key_manager)

    async def initialize(self):
        await self.client.ping()  # type: ignore
        await self.script_manager.register_scripts()
        logger.info("[RedisStorage] Initialized.")
    
    async def close(self) -> None:
        logger.info(f"[RedisProfileStorage] Close Redis")
        await self.client.close()

    async def flush(self) -> None:
        logger.info(f"[RedisProfileStorage] Flush redis")
        await self.client.flushdb()
    
    async def release_profile(self, profile_id) -> bool:
        return await self.operations.release_profile(profile_id=profile_id)
    
    async def mark_deleted(self, profile_id) -> bool:
        return await self.operations.mark_deleted(profile_id=profile_id)
    
    async def replace_all_profiles(self, profiles: List[str]) -> int:
        return await self.operations.replace_all_profiles(profiles=profiles)
    
    async def get_available_profiles(self) -> List[str]:
        return await self.reporter.get_available_profiles()
    
    async def get_status(self) -> dict:
        return await self.reporter.get_status()
    
    async def get_pool_count(self) -> int:
        """Get total count of profiles in pool"""
        return await self.reporter.get_pool_count()

    async def add_profile_if_under_limit(self, profile_id: str, max_limit: int) -> bool:
        """Add profile only if under limit (atomic check-and-add)."""
        return await self.operations.add_profile_if_under_limit(profile_id, max_limit)
    
    async def acquire_any_available(self) -> Optional[str]:
        return await self.operations.acquire_any_available()