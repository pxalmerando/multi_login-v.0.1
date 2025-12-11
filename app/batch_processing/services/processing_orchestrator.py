import logging
from typing import List
from app.batch_processing.services.url_processor import URLProcessor
from app.multilogin.domain.profile_lifecycle_manager import ProfileLifecycleManager
from app.utils.concurrent_task_executor import ConcurrentTaskExecutor
from app.batch_processing.schemas import ProcessingResult, BatchProcessingResult
from app.batch_processing.services.result_aggregator import BatchResultAggregator
from app.batch_processing.services.progress_notifier import BatchProgressNotifier

logger = logging.getLogger(__name__)

class BatchProcessingOrchestrator:
    """
    Coordinate batch URL processing using injected services.

    Uses URLProcessor, BatchProgressNotifier, BatchResultAggregator,
    ConcurrentTaskExecutor, and ProfileLifecycleManager to process many URLs.
    """
    
    def __init__(
        self,
        url_processor: URLProcessor,
        progress_notifier: BatchProgressNotifier,
        result_aggregator: BatchResultAggregator,
        task_executor: ConcurrentTaskExecutor,
        lifecycle_manager: ProfileLifecycleManager,
    ):
        self.url_processor = url_processor
        self.progress_notifier = progress_notifier
        self.result_aggregator = result_aggregator
        self.task_executor = task_executor
        self.lifecycle_manager = lifecycle_manager
    
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
            folder_id = await self.url_processor.multi_login.get_folder_id()
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
        Process a single URL using a profile from the given folder and handle CAPTCHA/failures.
        Acquires a profile, runs URLProcessor, updates profile status, and returns a ProcessingResult.
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
            result = await self.url_processor.process_with_profile(url, profile_id, folder_id)
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