import asyncio
import logging
from typing import Optional
from app.services.multilogin_auth_service import MultiLoginAuthService
from app.services.profile_operation_service import ProfileOperationService
from app.services.session_cleanup_service import SessionCleanupService
from app.utils.http_client import HttpClient
from app.core.config import BASE_URL, LAUNCHER_URL
from app.services.profile_registry import ProfileRegistry
from app.services.multilogin.folder_manager import FolderManager
from app.services.multilogin.profile_manager import ProfileManager
from app.services.multilogin.redis_token_manager import RedisTokenManager

logger = logging.getLogger(__name__)


class MultiLoginService:
    """
    Orchestrates MultiLogin operations by coordinating specialized services.
    
    This is the main entry point that other parts of your application use.
    It delegates actual work to focused, single-responsibility services.
    """
    
    def __init__(self, email: str = None, password: str = None, 
                 base_url: str = None, launcher_url: str = None,
                 token_manager: Optional[RedisTokenManager] = None):
        
        self.base_url = base_url or BASE_URL
        self.launcher_url = launcher_url or LAUNCHER_URL
        
        
        self.http_client = HttpClient(self.base_url)
        self.http_launcher = HttpClient(self.launcher_url)
        
        
        self.profile_registry = ProfileRegistry()
        
        
        self.multilogin_auth = MultiLoginAuthService(
            email, password, self.base_url, self.http_client, token_manager
        )
        
        
        self.folder_manager: Optional[FolderManager] = None
        self.profile_manager: Optional[ProfileManager] = None
        self.profile_operations: Optional[ProfileOperationService] = None
        self.cleanup_service: Optional[SessionCleanupService] = None
        self.headers: Optional[dict] = None
        
        self._init_lock = asyncio.Lock()
        self._initialized = False
    
    async def initialize(self) -> None:
        """Initialize all service components"""
        if self._initialized:
            return
        
        async with self._init_lock:
            if self._initialized:
                return
            
            
            access_token = await self.multilogin_auth.get_access_token()
            self.headers = {"Authorization": f"Bearer {access_token}"}
            
            
            self.folder_manager = FolderManager(self.base_url, access_token)
            self.profile_manager = ProfileManager(self.base_url, access_token)
            
            
            self.profile_operations = ProfileOperationService(
                self.http_launcher,
                self.profile_registry
            )
            self.cleanup_service = SessionCleanupService(
                self.profile_registry,
                self.profile_operations
            )
            
            self._initialized = True
            logger.info("MultiLoginService initialized successfully")
    
    async def get_folder_id(self, folder_name: Optional[str] = None) -> str:
        """
        Get or create a default folder.
        Delegates to FolderManager which already has this logic.
        """
        if not self._initialized:
            await self.initialize()
        
        return await self.folder_manager.get_or_create_default_folder(folder_name)
    
    async def start_profile(self, profile_id: str, folder_id: Optional[str] = None) -> str:
        """
        Start a profile and return its Selenium URL.
        
        Args:
            profile_id: The profile to start
            folder_id: Optional folder ID (will be fetched if not provided)
        
        Returns:
            Selenium URL for the started profile
        """
        if not self._initialized:
            await self.initialize()
        
        if folder_id is None:
            folder_id = await self.get_folder_id()
        
        return await self.profile_operations.start_profile(
            profile_id, folder_id, self.headers
        )
    
    async def stop_profile(self, profile_id: str) -> None:
        """Stop a running profile"""
        if not self._initialized:
            await self.initialize()
        
        await self.profile_operations.stop_profile(profile_id, self.headers)
    
    async def delete_profile(self, profile_id: str) -> None:
        """
        Delete a profile permanently (stops it first if running).
        
        Note: This is different from ProfileLifecycleManager.handle_failure()
        which makes the *decision* to delete. This just executes the deletion.
        """
        if not self._initialized:
            await self.initialize()
        
        
        if await self.profile_registry.is_running(profile_id):
            await self.profile_operations.stop_profile(profile_id, self.headers)
        
        
        await self.profile_registry.unregister(profile_id)
        await self.profile_manager.delete_profile(profile_id)
        logger.info(f"Profile {profile_id} deleted")
    
    async def cleanup(self) -> None:
        """Stop all running profiles"""
        if not self._initialized:
            await self.initialize()
        
        await self.cleanup_service.cleanup_all(self.headers)