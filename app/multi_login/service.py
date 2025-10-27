from selenium.common.exceptions import TimeoutException, WebDriverException
from src.http_client import HttpClient
from src.folder_manager import FolderManager
from src.profile_manager import ProfileManager
from src.token_manager import TokenManager
from src.auth import UserAuth
from decouple import config
import random
from .browser_manager import BrowserManager

class MultiLoginService:

    LAUNCHER_URL = "https://launcher.mlx.yt:45001"
    BASE_URL = "https://api.multilogin.com"
    PROFILE_RUNNING = []

    def __init__(self) -> None:

        self.user_auth = UserAuth(
            self.BASE_URL, 
            config("EMAIL"), 
            config("PASSWORD"),
            http_client=HttpClient(self.BASE_URL)
        )

        self.token_manager = TokenManager(self.user_auth)
        self._access_token = self._get_tokens()


        self.http_launcher = HttpClient(self.LAUNCHER_URL)
        self.folder_manager = FolderManager(api_token=self._access_token, api_url=self.BASE_URL)
        self.profile_manager = ProfileManager(api_token=self._access_token, api_url=self.BASE_URL)

        self.headers = {
            "Authorization": f"Bearer {self._access_token}"
        }

        self._folder_id_cache = None
        self._profile_id_cache = None

    def _get_tokens(self) -> str:
        results = self.token_manager.get_tokens()
        access_token = results.get("access_token", {})
        return access_token
    
    @property    
    def folder_id(self):
        if self._folder_id_cache is None:
            folder_ids = self.folder_manager.get_folder_ids()
            if folder_ids:
                self._folder_id_cache = folder_ids[0]
            else:
                number = random.randint(1, 1000)
                folder_name = f"My Folder{number}"
                new_folder = self.folder_manager.create_folder(folder_name=folder_name)
                self._folder_id_cache = new_folder['id']
        return self._folder_id_cache

    @property        
    def profile_id(self):
        if self._profile_id_cache is None:
            profile_ids = self.profile_manager.get_profile_ids(folder_id=self.folder_id)
            if profile_ids:
                self._profile_id_cache = profile_ids[0]
            else:
                profile_name = f"My Profile"
                new_profile = self.profile_manager.create_profile(folder_id=self.folder_id, name=profile_name)
                self._profile_id_cache = new_profile['id']

        return self._profile_id_cache
    def _get_running_profile_port(self, profile_id: str) -> int:
        for profile in self.PROFILE_RUNNING:
            if profile['profile_id'] == profile_id:
                return profile['selenium_port']

        return None
    def cleanup(self):
        for profile in self.PROFILE_RUNNING:
            self.stop_profile(profile['profile_id'])
        self.PROFILE_RUNNING.clear()
    def start_profile(self) -> str:
        try:
            selenium_port = self._get_running_profile_port(self.profile_id)
            
            if selenium_port:
                selenium_url = f"http://localhost:{selenium_port}"
                return selenium_url

            endpoint = f"api/v1/profile/f/{self.folder_id}/p/{self.profile_id}/start?automation_type=selenium"
            response = self.http_launcher.get(endpoint, headers=self.headers)
            selenium_port = response.get('status', {}).get('message')
            selenium_url = f"http://localhost:{selenium_port}"

            self.PROFILE_RUNNING.append({
                "profile_id": self.profile_id,
                "selenium_port": selenium_port
            })

            return selenium_url


        except Exception as e:
            print(f"Failed to start profile {self.profile_id}: {e}")
            return None    
    def stop_profile(self, profile_id: str):
        endpoint = f"api/v1/profile/stop/p/{profile_id}"
        return self.http_launcher.get(endpoint=endpoint, headers=self.headers)


    def process_url(self, url: str):
        try:               
            selenium_url = self.start_profile()
            if selenium_url:
                with BrowserManager(selenium_url=selenium_url) as driver:
                    driver.get(url)
                    return {
                        "success": True,
                        "message": "URL processed successfully",
                        "Title": driver.title,
                        "data": driver.page_source
                    }
            print("Failed to start profile", selenium_url)

        except (WebDriverException, TimeoutException) as e:
            self.PROFILE_RUNNING = [p for p in self.PROFILE_RUNNING if p.get("profile_id") != self.profile_id]
            self.stop_profile(self.profile_id)
            return {
                "success": False,
                "message": f"Failed to process URL with profile {self.profile_id}: {e}",
                "data": {}
            }