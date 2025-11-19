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
        
        
        self._pool_lock = asyncio.Lock()
        self._profile_locks: dict[str, asyncio.Lock] = {}
    
    async def acquire_profile(self, folder_id: str, timeout: float = 30.0) -> Optional[str]:
        """
        Acquire an available profile or create a new one if needed.
        Returns profile_id or None if timeout.
        """
        start = asyncio.get_event_loop().time()
        
        while True:
            elapsed = asyncio.get_event_loop().time() - start
            
            if elapsed > timeout:
                logger.warning(f"[Allocator] TIMEOUT after {elapsed:.1f}s")
                logger.info(f"[Allocator] Status: {self.state.get_status()}")
                return None
            
            async with self._pool_lock:
                
                if self.state.is_cache_dirty():
                    profiles = await self.repository.fetch_all_profiles(folder_id)
                    self.state.update_cache(profiles)
                
                
                for p in self.state.get_cached_profiles():
                    if p not in self._profile_locks:
                        self._profile_locks[p] = asyncio.Lock()
                
                
                available = self.state.get_available_profiles()
                
                for pid in available:
                    lock = self._profile_locks[pid]
                    if not lock.locked():
                        await lock.acquire()
                        self.state.mark_in_use(pid)
                        logger.info(f"[Allocator] Acquired existing profile {pid}")
                        return pid
                
                
                current_count = len(self.state.get_cached_profiles())
                if current_count < self.max_profiles:
                    logger.info(f"[Allocator] Creating new profile ({current_count}/{self.max_profiles})")
                    new_pid = await self.repository.create_profile(
                        folder_id=folder_id,
                        name=f"Profile {current_count}"
                    )
                    
                    if new_pid:
                        self.state.add_to_pool(new_pid)
                        self._profile_locks[new_pid] = asyncio.Lock()
                        await self._profile_locks[new_pid].acquire()
                        self.state.mark_in_use(new_pid)
                        logger.info(f"[Allocator] Created and acquired profile {new_pid}")
                        return new_pid
                    
                    logger.warning("[Allocator] Profile creation failed, retrying...")
            
            await asyncio.sleep(0.4)
    
    async def release_profile(self, profile_id: str):
        """Release a profile back to the pool."""
        if profile_id is None:
            logger.error("[Allocator] Attempted to release None profile!")
            return
        
        async with self._pool_lock:
            self.state.mark_available(profile_id)
            
            lock = self._profile_locks.get(profile_id)
            if lock and lock.locked():
                try:
                    lock.release()
                    logger.info(f"[Allocator] Released profile {profile_id}")
                except RuntimeError as e:
                    logger.exception(f"[Allocator] Failed to release lock for {profile_id}: {e}")
    
    async def delete_profile(self, profile_id: str):
        """Permanently delete a profile."""
        if profile_id is None:
            logger.error("[Allocator] Attempted to delete None profile")
            return
        
        async with self._pool_lock:
            self.state.mark_deleted(profile_id)
            
            
            lock = self._profile_locks.pop(profile_id, None)
            if lock and lock.locked():
                try:
                    lock.release()
                except RuntimeError:
                    pass
        
        
        await self.repository.delete_profile(profile_id)
    
    def get_pool_status(self) -> dict:
        """Get current pool status."""
        return self.state.get_status()