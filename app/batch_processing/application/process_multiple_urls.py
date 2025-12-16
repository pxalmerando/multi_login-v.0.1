"""WebSocket handlers for processing URLs and managing connections."""
from fastapi import WebSocket
from app.infrastructure.websocket.websocket_notifier import WebSocketNotifier
from app.multilogin.application.multi_login_service import MultiLoginService
from app.batch_processing.services.url_processor import URLProcessor
from app.multilogin.application.profile_allocation_service import ProfileAllocationService
from app.multilogin.domain.profile_lifecycle_manager import ProfileLifecycleManager
from app.utils.concurrent_task_executor import ConcurrentTaskExecutor
from app.batch_processing.services.progress_notifier import BatchProgressNotifier
from app.batch_processing.services.result_aggregator import BatchResultAggregator
from app.batch_processing.services.url_processing_service import URLProcessingService
from app.batch_processing.services.processing_orchestrator import BatchProcessingOrchestrator

async def process_multiple_urls(
    websocket: WebSocket,
    urls: list[str],
    multi_login_service: MultiLoginService,
    profile_allocator: ProfileAllocationService,
    max_concurrency: int = 3
):
    """Process multiple URLs using batch processing with WebSocket notifications.

    Args:
        websocket (WebSocket): The WebSocket connection for sending status updates.
        urls (list[str]): List of URLs to process.
        multi_login_service (MultiLoginService): Service for handling multi-login operations.
        profile_allocator (ProfileAllocationService): Service for allocating browser profiles.
        max_concurrency (int): Maximum number of concurrent processing tasks. Defaults to 3.
    """
    notifier = WebSocketNotifier(
        websocket=websocket,
    )

    lifecycle_manager = ProfileLifecycleManager(profile_allocator)

    url_processing_service = URLProcessingService()
    
    url_processor = URLProcessor(multi_login_service, url_processing_service)
    progress_notifier = BatchProgressNotifier(notifier)
    result_aggregator = BatchResultAggregator()
    task_executor = ConcurrentTaskExecutor(max_concurrency=max_concurrency)
    
    orchestrator = BatchProcessingOrchestrator(
        url_processor,
        progress_notifier,
        result_aggregator,
        task_executor,
        lifecycle_manager
    )

    await orchestrator.process_batch(urls=urls)