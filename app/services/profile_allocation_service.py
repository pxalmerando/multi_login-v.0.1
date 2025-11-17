import asyncio
from typing import List, Set, Optional
from app.services.multi_login_service import MultiLoginService
import logging

logger = logging.getLogger(__name__)
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

    
    async def _get_validated_profile(self, folder_id) -> List[str]:
        if not self._profile_pool:
            logger.info(f"[ProfileAllocator] Cache empty, fetching profiles from API")
            self._profile_pool = await self._get_valid_profiles(folder_id)
        else:
            logger.info(f"[ProfileAllocator] Using cached profiles ({len(self._profile_pool)} profiles)")
        return self._profile_pool

    async def acquire_profile(self, folder_id: str, timeout: float = 30.0) -> Optional[str]:
        start = asyncio.get_event_loop().time()
        while True:
            elapsed = asyncio.get_event_loop().time() - start

            if elapsed > timeout:
                logger.info(f"[ProfileAllocator] TIMEOUT after {elapsed:.1f}s")
                logger.info(f"[ProfileAllocator] Pool status: {self.get_pool_status()}")
                logger.info(f"[ProfileAllocator] In use: {self._in_use_profiles}")
                logger.info(f"[ProfileAllocator] Locks: {[(k, v.locked()) for k, v in self._profile_locks.items()]}")
                return None
            
            async with self._pool_lock:
                valid_profiles = await self._get_validated_profile(folder_id)
                valid_profiles = [p for p in valid_profiles if p not in self._deleted_profiles]
                self._profile_pool = valid_profiles

                for p in valid_profiles:
                    if p not in self._profile_locks:
                        self._profile_locks[p] = asyncio.Lock()
                
                for pid in valid_profiles:
                    if pid in self._in_use_profiles:
                        continue

                    lock = self._profile_locks[pid]
                    try:
                        if await asyncio.wait_for(lock.acquire(), timeout=.1):
                            self._in_use_profiles.add(pid)
                            logger.info(f"[ProfileAllocator] Acquired profile {pid}")
                            return pid
                    except asyncio.TimeoutError:
                        continue
                    except Exception as e:
                        logger.exception(f"Error acquiring profile {e}")
                    
                if len(valid_profiles) < self.max_profiles:
                    logger.info(f"[ProfileAllocator] Creating new ML profile "
                          f"({len(valid_profiles)}/{self.max_profiles})")
                    new_pid = await self._create_single_profile(folder_id, len(valid_profiles))

                    if new_pid:
                        self._profile_pool.append(new_pid)
                        self._profile_locks[new_pid] = asyncio.Lock()
                        await self._profile_locks[new_pid].acquire()
                        self._in_use_profiles.add(new_pid)
                        logger.info(f"[ProfileAllocator] Created new profile {new_pid}")
                        return new_pid
                    logger.info("[ProfileAllocator] ML create profile failed, retrying...")
                    
            await asyncio.sleep(0.4)

    async def release_profile(self, profile_id: str):

        if profile_id is None:
            logger.error(f"[ProfileAllocator] Attempted to release None Profile!")
            return
        
        async with self._pool_lock:

            if profile_id in self._in_use_profiles:
                self._in_use_profiles.remove(profile_id)

            lock = self._profile_locks.get(profile_id)

            if lock and lock.locked():
                try: 
                    lock.release()
                except RuntimeError as e:
                    logger.exception(f"[ProfileAllocator] Warning: Failed to release lock for {profile_id}: {e}")

            logger.info(f"[ProfileAllocator] Released profile {profile_id} "
                  f"(in use: {len(self._in_use_profiles)}/{self.max_profiles})")
            
    async def mark_profile_deleted(self, profile_id: str):

        if profile_id is None:
            logger.error(f"[ProfileAllocator] Warning: Attempted to delete None profile")
            return
        
        async with self._pool_lock:

            self._in_use_profiles.discard(profile_id)
            self._profile_pool = [p for p in self._profile_pool if p != profile_id]
            self._deleted_profiles.add(profile_id)

            lock = self._profile_locks.pop(profile_id, None)
            if lock and lock.locked():
                try: lock.release()
                except RuntimeError: pass

        try:
            await self.multi_login_service.delete_profile(profile_id)
            logger.info(f"[ProfileAllocator] Deleted ML profile {profile_id}")
        except Exception as e:
            logger.exception(f"[ProfileAllocator] Error stopping deleted profile {profile_id}: {e}")

    async def _create_single_profile(self, folder_id: str, idx: int) -> Optional[str]:
        try:
            resp = await self.multi_login_service.profile_manager.create_profile(
                folder_id=folder_id, name=f"Profile {idx}"
            )
            data = resp.get("data")
            if data is None:
                return None
            if not isinstance(data, dict):
                return None
            ids = data.get("ids", [])
            if not ids:
                return None
            profile_id = ids[0]
            if profile_id:
                print(f"[ProfileAllocator] Created profile {profile_id}")
                return profile_id
            
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
