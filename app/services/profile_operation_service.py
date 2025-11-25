import asyncio
import logging
from typing import Dict
from app.utils.http_client import HttpClient
from app.services.profile_registry import ProfileRegistry
from app.services.multilogin.exceptions import MultiLoginServiceError
from app.services.multilogin.parser import parse_profile_start_response

logger = logging.getLogger(__name__)


class ProfileOperationService:
    """
    Responsible for low-level profile operations (start/stop/delete).
    Interacts directly with MultiLogin API endpoints.
    """
    
    def __init__(self, http_launcher: HttpClient, profile_registry: ProfileRegistry):
        self.http_launcher = http_launcher
        self.profile_registry = profile_registry
        self._profile_locks: Dict[str, asyncio.Lock] = {}
    
    def _get_profile_lock(self, profile_id: str) -> asyncio.Lock:
        """Get or create a lock for a specific profile"""
        if profile_id not in self._profile_locks:
            self._profile_locks[profile_id] = asyncio.Lock()
        return self._profile_locks[profile_id]
    
    async def start_profile(self, profile_id: str, folder_id: str, headers: dict) -> str:
        """
        Start a profile and return its Selenium URL.
        Ensures thread-safe operation with profile-specific locks.
        """
        lock = self._get_profile_lock(profile_id)
        async with lock:
            
            existing_session = await self.profile_registry.get_session(profile_id=profile_id)
            if existing_session:
                logger.info(f"Profile {profile_id} already running, reusing session")
                return existing_session.selenium_url
            
            
            endpoint = f"api/v1/profile/f/{folder_id}/p/{profile_id}/start?automation_type=selenium"
            
            try:
                response = await self.http_launcher.get(endpoint=endpoint, headers=headers)
                session = parse_profile_start_response(response, profile_id)
                
                self._validate_start_response(session, profile_id)
                
                await self.profile_registry.register(session)
                logger.info(f"Profile {profile_id} started on port {session.selenium_port}")
                return session.selenium_url
            
            except Exception as e:
                logger.exception(f"Failed to start profile {profile_id}: {e}")
                await self._cleanup_failed_start(profile_id, headers)
                raise
    
    def _validate_start_response(self, session, profile_id: str) -> None:
        """Validate the profile start response status code"""
        if session.status_code == 401:
            raise MultiLoginServiceError(f"Unauthorized to start profile {profile_id}")
        
        if session.status_code == 400:
            raise MultiLoginServiceError(f"Profile {profile_id} already running or invalid request")
        
        if session.status_code != 200:
            raise MultiLoginServiceError(
                f"Failed to start profile {profile_id}: HTTP {session.status_code}"
            )
    
    async def stop_profile(self, profile_id: str, headers: dict) -> None:
        """Stop a running profile"""
        lock = self._get_profile_lock(profile_id)
        async with lock:
            if not await self.profile_registry.is_running(profile_id):
                logger.info(f"Profile {profile_id} is not running.")
                return
            
            await self._stop_profile_internal(profile_id, headers)
    
    async def _stop_profile_internal(self, profile_id: str, headers: dict) -> None:
        """Internal helper to stop a profile (caller must hold lock)"""
        endpoint = f"api/v1/profile/stop/p/{profile_id}"
        try:
            await self.http_launcher.get(endpoint=endpoint, headers=headers)
            await self.profile_registry.unregister(profile_id)
            logger.info(f"Profile {profile_id} stopped")
        except Exception as e:
            await self.profile_registry.unregister(profile_id)
            logger.exception(f"Failed to stop profile {profile_id}: {e}")
            raise
    
    async def _cleanup_failed_start(self, profile_id: str, headers: dict) -> None:
        """Clean up after a failed profile start"""
        try:
            stop_endpoint = f"api/v1/profile/stop/p/{profile_id}"
            await self.http_launcher.get(endpoint=stop_endpoint, headers=headers, timeout=5.0)
            logger.info(f"Stopped profile {profile_id} after startup failure")
        except Exception as stop_error:
            logger.warning(f"Failed to stop profile {profile_id} after startup failure: {stop_error}")
    
    def clear_locks(self) -> None:
        """Clear all profile locks"""
        self._profile_locks.clear()