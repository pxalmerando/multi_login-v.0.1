from typing import List, Tuple
from app.services.multi_login_service import MultiLoginService
import asyncio


class ProfileAllocationService:

    def __init__(
            self,
            multi_login_service: MultiLoginService
    ):
        self.multi_login_service = multi_login_service
        
    async def pair_urls_with_profile(
            self,
            urls: List[str],
            max_profiles: int
    ) -> List[Tuple[str, str]]:
        
        await self.multi_login_service.initialize()
        folder_id = await self.multi_login_service.get_folder_id()
        profile_ids = await self.multi_login_service.profile_manager.get_profile_ids(folder_id=folder_id)

        if not profile_ids:
            raise ValueError("No profiles available for allocation")
        
        if max_profiles <= 0:
            raise ValueError("max_profiles must be greater than 0")
        
        profile_ids_to_use = profile_ids[:max_profiles]
        print(f"Using profile IDs: {profile_ids_to_use}")

        results = []

        for index, url in enumerate(urls):
            profile_id = profile_ids_to_use[index % len(profile_ids_to_use)]
            results.append((url, profile_id))

        return results

    
