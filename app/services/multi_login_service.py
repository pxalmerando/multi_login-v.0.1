from app.utils.http_client import HttpClient
from app.services.multilogin.auth import UserAuth
from app.services.multilogin.folder_manager import FolderManager
from app.services.multilogin.token_manager import TokenManager
from app.services.multilogin.profile_manager import ProfileManager
from app.models.schemas.profile_models import MultiLoginProfileSession

from decouple import config
import random


class MultiLoginService:
    LAUNCHER_URL = "https://launcher.mlx.yt:45001"
    BASE_URL = "https://api.multilogin.com"

    def __init__(self) -> None:

        self.email = config("EMAIL")
        self.password = config("PASSWORD")

        self.http_client = HttpClient(self.BASE_URL)
        self.http_launcher = HttpClient(self.LAUNCHER_URL)

        self._access_token = None
        self._folder_id_cache = None
        self._profile_id_cache = []
        self.profile_running = []

    async def initialize(self):
        self._access_token = await self._get_tokens()
        self.folder_manager = FolderManager(
            self.BASE_URL, 
            self._access_token
        )
        self.profile_manager = ProfileManager(
            self.BASE_URL, 
            self._access_token
        )
        self.headers = {
            "Authorization": f"Bearer {self._access_token}"
        }

    async def _get_tokens(self) -> str:

        user_auth = UserAuth(
            base_url=self.BASE_URL,
            email=self.email,
            password=self.password,
            http_client=self.http_client
        )       
        
        token_manager = TokenManager(user_auth)
        results = await token_manager.get_tokens()
        return results.get("access_token", None)
    
    async def get_folder_id(self):
        if self._folder_id_cache is None:
            folder_ids = await self.folder_manager.get_folder_ids()
            if folder_ids:
                self._folder_id_cache = folder_ids[0]
            else:
                folder_name = f"Folder {random.randint(1, 100)}"
                new_folder = await self.folder_manager.create_folder(name=folder_name)
                self._folder_id_cache = new_folder['id']

        return self._folder_id_cache
    
    def _get_running_profile_port(self, profile_id: str) -> int:
        for profile in self.profile_running:
            if profile['profile_id'] == profile_id:
                return profile['selenium_port']

        return None
    async def cleanup(self):
        for profile in self.profile_running:
            await self.stop_profile(profile['profile_id'])
        self.profile_running.clear()

    async def start_profile(self, profile_id: str) -> str:
        folder_id = await self.get_folder_id()
        try:         
            endpoint = f"api/v1/profile/f/{folder_id}/p/{profile_id}/start?automation_type=selenium"
            response = await self.http_launcher.get(endpoint, headers=self.headers)
            try:
                http_code = response.get("status", {}).get("http_code", None)
                selenium_port = response.get("status", {}).get("message", None)

                selenium_url = MultiLoginProfileSession(
                    profile_id=profile_id,
                    selenium_port=selenium_port
                )

                url = selenium_url.selenium_url
                print(url)
                self.profile_running.append({
                    "profile_id": profile_id,
                    "selenium_port": selenium_port
                })
                return url
            except Exception as e:
                print(f"Failed to get http_code or selenium_port: {e}")
        except Exception as e:
            print(f"Failed to start profile {profile_id}: {e}")
            return None
    async def stop_profile(self, profile_id: str):
        try:
            endpoint = f"api/v1/profile/stop/p/{profile_id}"
            self.profile_running = [p for p in self.profile_running if p.get("profile_id") != profile_id]
            await self.http_launcher.get(endpoint=endpoint, headers=self.headers)
        except Exception as e:
            print(f"Failed to stop profile {profile_id}: {e}")
