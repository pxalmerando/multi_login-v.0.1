
from typing import List, Set
import logging

logger = logging.getLogger(__name__)

class ProfileStateManager:
    """
    Manages the state of profiles: cached pool, in-use, deleted.
    Only reason to change: State management strategy changes.
    """
    
    def __init__(self):
        self._profile_pool: List[str] = []
        self._deleted_profiles: Set[str] = set()
        self._in_use_profiles: Set[str] = set()
        self._cache_dirty = True  
    
    def get_cached_profiles(self) -> List[str]:
        """Get currently cached profile IDs."""
        return self._profile_pool.copy()
    
    def update_cache(self, profiles: List[str]):
        """Update the cached profile pool."""
        self._profile_pool = profiles
        self._cache_dirty = False
        logger.info(f"[StateManager] Cache updated with {len(profiles)} profiles")
    
    def get_available_profiles(self) -> List[str]:
        """Get profiles that are not in use and not deleted."""
        return [
            p for p in self._profile_pool 
            if p not in self._in_use_profiles 
            and p not in self._deleted_profiles
        ]
    
    def mark_in_use(self, profile_id: str):
        """Mark a profile as currently in use."""
        self._in_use_profiles.add(profile_id)
        logger.debug(f"[StateManager] Profile {profile_id} marked in-use")
    
    def mark_available(self, profile_id: str):
        """Mark a profile as available (not in use)."""
        self._in_use_profiles.discard(profile_id)
        logger.debug(f"[StateManager] Profile {profile_id} marked available")
    
    def mark_deleted(self, profile_id: str):
        """Mark a profile as deleted (permanently unusable)."""
        self._in_use_profiles.discard(profile_id)
        self._profile_pool = [p for p in self._profile_pool if p != profile_id]
        self._deleted_profiles.add(profile_id)
        logger.info(f"[StateManager] Profile {profile_id} marked deleted")
    
    def add_to_pool(self, profile_id: str):
        """Add a newly created profile to the pool."""
        if profile_id not in self._profile_pool:
            self._profile_pool.append(profile_id)
            logger.debug(f"[StateManager] Profile {profile_id} added to pool")
    
    def is_cache_dirty(self) -> bool:
        """Check if cache needs refreshing."""
        return self._cache_dirty or len(self._profile_pool) == 0
    
    def get_status(self) -> dict:
        """Get current state statistics."""
        return {
            "total_profiles": len(self._profile_pool),
            "in_use": len(self._in_use_profiles),
            "available": len(self.get_available_profiles()),
            "deleted": len(self._deleted_profiles),
            "profiles": self._profile_pool,
        }