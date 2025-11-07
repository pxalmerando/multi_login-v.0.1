import asyncio
from typing import List, Set, Optional
from app.services.multi_login_service import MultiLoginService

class ProfileAllocationService:
    """
    Profile allocation with locking to prevent race conditions.
    Ensures profiles can't be used by multiple tasks simultaneously.
    """

    def __init__(
        self, 
        multi_login_service: MultiLoginService,
    ):
        self.multi_login_service = multi_login_service
        self._profile_creation_lock = asyncio.Lock()
        self._profile_pool: List[str] = []
        self._deleted_profiles: Set[str] = set()
        self._in_use_profiles: Set[str] = set()
        self._profile_locks: dict = {}

    async def acquire_profile(
        self,
        folder_id: str,
        max_profiles: int,
        timeout: float = 30.0
    ) -> Optional[str]:
        """
        Acquire an available profile for exclusive use.
        Waits if all profiles are in use.
        
        Args:
            folder_id: The folder to get/create profiles in
            max_profiles: Maximum number of profiles to maintain
            timeout: How long to wait for an available profile
            
        Returns:
            A profile_id locked for exclusive use, or None if timeout
        """
        start_time = asyncio.get_event_loop().time()
        
        while True:
            if asyncio.get_event_loop().time() - start_time > timeout:
                print(f"Timeout waiting for available profile after {timeout}s")
                return None
            
            async with self._profile_creation_lock:
                await self._refresh_profile_pool(folder_id, max_profiles)
                
                available_profiles = [
                    p for p in self._profile_pool 
                    if p not in self._in_use_profiles 
                    and p not in self._deleted_profiles
                ]
                
                if available_profiles:
                    profile_id = available_profiles[0]
                    self._in_use_profiles.add(profile_id)
                    print(f"Acquired profile {profile_id} (in use: {len(self._in_use_profiles)}/{len(self._profile_pool)})")
                    return profile_id
                
                if len(self._profile_pool) < max_profiles:
                    print(f"All profiles in use, creating additional profile...")
                    new_profile = await self._create_single_profile(folder_id)
                    if new_profile:
                        self._profile_pool.append(new_profile)
                        self._in_use_profiles.add(new_profile)
                        print(f"Acquired new profile {new_profile}")
                        return new_profile
            
            print(f"All {max_profiles} profiles in use, waiting...")
            await asyncio.sleep(0.5)

    async def release_profile(self, profile_id: str):
        """
        Release a profile back to the pool for reuse.
        Call this after you're done using the profile.
        """
        async with self._profile_creation_lock:
            if profile_id in self._in_use_profiles:
                self._in_use_profiles.remove(profile_id)
                print(f"Released profile {profile_id} (in use: {len(self._in_use_profiles)}/{len(self._profile_pool)})")

    async def mark_profile_deleted(self, profile_id: str):
        """
        Mark a profile as deleted so it won't be reused.
        Automatically releases it from in-use set.
        """
        async with self._profile_creation_lock:
            self._deleted_profiles.add(profile_id)
            
            
            if profile_id in self._in_use_profiles:
                self._in_use_profiles.remove(profile_id)
            
            
            if profile_id in self._profile_pool:
                self._profile_pool.remove(profile_id)
                print(f"Removed deleted profile {profile_id} from pool")

    async def _refresh_profile_pool(self, folder_id: str, max_profiles: int):
        
        valid_profiles = await self._get_valid_profiles(folder_id)
        
        
        valid_profiles = [p for p in valid_profiles if p not in self._deleted_profiles]
        
        
        if len(valid_profiles) < max_profiles:
            needed = max_profiles - len(valid_profiles)
            print(f"Creating {needed} additional profiles...")
            
            for i in range(needed):
                new_profile = await self._create_single_profile(folder_id=folder_id, name=i)
                if new_profile:
                    valid_profiles.append(new_profile)
        
        
        self._profile_pool = valid_profiles[:max_profiles]

    async def _create_single_profile(self, folder_id: str, name: str) -> Optional[str]:
        
        try:
            profile_id = await self.multi_login_service.profile_manager.create_profile(
                folder_id=folder_id,
                name=f"Profile {name}"
            )
            profile_id = profile_id.get('data', {}).get('ids', [])[0]
            print(f"Created profile: {profile_id}")
            return profile_id
        except Exception as e:
            print(f"Failed to create profile: {e}")
            return None

    async def _get_valid_profiles(self, folder_id: str) -> List[str]:
        
        try:
            profile_ids = await self.multi_login_service.profile_manager.get_profile_ids(
                folder_id=folder_id
            )
            return profile_ids
        except Exception as e:
            print(f"Error getting valid profiles: {e}")
            return []

    def get_pool_status(self) -> dict:
        
        return {
            "total_profiles": len(self._profile_pool),
            "in_use": len(self._in_use_profiles),
            "available": len(self._profile_pool) - len(self._in_use_profiles),
            "deleted": len(self._deleted_profiles),
            "profiles": self._profile_pool,
        }