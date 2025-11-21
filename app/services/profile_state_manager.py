import logging
from typing import List

logger = logging.getLogger(__name__)


class ProfileStateManager:

    def __init__(self, storage):
        """
        Args:
            storage: Any object implementing ProfileStorage protocol
                     (InMemoryProfileStorage, RedisProfileStorage, etc.)
        """
        self._storage = storage
        logger.info("[StateManager] Initialized with atomic storage")
    
    async def get_cached_profiles(self) -> List[str]:
        """
        Get all profile IDs.
        
        Note: We removed the "cache dirty" concept because the storage
        layer is now the source of truth.
        """
        return await self._storage.get_available_profiles()
    
    async def get_available_profiles(self) -> List[str]:
        """Get profiles that are not in use and not deleted."""
        return await self._storage.get_available_profiles()
    
    async def get_status(self) -> dict:
        """Get current state statistics."""
        return await self._storage.get_status()
    
    async def try_acquire(self, profile_id: str) -> bool:
        """
        Try to acquire a profile atomically.
        
        Returns:
            True if acquired, False if unavailable
        """
        success = await self._storage.try_acquire_profile(profile_id)
        if success:
            logger.info(f"[StateManager] ✓ Acquired {profile_id}")
        else:
            logger.debug(f"[StateManager] ✗ Failed to acquire {profile_id}")
        return success
    
    async def release(self, profile_id: str) -> bool:
        """
        Release a profile back to the available pool.
        
        Returns:
            True if released, False if wasn't in-use
        """
        success = await self._storage.release_profile(profile_id)
        if success:
            logger.info(f"[StateManager] Released {profile_id}")
        return success
    
    async def mark_deleted(self, profile_id: str) -> bool:
        """
        Mark a profile as permanently deleted.
        
        Returns:
            True if deleted, False if already deleted
        """
        success = await self._storage.mark_deleted(profile_id)
        if success:
            logger.info(f"[StateManager] Deleted {profile_id}")
        return success
    
    async def add_profile(self, profile_id: str) -> bool:
        """
        Add a new profile to the pool.
        
        Returns:
            True if added, False if already exists
        """
        success = await self._storage.add_profile(profile_id)
        if success:
            logger.info(f"[StateManager] Added {profile_id}")
        return success
    
    async def update_cache(self, profiles: List[str]):
        """
        Replace the entire profile pool with a fresh list.
        
        Used when refreshing from the API.
        """
        await self._storage.replace_all_profiles(profiles)
        logger.info(f"[StateManager] Updated cache with {len(profiles)} profiles")

