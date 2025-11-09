import asyncio
from typing import Dict, Optional, List
from app.models.schemas.profile_models import MultiLoginProfileSession
class ProfileRegistry:
    def __init__(self):
        self._sessions: Dict[str, MultiLoginProfileSession] = {}
        self._lock = asyncio.Lock()
    async def register(self, session: MultiLoginProfileSession) -> None:
        async with self._lock:
            if session.profile_id in self._sessions:
                raise ValueError(f"Profile {session.profile_id} already registered")
            self._sessions[session.profile_id] = session
            print(f"Profile {session.profile_id} registered")
    async def unregister(self, profile_id: str) -> None:
        async with self._lock:
            if profile_id in self._sessions:
                    del self._sessions[profile_id]
                    print(f"Profile {profile_id} unregistered")
        
    async def get_session(self, profile_id: str) -> Optional[MultiLoginProfileSession]:
        async with self._lock:
            return self._sessions.get(profile_id)
    
    async def is_running(self, profile_id: str) -> bool:
        async with self._lock:
            return profile_id in self._sessions
    
    def get_all_sessions(self) -> List[MultiLoginProfileSession]:
        return list(self._sessions.values())
    
    def clear(self):
        self._sessions.clear()
    def count(self) -> int:
        return len(self._sessions)
