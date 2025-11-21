import logging
from typing import List
import redis.asyncio as redis

from app.services.redis_key_manager import RedisKeyManager
from app.services.redis_profile_operation import RedisProfileOperations
from app.services.redis_profile_reporter import RedisProfileStatusReporter
from app.services.redis_script_manager import RedisScriptManager

logger = logging.getLogger(__name__)

class RedisProfileStorage:

    def __init__(self, url: str = "redis://127.0.0.1:6379", prefix: str = "profiles"):
        self.client = redis.from_url(url=url, decode_responses=True)
        
        self.key_manager = RedisKeyManager(prefix=prefix)
        self.script_manager = RedisScriptManager(self.client)
        self.operations = RedisProfileOperations(self.script_manager, self.key_manager)
        self.reporter = RedisProfileStatusReporter(self.client, self.key_manager)

    async def initialize(self):
        await self.client.ping()
        await self.script_manager.register_scripts()
        logger.info("[RedisStorage] Initialized.")

    async def try_acquire_profile(self, profile_id: str) -> bool:
        return await self.operations.try_acquire_profile(profile_id=profile_id)
    
    async def release_profile(self, profile_id) -> bool:
        return await self.operations.release_profile(profile_id=profile_id)
    
    async def mark_deleted(self, profile_id) -> bool:
        return await self.operations.mark_deleted(profile_id=profile_id)
    
    async def add_profile(self, profile_id) -> bool:
        return await self.operations.add_profile(profile_id=profile_id)
    
    async def replace_all_profiles(self, profiles: List[str]) -> None:
        return await self.operations.replace_all_profiles(profiles=profiles)
    
    async def get_available_profiles(self) -> List[str]:
        return await self.reporter.get_available_profiles()
    
    async def get_status(self) -> dict:
        return await self.reporter.get_status()