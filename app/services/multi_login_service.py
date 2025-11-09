from app.utils.http_client import HttpClient
from app.services.multilogin.auth import UserAuth
from app.services.multilogin.folder_manager import FolderManager
from app.services.multilogin.token_manager import TokenManager
from app.services.multilogin.profile_manager import ProfileManager
from app.models.schemas.profile_models import MultiLoginProfileSession
from app.services.profile_registry import ProfileRegistry
from collections import defaultdict
import asyncio
from app.core.config import (
    BASE_URL,
    LAUNCHER_URL
)
from decouple import config
import random
class MultiLoginService:
    def __init__(self, base_url: str = None, launcher_url: str = None, email: str = None, password: str = None) -> None:
        self.email = email or config("EMAIL")
        self.password = password or config("PASSWORD")
        self.base_url = base_url or BASE_URL
        self.launcher_url = launcher_url or LAUNCHER_URL
        self.http_client = HttpClient(self.base_url)
        self.http_launcher = HttpClient(self.launcher_url)
        self.profile_registry = ProfileRegistry()
        self._access_token = None
        self._folder_id_cache = None
        self.folder_manager = None
        self.profile_manager = None
        self.headers = None
        self._profile_locks: defaultdict[str, asyncio.Lock] = defaultdict(asyncio.Lock)
        
    async def initialize(self):
        self._access_token = await self._get_tokens()
        self.folder_manager = FolderManager(
            self.base_url, 
            self._access_token
        )
        self.profile_manager = ProfileManager(
            self.base_url, 
            self._access_token
        )
        self.headers = {
            "Authorization": f"Bearer {self._access_token}"
        }
    async def _get_tokens(self) -> str:
        user_auth = UserAuth(
            base_url=self.base_url,
            email=self.email,
            password=self.password,
            http_client=self.http_client
        )       
        
        token_manager = TokenManager(user_auth)
        results = await token_manager.get_tokens()
        access_token = results.get("access_token")
        if not access_token:
            raise Exception("Authentication failed. Failed: Unable to obtain access token")
        
        return access_token
    
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
    async def cleanup(self):
        sessions = self.profile_registry.get_all_sessions()
        if not sessions:
            print("No profiles running")
            return
        
        print(f"Cleaning up {len(sessions)} running profiles...")
        failures = []
        for session in sessions:
            try:
                await self.stop_profile(session.profile_id)
            except Exception as e:
                print(f'failed to stop profile {session.profile_id}: {e}')
                failures.append(session.profile_id)
        
        self.profile_registry.clear()
        self._profile_locks.clear()
        if failures:
            print(f"Failed to stop profiles: {failures}")
        else:
            print("All profiles stopped successfully")
    
    def _parse_profile_start_response(self, response: dict, profile_id: str) -> MultiLoginProfileSession:
        http_code = response.get("status", {}).get("http_code", None)
        selenium_port = response.get("status", {}).get("message", None)
        if http_code is None or selenium_port is None:
            raise Exception(f"Invalid response: missing http_code or selenium_port {profile_id}")
        return MultiLoginProfileSession(
            status_code=http_code,
            profile_id=profile_id,
            selenium_port=selenium_port
        )
    async def delete_profile(self, profile_id: str) -> None:
        async with self._profile_locks[profile_id]:
            try:
                await self.profile_manager.delete_profile(profile_id)
                await self.profile_registry.unregister(profile_id)
                print(f"Profile {profile_id} deleted")
            except Exception as e:
                print(f"Failed to delete profile {profile_id}: {e}")
    async def start_profile(self, profile_id: str) -> str:        
        async with self._profile_locks[profile_id]:
            existing_session = await self.profile_registry.get_session(profile_id=profile_id)
            if existing_session:
                print(f"Profile {profile_id} already running, reusing session")
                return existing_session.selenium_url
                
            folder_id = await self.get_folder_id()
            endpoint = f"api/v1/profile/f/{folder_id}/p/{profile_id}/start?automation_type=selenium"
        
            try:
                response = await self.http_launcher.get(endpoint=endpoint, headers=self.headers)
                session = self._parse_profile_start_response(response, profile_id)
                
                if session.status_code == 401:
                    raise ValueError(f"Unauthorized to start profile {profile_id}: {session.selenium_port}")
                
                if session.status_code == 400:
                    raise ValueError(f"Profile {profile_id} already running or invalid request")
                
                if session.status_code != 200:
                    raise ValueError(f"Failed to start profile {profile_id}: HTTP {session.status_code} - {session.selenium_port}")
                
                await self.profile_registry.register(session)
                print(f"Profile {profile_id} started on port {session.selenium_port}")
                return session.selenium_url
            
            except Exception as e:
                raise Exception(f"Failed to start profile {profile_id}: {e}") from e
    async def stop_profile(self, profile_id: str) -> None:
        async with self._profile_locks[profile_id]:
            profile_running = await self.profile_registry.is_running(profile_id)
            if not profile_running:
                print(f"Profile {profile_id} is not running.")
                return
            
            endpoint = f"api/v1/profile/stop/p/{profile_id}"
            try:
                await self.http_launcher.get(endpoint=endpoint, headers=self.headers)
                await self.profile_registry.unregister(profile_id)
                print(f"Profile {profile_id} stopped")
            except Exception as e:
                await self.profile_registry.unregister(profile_id)
                raise Exception(f"Failed to stop profile {profile_id}: {e}") from e