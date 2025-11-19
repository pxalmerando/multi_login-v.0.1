import logging
from typing import List
from app.services.url_processor import URLProcessor
from app.adapters.websocket_notifier import WebSocketNotifier
from app.services.multi_login_service import MultiLoginService
from app.services.url_processing_service import URLProcessingService
from app.services.batch_progress_notifier import BatchProgressNotifier
from app.services.concurrent_task_executor import ConcurrentTaskExecutor
from app.services.batch_result_aggregator import BatchResultAggregator
from app.services.profile_life_cycle_manager import ProfileLifecycleManager
from app.services.profile_allocation_service import ProfileAllocationService
from app.models.schemas.processing_results import ProcessingResult, BatchProcessingResult

logger = logging.getLogger(__name__)

class BatchProcessingOrchestrator:
    """
    Orchestrates batch URL processing by coordinating specialized components.
    Each component handles one specific aspect of processing.
    """
    
    def __init__(
        self,
        multi_login_service: MultiLoginService,
        notifier: WebSocketNotifier,
        max_concurrency: int,
        profile_allocator: ProfileAllocationService
    ):
        
        self.lifecycle_manager = ProfileLifecycleManager(profile_allocator)
        self.url_processor = URLProcessor(
            multi_login_service,
            URLProcessingService()
        )
        self.progress_notifier = BatchProgressNotifier(notifier)
        self.result_aggregator = BatchResultAggregator()
        self.task_executor = ConcurrentTaskExecutor(max_concurrency)
        
        self.multi_login_service = multi_login_service
    
    async def process_batch(self, urls: List[str]) -> BatchProcessingResult:
        """
        Process a batch of URLs with concurrent execution.
        Coordinates all components to complete the workflow.
        """
        
        if not urls:
            await self.progress_notifier.notify_error("No URLs provided")
            return BatchProcessingResult(
                failed_urls=0,
                successful_urls=0,
                total_urls=0,
                results=[]
            )
        
        
        await self.progress_notifier.notify_batch_start(
            total_urls=len(urls),
            max_concurrent=self.task_executor.max_concurrency
        )
        
        try:
            
            folder_id = await self.multi_login_service.get_folder_id()
            
            
            raw_results = await self.task_executor.execute_batch(
                items=urls,
                processor_func=lambda url: self._process_single_url(url, folder_id)
            )
            
            
            results = self.result_aggregator.handle_exception_results(
                raw_results,
                urls
            )
            
            
            batch_result = self.result_aggregator.create_batch_result(results)
            
            
            await self.progress_notifier.notify_batch_complete(
                total=batch_result.total_urls,
                successful=batch_result.successful_urls,
                failed=batch_result.failed_urls
            )
            
            logger.info(
                f"Batch complete: {batch_result.successful_urls} successful, "
                f"{batch_result.failed_urls} failed"
            )
            
            return batch_result
            
        except Exception as e:
            await self.progress_notifier.notify_error(
                f"Batch processing failed: {str(e)}"
            )
            raise
    
    async def _process_single_url(self, url: str, folder_id: str) -> ProcessingResult:
        """
        Process a single URL (called by task executor).
        Coordinates profile lifecycle and URL processing.
        """
        profile_id = None
        
        try:
            
            profile_id = await self.lifecycle_manager.acquire_profile(folder_id)
            
            if not profile_id:
                return ProcessingResult(
                    success=False,
                    url=url,
                    error_message="Failed to acquire profile"
                )
            
            logger.info(f"Processing {url} with profile {profile_id}")
            
            
            await self.progress_notifier.notify_url_processing(
                url=url,
                step=1,
                total_steps=3
            )
            
            
            result = await self.url_processor.process_with_profile(url, profile_id)
            
            
            if result.captcha_detected or not result.success:
                await self.lifecycle_manager.handle_failure(
                    profile_id,
                    reason="CAPTCHA" if result.captcha_detected else "Processing failed"
                )
                
                if result.captcha_detected:
                    await self.progress_notifier.notify_captcha_detected(url)
            else:
                await self.lifecycle_manager.handle_success(profile_id)
                await self.progress_notifier.notify_url_completed(result)
            
            return result
            
        except Exception as e:
            logger.exception(f"Error processing {url}: {e}")
            
            
            await self.lifecycle_manager.cleanup_on_error(profile_id)
            
            return ProcessingResult(
                success=False,
                url=url,
                error_message=str(e)
            )