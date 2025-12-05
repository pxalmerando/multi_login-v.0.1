import logging
from typing import List

logger = logging.getLogger(__name__)


class ProfileStateManager:

    def __init__(self, storage):
        self._storage = storage
        logger.info("[StateManager] Initialized with atomic storage")
    
    async def get_available_profiles(self) -> List[str]:
        """Get profiles that are available for acquisition."""
        return await self._storage.get_available_profiles()
    
    async def get_status(self) -> dict:
        """Get current state statistics."""
        return await self._storage.get_status()
    
    async def get_total_count(self) -> int:
        """Get total number of profiles in pool."""
        count = await self._storage.get_pool_count()
        return count if count is not None else 0
    
    async def try_acquire(self, profile_id: str) -> bool:
        success = await self._storage.try_acquire_profile(profile_id)
        if success:
            logger.info(f"[StateManager] ✓ Acquired {profile_id}")
        else:
            logger.debug(f"[StateManager] ✗ Failed to acquire {profile_id}")
        return success
    
    async def release(self, profile_id: str) -> bool:
        success = await self._storage.release_profile(profile_id)
        if success:
            logger.info(f"[StateManager] Released {profile_id}")
        return success
    
    async def mark_deleted(self, profile_id: str) -> bool:
        success = await self._storage.mark_deleted(profile_id)
        if success:
            logger.info(f"[StateManager] Deleted {profile_id}")
        return success
    
    async def add_profile(self, profile_id: str) -> bool:
        success = await self._storage.add_profile(profile_id)
        if success:
            logger.info(f"[StateManager] Added {profile_id}")
        return success
    
    async def update_cache(self, profiles: List[str]):
        await self._storage.replace_all_profiles(profiles)
        logger.info(f"[StateManager] Updated cache with {len(profiles)} profiles")
    
    async def add_profile_if_under_limit(self, profile_id: str, max_limit: int) -> bool:
        """Add profile only if total count is under limit (atomic)."""
        success = await self._storage.add_profile_if_under_limit(profile_id, max_limit)
        if success:
            logger.info(f"[StateManager] Added {profile_id} (under limit)")
        else:
            logger.warning(f"[StateManager] Cannot add {profile_id} (at/over limit)")
        return success  # <-- Return the boolean from storage
