import asyncio
import logging
import time
from typing import Optional

from app.database.profile_repository import ProfileRepository
from app.services.profile_state_manager import ProfileStateManager

logger = logging.getLogger(__name__)


class ProfileAllocationService:
    """
    Coordinates profile allocation with thread-safe locking.
    Only reason to change: Concurrency control strategy changes.
    """
    
    def __init__(
        self, 
        repository: ProfileRepository,
        state_manager: ProfileStateManager,
        max_profiles: int = 10
    ):
        self.repository = repository
        self.state = state_manager
        self.max_profiles = max_profiles
        self._cache_refresh_lock = asyncio.Lock()
        self._profile_creation_lock = asyncio.Lock()
        
        # New: Track if initial fetch has been performed
        self._cache_profiles: list | None = None
        self._initial_fetch_done: bool = False
        self._initial_fetch_lock = asyncio.Lock()

    async def _ensure_initial_fetch(self, folder_id: str) -> list | None:
        """
        Ensure fetch_all_profiles is called only once across all workers.
        Subsequent calls return cached result.
        
        Uses double-check locking pattern for thread safety.
        """
        # Fast path: already fetched
        if self._initial_fetch_done:
            logger.debug("Using cached profiles (already fetched)")
            return self._cache_profiles
        
        async with self._initial_fetch_lock:
            # Double-check after acquiring lock
            if self._initial_fetch_done:
                logger.debug("Using cached profiles (fetched by another worker)")
                return self._cache_profiles
            
            logger.info("Performing initial fetch of all profiles (first call)")
            self._cache_profiles = await self.repository.fetch_all_profiles(folder_id)
            self._initial_fetch_done = True
            
            profile_count = len(self._cache_profiles) if self._cache_profiles else 0
            logger.info(f"Initial fetch complete: {profile_count} profiles cached")
            
            return self._cache_profiles

    def has_fetched_profiles(self) -> bool:
        """
        Check if profiles have already been fetched.
        
        Returns:
            bool: True if fetch_all_profiles has been called, False otherwise.
        """
        return self._initial_fetch_done

    def get_cached_profiles(self) -> list | None:
        """
        Get the cached profiles without triggering a fetch.
        
        Returns:
            list | None: Cached profiles or None if not yet fetched.
        """
        return self._cache_profiles

    def reset_cache(self) -> None:
        """
        Reset the cache to allow a fresh fetch.
        Useful for testing or manual cache invalidation.
        """
        self._cache_profiles = None
        self._initial_fetch_done = False
        logger.info("Profile cache has been reset")

    async def acquire_profile(self, folder_id: str, timeout: float = 30.0) -> Optional[str]:
        start = time.monotonic()
        attempt = 0
        
        while True:
            attempt += 1
            elapsed = time.monotonic() - start
            
            if elapsed > timeout:
                status = await self.state.get_status()
                logger.warning(f"TIMEOUT after {elapsed:.1f}s. Status: {status}")
                return None
            
            # Refresh cache if empty - uses cached result if already fetched
            async with self._cache_refresh_lock:
                available = await self.state.get_available_profiles()
                if not available:
                    # This will only call API once, subsequent calls use cache
                    profiles = await self._ensure_initial_fetch(folder_id)
                    if profiles:
                        await self.state.update_cache(profiles)
                    available = await self.state.get_available_profiles()
            
            # Try to acquire an existing profile
            for profile_id in available:
                if await self.state.try_acquire(profile_id):
                    logger.info(f"Acquired existing profile {profile_id}")
                    return profile_id
            
            # Check if we can create a new profile
            async with self._profile_creation_lock:
                current_total = await self.state.get_total_count()
                
                if current_total < self.max_profiles:
                    logger.info(f"Creating new profile ({current_total}/{self.max_profiles})")
                    
                    name = f"profile-{int(time.time() * 1000)}"
                    new_profile_id = await self.repository.create_profile(
                        folder_id=folder_id, 
                        name=name
                    )
                    
                    if new_profile_id:
                        added = await self.state.add_profile_if_under_limit(
                            new_profile_id, 
                            self.max_profiles
                        )
                        if added:
                            if await self.state.try_acquire(new_profile_id):
                                logger.info(f"Created and acquired {new_profile_id}")
                                return new_profile_id
                        else:
                            logger.warning(f"Max limit reached, cleaning up {new_profile_id}")
                            try:
                                await self.repository.delete_profile(new_profile_id)
                            except Exception as e:
                                logger.error(f"Failed to cleanup profile: {e}")
                else:
                    logger.debug(f"At max capacity ({current_total}/{self.max_profiles})")

            await asyncio.sleep(0.5)
    
    async def release_profile(self, profile_id: str):
        """Release a profile back to the pool."""
        if profile_id is None:
            logger.error("[ProfileAllocator] Attempted to release None profile!")
            return
        
        success = await self.state.release(profile_id)
        if success:
            logger.info(f"[Allocator] Released {profile_id}")
        else:
            logger.debug(f"[Allocator] Release no-op for {profile_id} (wasn't in-use)")

    async def delete_profile(self, profile_id: str):
        """Permanently delete a profile."""
        if profile_id is None:
            logger.error("[ProfileAllocator] Attempted to delete None profile")
            return
        
        success = await self.state.mark_deleted(profile_id)
        if success:
            logger.info(f"[Allocator] Marked {profile_id} as deleted")
            try:
                await self.repository.delete_profile(profile_id)
                logger.info(f"[Allocator] Deleted {profile_id} from API")
            except Exception as e:
                logger.error(f"[Allocator] Failed to delete {profile_id} from API: {e}")
        else:
            logger.debug(f"[Allocator] Delete no-op for {profile_id} (already deleted)")
    
    async def get_pool_status(self) -> dict:
        """Get current pool status."""
        status = await self.state.get_status()
        status['cache_initialized'] = self._initial_fetch_done
        return status