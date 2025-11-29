import asyncio
from typing import List, Set
import logging

logger = logging.getLogger(__name__)

class InMemoryProfileStorage:

    def __init__(self):
        
        self._profile_pool: Set[str] = set()
        self._in_use_profiles: Set[str] = set()
        self._deleted_profiles: Set[str] = set()
        
        
        
        self._lock = asyncio.Lock()
        
        logger.info("[InMemoryStorage] Initialized")

    async def get_all_profiles(self) -> List[str]:
        """Get all profile IDs (excluding deleted)."""
        async with self._lock:
            return list(self._profile_pool)
        
    async def get_available_profiles(self) -> List[str]:
        """Get profiles that are available (not in-use, not deleted)."""
        async with self._lock:
            available = self._profile_pool - self._in_use_profiles - self._deleted_profiles
            return list(available)
    
    async def get_status(self) -> dict:
        """Get statistics about the profile pool."""
        async with self._lock:
            available = self._profile_pool - self._in_use_profiles - self._deleted_profiles
            
            return {
                "total_profiles": len(self._profile_pool),
                "in_use": len(self._in_use_profiles),
                "available": len(available),
                "deleted": len(self._deleted_profiles),
            }
    
    async def try_acquire_profile(self, profile_id: str) -> bool:
        """
        ATOMICALLY check if profile is available and mark it in-use.
        
        This is THE critical operation for distributed systems.
        
        Returns:
            True  = Successfully acquired (you now own it)
            False = Failed (already in-use, deleted, or doesn't exist)
        """
        async with self._lock:  
            
            if profile_id not in self._profile_pool:
                logger.debug(f"[Storage] Acquire failed: {profile_id} not in pool")
                return False
            
            if profile_id in self._deleted_profiles:
                logger.debug(f"[Storage] Acquire failed: {profile_id} is deleted")
                return False
            
            if profile_id in self._in_use_profiles:
                logger.debug(f"[Storage] Acquire failed: {profile_id} already in-use")
                return False
            
            
            self._in_use_profiles.add(profile_id)
            logger.info(f"[Storage] ✓ Acquired {profile_id}")
            return True
    
    async def release_profile(self, profile_id: str) -> bool:
        """
        ATOMICALLY mark a profile as available (not in-use).
        
        Idempotent: Safe to call multiple times.
        
        Returns:
            True  = Successfully released
            False = Wasn't in-use (already released or never acquired)
        """
        async with self._lock:  
            if profile_id in self._in_use_profiles:
                self._in_use_profiles.remove(profile_id)
                logger.info(f"[Storage] ✓ Released {profile_id}")
                return True
            else:
                logger.debug(f"[Storage] Release no-op: {profile_id} wasn't in-use")
                return False
    
    async def mark_deleted(self, profile_id: str) -> bool:
        """
        ATOMICALLY mark a profile as permanently deleted.
        
        Multi-step operation:
        1. Remove from in-use (if applicable)
        2. Remove from pool
        3. Add to deleted set
        
        All three steps happen atomically or not at all.
        
        Returns:
            True  = Successfully deleted
            False = Already deleted (idempotent)
        """
        async with self._lock:  
            
            if profile_id in self._deleted_profiles:
                logger.debug(f"[Storage] Delete no-op: {profile_id} already deleted")
                return False
            
            
            self._in_use_profiles.discard(profile_id)
            
            
            self._profile_pool.discard(profile_id)
            
            
            self._deleted_profiles.add(profile_id)
            
            logger.info(f"[Storage] ✓ Deleted {profile_id}")
            return True
        
    async def add_profile(self, profile_id: str) -> bool:
        """
        ATOMICALLY add a new profile to the pool if it doesn't exist.
        
        Prevents duplicate profiles when multiple servers try to
        create profiles simultaneously.
        
        Returns:
            True  = Successfully added new profile
            False = Profile already exists (idempotent)
        """
        async with self._lock:  
            
            if profile_id in self._profile_pool or profile_id in self._deleted_profiles:
                logger.debug(f"[Storage] Add no-op: {profile_id} already exists")
                return False
            
            self._profile_pool.add(profile_id)
            logger.info(f"[Storage] ✓ Added {profile_id}")
            return True

    async def replace_all_profiles(self, profiles: List[str]) -> None:
        """
        ATOMICALLY replace the entire profile pool.
        
        Used when refreshing from the API - replaces the entire
        list in one operation.
        
        Note: Doesn't affect in-use or deleted status.
        """
        async with self._lock:  
            self._profile_pool = set(profiles)
            logger.info(f"[Storage] ✓ Replaced pool with {len(profiles)} profiles")
