
import logging
from typing import Optional

from app.multilogin.application.profile_allocation_service import ProfileAllocationService

logger = logging.getLogger(__name__)

class ProfileLifecycleManager:
    """
    Manages profile lifecycle decisions based on processing results.
    Encapsulates the logic of when to reuse vs. delete profiles.
    """
    
    def __init__(self, profile_allocator: ProfileAllocationService):
        self.profile_allocator = profile_allocator
    
    async def acquire_profile(self, folder_id: str) -> Optional[str]:
        """Acquire a profile from the pool."""
        try:
            profile_id = await self.profile_allocator.acquire_profile(folder_id)
            if profile_id:
                logger.info(f"[LifecycleManager] Acquired profile {profile_id}")
            return profile_id
        except Exception as e:
            logger.exception(f"[LifecycleManager] Failed to acquire profile: {e}")
            return None
    
    async def handle_success(self, profile_id: str):
        """Handle profile after successful processing - release back to pool."""
        try:
            await self.profile_allocator.release_profile(profile_id)
            logger.info(f"[LifecycleManager] Released profile {profile_id} after success")
        except Exception as e:
            logger.exception(f"[LifecycleManager] Failed to release {profile_id}: {e}")
    
    async def handle_failure(self, profile_id: str, reason: str):
        """Handle profile after failure - delete it (might be compromised)."""
        try:
            await self.profile_allocator.delete_profile(profile_id)
            logger.warning(f"[LifecycleManager] Deleted profile {profile_id} due to: {reason}")
        except Exception as e:
            logger.exception(f"[LifecycleManager] Failed to delete {profile_id}: {e}")
    
    async def cleanup_on_error(self, profile_id: Optional[str]):
        """Emergency cleanup when exception occurs."""
        if profile_id:
            try:
                await self.profile_allocator.delete_profile(profile_id)
                logger.info(f"[LifecycleManager] Emergency cleanup of profile {profile_id}")
            except Exception as e:
                logger.exception(f"[LifecycleManager] Emergency cleanup failed: {e}")