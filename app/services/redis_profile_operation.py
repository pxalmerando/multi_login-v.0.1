

from typing import List, Optional, Tuple
from app.services.redis_key_manager import RedisKeyManager
from app.services.redis_script_manager import RedisScriptManager
import logging

logger = logging.getLogger(__name__)

class RedisProfileOperations:
    def __init__(
        self,
        script_manager: RedisScriptManager,
        key_manager: RedisKeyManager
    ):
        
        self.scripts = script_manager
        self.keys = key_manager

    async def try_acquire_profile(self, profile_id: str) -> bool:
        result = await self.scripts.execute_script(
            'acquire',
            3, 
            self.keys.pool_key,
            self.keys.in_use_key,
            self.keys.deleted_key,
            profile_id
        )

        if result == 1:
            logger.info(f"Acquired profile: {profile_id}")
        else:
            logger.warning(f"Failed to acquire profile: {profile_id}")

        return result == 1

    async def release_profile(self, profile_id: str) -> bool:
        """
        Release a profile back to the pool.
        
        Returns:
            True if released successfully, False if not in use
        """
        result = await self.scripts.execute_script(
            'release',
            1,
            self.keys.in_use_key,
            profile_id
        )
        
        if result == 1:
            logger.info(f"Released profile: {profile_id}")
        
        return result == 1
    
    async def mark_deleted(self, profile_id: str) -> bool:
        """
        Mark a profile as deleted (removes from pool and in_use, adds to deleted).
        
        Returns:
            True if marked deleted, False if already deleted
        """
        result = await self.scripts.execute_script(
            'delete',
            3,
            self.keys.pool_key,
            self.keys.in_use_key,
            self.keys.deleted_key,
            profile_id
        )
        
        if result == 1:
            logger.info(f"Marked profile as deleted: {profile_id}")
        
        return result == 1
    
    async def add_profile(self, profile_id: str) -> bool:
        """
        Add a new profile to the pool.
        
        Returns:
            True if added, False if already exists or is deleted
        """

        result = await self.scripts.execute_script(
            'add',
            2,
            self.keys.pool_key,
            self.keys.deleted_key,
            profile_id
        )

        if result == 1:
            logger.info(f"Added profile: {profile_id}")
        return result == 1
    async def add_profile_if_under_limit(self, profile_id: str, max_limit: int) -> bool:
        """Atomically add profile only if total count is under limit."""
        result = await self.scripts.execute_script(
            'add_if_under_limit', 
            2,  # num_keys = 2 (pool_key, deleted_key)
            self.keys.pool_key, 
            self.keys.deleted_key,
            profile_id, 
            str(max_limit)  # Convert to string for Redis
        )
        return bool(result)
        
    async def replace_all_profiles(self, profiles: List[str]) -> int:
        """
        Replace entire profile pool with new list.
        
        Returns:
            Number of profiles actually added (excludes deleted ones)
        """

        if not profiles:
            await self.scripts.client.delete(self.keys.pool_key)
            logger.info("Cleared all profiles")
            return 0

        result = await self.scripts.execute_script(
            'replace',
            2,
            self.keys.pool_key,
            self.keys.deleted_key,
            *profiles
        )

        logger.info(f"Replaced profiles, added {result} profiles")
        return int(result)
    
    