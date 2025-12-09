
from app.batch_processing.schemas import ProcessingResult
from app.adapters.websocket_notifier import WebSocketNotifier

class BatchProgressNotifier:
    """
    Handles all user-facing notifications during batch processing.
    Abstracts away the websocket/notification details.
    """
    
    def __init__(self, notifier: WebSocketNotifier):
        self.notifier = notifier
    
    async def notify_batch_start(self, total_urls: int, max_concurrent: int):
        """Notify when batch processing begins."""
        await self.notifier.notify_batch_started(
            total_urls=total_urls,
            max_concurrent=max_concurrent
        )
    
    async def notify_url_processing(self, url: str, step: int, total_steps: int):
        """Notify when a specific URL is being processed."""
        await self.notifier.notify_processing(
            step=step,
            message=f"Processing URL: {url}",
            total_steps=total_steps
        )
    
    async def notify_profile_started(self, selenium_url: str, step: int, total_steps: int):
        """Notify when browser profile is ready."""
        await self.notifier.notify_processing(
            message=f"Browser ready: {selenium_url}",
            step=step,
            total_steps=total_steps
        )
    
    async def notify_captcha_detected(self, url: str):
        """Notify when CAPTCHA is detected."""
        await self.notifier.notify_error(f"CAPTCHA detected for URL: {url}")
    
    async def notify_url_completed(self, result: ProcessingResult):
        """Notify when URL processing completes successfully."""
        await self.notifier.notify_completed(
            message="URL processed successfully",
            data=result.to_dict()
        )
    
    async def notify_batch_complete(
        self,
        total: int,
        successful: int,
        failed: int
    ):
        """Notify when entire batch completes."""
        await self.notifier.notify_batch_completed(
            successful_urls=successful,
            total_urls=total,
            failed_urls=failed
        )
    
    async def notify_error(self, message: str):
        """Notify general error."""
        await self.notifier.notify_error(message)