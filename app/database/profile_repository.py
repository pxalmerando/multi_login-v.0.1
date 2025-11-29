
import logging
from typing import Optional, List
from app.services.multi_login_service import MultiLoginService

logger = logging.getLogger(__name__)

class ProfileRepository:
    """
    Handles all communication with the MultiLogin API.
    Only reason to change: API contract changes.
    """
    
    def __init__(self, multi_login_service: MultiLoginService):
        self.multi_login_service = multi_login_service
    
    async def create_profile(self, folder_id: str, name: str) -> Optional[str]:
        """Create a single profile and return its ID."""
        try:
            resp = await self.multi_login_service.profile_manager.create_profile(
                folder_id=folder_id, 
                name=name
            )
            data = resp.get("data")
            if data is None or not isinstance(data, dict):
                return None
                
            ids = data.get("ids", [])
            if not ids:
                return None
                
            profile_id = ids[0]
            logger.info(f"[ProfileRepository] Created profile {profile_id}")
            return profile_id
            
        except Exception as e:
            logger.exception(f"[ProfileRepository] Creation error: {e}")
            return None
    
    async def fetch_all_profiles(self, folder_id: str) -> List[str]:
        """Fetch all profile IDs from the API."""
        try:
            profiles = await self.multi_login_service.profile_manager.get_profile_ids(
                folder_id=folder_id
            )
            logger.info(f"[ProfileRepository] Fetched {len(profiles)} profiles")
            return profiles
        except Exception as e:
            logger.exception(f"[ProfileRepository] Fetch error: {e}")
            return []
    
    async def delete_profile(self, profile_id: str) -> bool:
        """Delete a profile from the API."""
        try:
            await self.multi_login_service.delete_profile(profile_id)
            logger.info(f"[ProfileRepository] Deleted profile {profile_id}")
            return True
        except Exception as e:
            logger.exception(f"[ProfileRepository] Delete error for {profile_id}: {e}")
            return False