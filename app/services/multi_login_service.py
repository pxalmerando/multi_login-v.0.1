import random
import asyncio
import logging
from typing import Dict, Optional, Any

from decouple import config

from app.utils.http_client import HttpClient
from app.services.multilogin.auth import UserAuth
from app.core.config import BASE_URL, LAUNCHER_URL
from app.services.profile_registry import ProfileRegistry
from app.services.multilogin.token_manager import TokenManager
from app.services.multilogin.folder_manager import FolderManager
from app.services.multilogin.profile_manager import ProfileManager
from app.models.schemas.profile_models import MultiLoginProfileSession

logger = logging.getLogger(__name__)


class MultiLoginServiceError(Exception):
    """Domain exception for MultiLoginService failures."""


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

        self._profile_locks: Dict[str, asyncio.Lock] = {}

        self._init_lock = asyncio.Lock()
        self._initialized = False
    
    def _get_profile_lock(self, profile_id: str) -> asyncio.Lock:
        lock = self._profile_locks.get(profile_id)
        if lock is None:
            lock = asyncio.Lock()
            self._profile_locks[profile_id] = lock
        return lock

    async def initialize(self) -> None:

        if self._initialized:
            return
        
        async with self._init_lock:

            if self._initialized:
                return
            

            self._access_token = await self._get_tokens()
            self.folder_manager = FolderManager(self.base_url, self._access_token)
            self.profile_manager = ProfileManager(self.base_url, self._access_token)
            self.headers = {"Authorization": f"Bearer {self._access_token}"}

            self._initialized = True
            logger.info("MultiLoginService initialized with access token", self._access_token)

    async def _get_tokens(self) -> str:

        try:
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
                raise MultiLoginServiceError("Authentication failed. Failed: Unable to obtain access token")
            
            return access_token
        
        except Exception as e:
            raise MultiLoginServiceError(f"Authentication failed. Failed: {e}")
    
    async def get_folder_id(self, folder_name: Optional[str] = None) -> str:
        if self._folder_id_cache is not None:
            return self._folder_id_cache
        
        if self.profile_manager is None:
            raise MultiLoginServiceError("Service not initialized. Call initialize() first")
        
        try:
            folder_name = folder_name or f"Folder {random.randint(1, 100)}"

            folder_ids = await self.folder_manager.get_folder_ids()
            if folder_ids:
                self._folder_id_cache = folder_ids[0]
                return self._folder_id_cache
            
            new_folder = await self.folder_manager.create_folder(folder_name)
            data = new_folder.get('data', {})
            folder_id = data.get('id')

            self._folder_id_cache = folder_id
            return folder_id
        except Exception as e:
            logger.exception(f"Failed to get folder ID: {e}")
            raise

    async def cleanup(self) -> None:

        sessions = self.profile_registry.get_all_sessions()
        if not sessions:
            logger.debug("No profiles running")
            return
        
        logger.info("Cleaning up %d running profiles...", len(sessions))
        failures = []
        for session in sessions:
            try:
                await self.stop_profile(session.profile_id)
            except Exception as e:
                logger.exception(f'failed to stop profile {session.profile_id}: {e}')
                failures.append(session.profile_id)
        
        self.profile_registry.clear()
        self._profile_locks.clear()

        if failures:
            logger.info(f"Failed to stop profiles: {failures}")
        else:
            logger.info("All profiles stopped successfully")
    
    def _parse_profile_start_response(self, response: dict, profile_id: str) -> MultiLoginProfileSession:

        try:
            if not isinstance(response, dict):
                raise MultiLoginServiceError(f"Invalid response: {response}")
            
            status = response.get("status")
            if not isinstance(status, dict):
                raise MultiLoginServiceError(f"Invalid status: {status}")
            
            http_code = status.get("http_code")

            if http_code is None:
                raise MultiLoginServiceError(f"Invalid response: missing http_code {profile_id}")
            
            selenium_port = status.get("message")
            if selenium_port is None:
                raise MultiLoginServiceError(f"Invalid response: missing selenium_port {profile_id}")
            
            return MultiLoginProfileSession(
                status_code=http_code,
                profile_id=profile_id,
                selenium_port=selenium_port
            )
        
        except Exception as e:
            raise MultiLoginServiceError(f"Invalid response: {e}")
        
    async def delete_profile(self, profile_id: str) -> None:

        lock = self._get_profile_lock(profile_id)
        async with lock:
            try:
                if self.profile_manager is None:
                    raise MultiLoginServiceError("Service not initialized. Call initialize() first")
                
                await self.profile_manager.delete_profile(profile_id)
                await self.profile_registry.unregister(profile_id)
                logger.info(f"Profile {profile_id} deleted")

            except Exception as e:
                logger.exception(f"Failed to delete profile {profile_id}: {e}")
                raise

    async def start_profile(self, profile_id: str) -> str:
        if not self._initialized:
            await self.initialize()

        lock = self._get_profile_lock(profile_id)     
        async with lock:

            existing_session = await self.profile_registry.get_session(profile_id=profile_id)

            if existing_session:
                logger.info(f"Profile {profile_id} already running, reusing session")
                return existing_session.selenium_url
                
            folder_id = await self.get_folder_id()
            endpoint = f"api/v1/profile/f/{folder_id}/p/{profile_id}/start?automation_type=selenium"
        
            try:
                response = await self.http_launcher.get(endpoint=endpoint, headers=self.headers)
                session = self._parse_profile_start_response(response, profile_id)
                
                if session.status_code == 401:
                    raise MultiLoginServiceError(f"Unauthorized to start profile {profile_id}: {session.selenium_port}")
                
                if session.status_code == 400:
                    raise MultiLoginServiceError(f"Profile {profile_id} already running or invalid request")
                
                if session.status_code != 200:
                    raise MultiLoginServiceError(f"Failed to start profile {profile_id}: HTTP {session.status_code} - {session.selenium_port}")
                
                await self.profile_registry.register(session)
                logger.info(f"Profile {profile_id} started on port {session.selenium_port}")
                return session.selenium_url
            
            except Exception as e:
                logger.exception(f"Failed to start profile {profile_id}: {e}")
                raise

    async def stop_profile(self, profile_id: str) -> None:

        if not self._initialized:
            await self.initialize()

        lock = self._get_profile_lock(profile_id)
        async with lock:

            profile_running = await self.profile_registry.is_running(profile_id)
            if not profile_running:
                logger.info(f"Profile {profile_id} is not running.")
                return
            
            endpoint = f"api/v1/profile/stop/p/{profile_id}"

            try:
                await self.http_launcher.get(endpoint=endpoint, headers=self.headers)
                await self.profile_registry.unregister(profile_id)
                logger.info(f"Profile {profile_id} stopped")

            except Exception as e:
                await self.profile_registry.unregister(profile_id)
                logger.exception(f"Failed to stop profile {profile_id}: {e}")