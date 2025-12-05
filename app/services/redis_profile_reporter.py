from typing import Dict, List
import redis.asyncio as redis

from app.services.redis_key_manager import RedisKeyManager


class RedisProfileStatusReporter:
    
    def __init__(self, client: redis.Redis, key_manager: RedisKeyManager):
        self.client = client
        self.keys = key_manager

    async def get_available_profiles(self) -> List[str]:
        """Get list of profiles that are available (not in use, not deleted)"""
        members = await self.client.sdiff([
            self.keys.pool_key,
            self.keys.in_use_key,
            self.keys.deleted_key
        ]) # type: ignore
        return list(members)
    
    async def get_pool_count(self) -> int:
        """Get total count of profiles in the pool (single Redis call)"""
        return await self.client.scard(self.keys.pool_key) # type: ignore
    
    async def get_status(self) -> Dict:
        """Get comprehensive status of the profile pool"""
        async with self.client.pipeline(transaction=False) as pipe:
            pipe.scard(self.keys.pool_key)
            pipe.scard(self.keys.in_use_key)
            pipe.scard(self.keys.deleted_key)
            pipe.sdiff([
                self.keys.pool_key,
                self.keys.in_use_key,
                self.keys.deleted_key
            ])
            total, in_use, deleted, available = await pipe.execute()
        
        return {
            "total_profiles": total,
            "in_use": in_use,
            "deleted": deleted,
            "available": len(available),
        }
    
    async def is_pool_exhausted(self) -> bool:
        """Check if all profiles are in use or deleted"""
        available = await self.get_available_profiles()
        return len(available) == 0