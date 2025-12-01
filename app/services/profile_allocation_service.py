import asyncio
import logging
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
    
    async def acquire_profile(self, folder_id: str, timeout: float = 30.0) -> Optional[str]:
        """
        Acquire an available profile or create a new one if needed.
        Returns profile_id or None if timeout.
        """
        start = asyncio.get_event_loop().time()
        attempt = 0
        
        while True:
            attempt += 1
            elapsed = asyncio.get_event_loop().time() - start
            
            if elapsed > timeout:
                status = await self.state.get_status()
                logger.warning(f"[ProfileAllocator] TIMEOUT after {elapsed:.1f}s ({attempt} attempts) Status: {status}")
                return None
            
            profiles = await self.state.get_cached_profiles()
            if len(profiles) == 0:
                logger.info(f"[ProfileAllocator] Cache is empty, fetching from API...")
                fresh_profiles = await self.repository.fetch_all_profiles(folder_id)
                await self.state.update_cache(fresh_profiles)
                logger.info(f"[ProfileAllocator] Fetched {len(fresh_profiles)} profiles from API")
            
            available = await self.state.get_available_profiles()

            if available:
                for profile_id in available:
                    success = await self.state.try_acquire(profile_id)

                    if success:
                        logger.info(f"[Allocator] ✓ Acquired existing profile {profile_id}")
                        return profile_id
                    else:
                        logger.debug(f"[Allocator] Profile {profile_id} taken, trying next...")

                logger.debug("[Allocator] All available profiles were acquired by others")
            
            current_count = len(await self.state.get_cached_profiles())

            if current_count < self.max_profiles:
                logger.info(f"[Allocator] Creating new profile ({current_count}/{self.max_profiles})...")

                new_profile_id = await self.repository.create_profile(folder_id=folder_id, name=f"{current_count + 1}" )

                if new_profile_id:
                    
                    added = await self.state.add_profile(new_profile_id)

                    if added:

                        success = await self.state.try_acquire(new_profile_id)

                        if success:
                            logger.info(
                                f"[Allocator] ✓ Created and acquired {new_profile_id} (attempt {attempt}, {elapsed:.1f}s elapsed)"
                            )

                            return new_profile_id
                        else:
                            logger.debug(f"[Allocator] Created {new_profile_id} but another server acquired it")
                    else:
                        logger.debug(f"[Allocator] Profile {new_profile_id} already exists")
                    
                else:
                    logger.warning("[Allocator] Profile creation failed")
            else:
                logger.debug(
                    f"[Allocator] At max capacity ({current_count}/{self.max_profiles}), waiting for release..."
                )

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
        return await self.state.get_status()