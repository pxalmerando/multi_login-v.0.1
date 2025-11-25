import logging
from typing import List
from app.services.profile_registry import ProfileRegistry
from app.services.profile_operation_service import ProfileOperationService

logger = logging.getLogger(__name__)


class SessionCleanupService:
    """
    Responsible for batch cleanup operations on running profiles.
    """
    
    def __init__(self, profile_registry: ProfileRegistry, 
                 profile_operations: ProfileOperationService):
        self.profile_registry = profile_registry
        self.profile_operations = profile_operations
    
    async def cleanup_all(self, headers: dict) -> List[str]:
        """
        Stop all running profiles and return list of failures.
        
        Returns:
            List of profile IDs that failed to stop
        """
        sessions = self.profile_registry.get_all_sessions()
        if not sessions:
            logger.debug("No profiles running")
            return []
        
        logger.info(f"Cleaning up {len(sessions)} running profiles...")
        failures = []
        
        for session in sessions:
            try:
                await self.profile_operations.stop_profile(session.profile_id, headers)
            except Exception as e:
                logger.exception(f"Failed to stop profile {session.profile_id}: {e}")
                failures.append(session.profile_id)
        
        self.profile_registry.clear()
        self.profile_operations.clear_locks()
        
        if failures:
            logger.warning(f"Failed to stop profiles: {failures}")
        else:
            logger.info("All profiles stopped successfully")
        
        return failures