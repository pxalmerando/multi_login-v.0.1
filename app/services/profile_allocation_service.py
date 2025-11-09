import asyncio
from typing import List, Set, Optional
from app.services.multi_login_service import MultiLoginService
class ProfileAllocationService:
    """
    Allocates MultiLogin profiles safely in concurrent environments.
    Ensures profiles cannot be acquired by multiple tasks at once.
    """
    def __init__(self, multi_login_service: MultiLoginService, max_profiles: int = 10):
        self.multi_login_service = multi_login_service
        self.max_profiles = max_profiles  

        self._pool_lock = asyncio.Lock()
        self._profile_pool: List[str] = []
        self._deleted_profiles: Set[str] = set()
        self._in_use_profiles: Set[str] = set()
        self._profile_locks: dict[str, asyncio.Lock] = {}
    async def acquire_profile(self, folder_id: str, timeout: float = 30.0) -> Optional[str]:
        start = asyncio.get_event_loop().time()
        while True:
            if asyncio.get_event_loop().time() - start > timeout:
                print(f"[ProfileAllocator] Timeout waiting for profile")
                return None
            async with self._pool_lock:
                

                valid_profiles = await self._get_valid_profiles(folder_id)
                valid_profiles = [p for p in valid_profiles if p not in self._deleted_profiles]
                self._profile_pool = valid_profiles
                for p in valid_profiles:
                    if p not in self._profile_locks:
                        self._profile_locks[p] = asyncio.Lock()
                

                available = [p for p in valid_profiles if p not in self._in_use_profiles]
                

                for pid in available:
                    lock = self._profile_locks[pid]
                    if not lock.locked():
                        await lock.acquire()
                        self._in_use_profiles.add(pid)
                        print(f"[ProfileAllocator] Reusing profile {pid}")
                        return pid
                

                if len(valid_profiles) < self.max_profiles:
                    print(f"[ProfileAllocator] Creating new ML profile "
                          f"({len(valid_profiles)}/{self.max_profiles})")
                    new_pid = await self._create_single_profile(folder_id, len(valid_profiles))
                    if new_pid:
                        self._profile_pool.append(new_pid)
                        self._profile_locks[new_pid] = asyncio.Lock()
                        await self._profile_locks[new_pid].acquire()
                        self._in_use_profiles.add(new_pid)
                        print(f"[ProfileAllocator] Created new profile {new_pid}")
                        return new_pid
                    print("[ProfileAllocator] ML create profile failed, retrying...")
            await asyncio.sleep(0.4)
    async def release_profile(self, profile_id: str):
        async with self._pool_lock:
            if profile_id in self._in_use_profiles:
                self._in_use_profiles.remove(profile_id)
            lock = self._profile_locks.get(profile_id)
            if lock and lock.locked():
                try: lock.release()
                except RuntimeError: pass
            print(f"[ProfileAllocator] Released profile {profile_id} "
                  f"(in use: {len(self._in_use_profiles)}/{self.max_profiles})")
    async def mark_profile_deleted(self, profile_id: str):
        async with self._pool_lock:
            self._in_use_profiles.discard(profile_id)
            self._profile_pool = [p for p in self._profile_pool if p != profile_id]
            self._deleted_profiles.add(profile_id)
            lock = self._profile_locks.pop(profile_id, None)
            if lock and lock.locked():
                try: lock.release()
                except RuntimeError: pass
        try:
            await self.multi_login_service.stop_profile(profile_id)
            print(f"[ProfileAllocator] Deleted ML profile {profile_id}")
        except Exception as e:
            print(f"[ProfileAllocator] Error stopping deleted profile {profile_id}: {e}")
    async def _create_single_profile(self, folder_id: str, idx: int) -> Optional[str]:
        try:
            resp = await self.multi_login_service.profile_manager.create_profile(
                folder_id=folder_id, name=f"Profile {idx}"
            )
            pid = resp.get("data", {}).get("ids", [None])[0]
            if pid:
                print(f"[ProfileAllocator] Created profile {pid}")
                return pid
        except Exception as e:
            print(f"[ProfileAllocator] Creation error: {e}")
        return None
    async def _get_valid_profiles(self, folder_id: str) -> List[str]:
        try:
            return await self.multi_login_service.profile_manager.get_profile_ids(folder_id=folder_id)
        except Exception as e:
            print(f"[ProfileAllocator] Fetch error: {e}")
            return []
    def get_pool_status(self) -> dict:
        return {
            "total_profiles": len(self._profile_pool),
            "in_use": len(self._in_use_profiles),
            "available": len(self._profile_pool) - len(self._in_use_profiles),
            "deleted": len(self._deleted_profiles),
            "profiles": self._profile_pool,
        }
