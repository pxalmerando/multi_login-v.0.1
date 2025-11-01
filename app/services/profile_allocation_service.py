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
    ) -> List[Tuple[str, str]]:
        
        await self.multi_login_service.initialize()
        folder_id = await self.multi_login_service.get_folder_id()
        profile_ids = await self.multi_login_service.profile_manager.get_profile_ids(folder_id=folder_id)
        
        profile_queue = asyncio.Queue()
        
        for profile in profile_ids:
            await profile_queue.put(profile)

        results = []

        async def process_url(url: str) -> List[Tuple[str, str]]:
            profile_id = await profile_queue.get()
            try:
                results.append((url, profile_id))
            except Exception as e:
                print(f"Failed to process url {url}: {e}")
            finally:
                await profile_queue.put(profile_id)
        
        tasks = [
            process_url(url)
            for url in urls
        ]

        await asyncio.gather(*tasks)

        return results

    
