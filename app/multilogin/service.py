from selenium import webdriver
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.chrome.options import Options
from src.http_client import HttpClient
from src.folder_manager import FolderManager
from src.profile_manager import ProfileManager
from src.token_manager import TokenManager
from src.auth import UserAuth
from decouple import config
import random

class MultiloginService:

    LAUNCHER_URL = "https://launcher.mlx.yt:45001"
    BASE_URL = "https://api.multilogin.com"

    def __init__(self) -> None:

        # Initialize managers
        self.user_auth = UserAuth(
            self.BASE_URL, 
            config("EMAIL"), 
            config("PASSWORD"),
            http_client=HttpClient(self.BASE_URL)
        )

        self.token_manager = TokenManager(self.user_auth)
        self.http_launcher = HttpClient(self.LAUNCHER_URL)
        self.folder_manager = FolderManager(api_token=self._get_tokens(), api_url=self.BASE_URL)
        self.profile_manager = ProfileManager(api_token=self._get_tokens(), api_url=self.BASE_URL)

        # Set headers
        self.headers = {
            "Authorization": f"Bearer {self._get_tokens()}"
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
            self.folder_manager.create_folder(folder_name=f"My Folder{number}")
        return self._folder_id_cache
    @property        
    def profile_id(self):
        if self._profile_id_cache is None:
            profile_ids = self.profile_manager.get_profile_ids(folder_id=self.folder_id)
            if profile_ids:
                self._profile_id_cache = profile_ids[0]
        else:
            self.profile_manager.create_profile(folder_id=self.folder_id, name="My Profile")

        return self._profile_id_cache

    def run_profile(self):
        print(self.headers)
        endpoint = f"api/v1/profile/f/{self.folder_id}/p/{self.profile_id}/start?automation_type=selenium"
        print(endpoint)
        return self.http_launcher.get(
            endpoint=endpoint, 
            headers=self.headers
        )
    
    def stop_profile(self):
        return self.http_launcher.post(f"api/v1/profile/stop_script", headers=self.headers)

    def process_url(self, url: str) -> dict:
        try:
            response = self.run_profile()
            selenium_port = response.get('status', {}).get('message')
            selenium_url = f"http://localhost:{selenium_port}"

            options = Options()
            options.add_argument("--disable-blink-features=AutomationControlled")

            driver = webdriver.Remote(
                command_executor=selenium_url,
                options=options
            )

            driver.get(url=url)
            page_title = driver.title

            return {
                "success": True,
                "message": f"Successfully processed URL with profile {self.profile_id}",
                "data": {
                    "profile_id": self.profile_id,
                    "folder_id": self.folder_id,
                    "url": url,
                    "page_title": page_title,
                    "selenium_port": selenium_port
                }
            }
        except (WebDriverException, TimeoutException) as e:
            return {
                "success": False,
                "message": f"Failed to process URL with profile {self.profile_id}: {e}",
                "data": {}
            }