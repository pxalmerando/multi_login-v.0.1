
import logging

from app.models.schemas.processing_results import ProcessingResult
from app.services.multi_login_service import MultiLoginService
from app.services.url_processing_service import URLProcessingService

logger = logging.getLogger(__name__)

class URLProcessor:
    """
    Handles the processing of a single URL through browser automation.
    Manages the connection to browser and URL processing logic.
    """
    
    def __init__(
        self,
        multi_login_service: MultiLoginService,
        url_processing_service: URLProcessingService
    ):
        self.multi_login = multi_login_service
        self.url_processor = url_processing_service
    
    async def process_with_profile(
        self,
        url: str,
        profile_id: str,
        folder_id: str
    ) -> ProcessingResult:
        """
        Process a URL using the given profile.
        Returns ProcessingResult with success/failure details.
        """
        selenium_url = None
        
        try:
            
            selenium_url = await self.multi_login.start_profile(profile_id, folder_id)
            
            if selenium_url is None:
                logger.error(f"[URLProcessor] Failed to start profile {profile_id}")
                return ProcessingResult(
                    success=False,
                    error_message="Failed to start browser profile",
                    url=url
                )
            
            logger.info(f"[URLProcessor] Started browser at {selenium_url}")
            
            
            result = await self.url_processor.process_url(
                url=url,
                selenium_url=selenium_url
            )
            
            
            if result.captcha_detected:
                logger.warning(f"[URLProcessor] CAPTCHA detected for {url}")
                return ProcessingResult(
                    success=False,
                    url=url,
                    captcha_detected=True,
                    error_message="CAPTCHA detected!"
                )
            
            if result.success:
                logger.info(f"[URLProcessor] Successfully processed {url}")
            
            return result
            
        except Exception as e:
            logger.exception(f"[URLProcessor] Error processing {url}: {e}")
            return ProcessingResult(
                success=False,
                url=url,
                error_message=str(e)
            )