import asyncio
from typing import List, Tuple
from app.services.multi_login_service import MultiLoginService

class ProfileAllocationService:

    def __init__(
            self, 
            multi_login_service: MultiLoginService,
        ):
        self.multi_login_service = multi_login_service
        self._profile_creation_lock = asyncio.Lock()

        
    async def pair_urls_with_profile(
            self,
            urls: List[str],
            max_profiles: int,
    ) -> List[Tuple[str, str]]:
        
        if max_profiles <= 0:
            raise ValueError("max_profiles must be greater than 0")
        
        folder_id = await self.multi_login_service.get_folder_id()
        
        async with self._profile_creation_lock:
            profile_ids = await self.multi_login_service.profile_manager.get_profile_ids(
                folder_id=folder_id
            )

            if len(profile_ids) < max_profiles:
                needed = max_profiles - len(profile_ids)
                print(f"Creating {needed} additional profiles...")
                
                for i in range(needed):
                    await self.multi_login_service.profile_manager.create_profile(
                        folder_id=folder_id,
                        name=f"Profile {len(profile_ids) + i + 1}"
                    )

        profile_ids = await self.multi_login_service.profile_manager.get_profile_ids(
                folder_id=folder_id
            )
        
        profile_ids_to_use = profile_ids[:max_profiles]
        results = [(url, profile_ids_to_use[i % len(profile_ids_to_use)]) 
                   for i, url in enumerate(urls)]
        
        return results