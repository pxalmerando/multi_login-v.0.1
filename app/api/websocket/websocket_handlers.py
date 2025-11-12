"""WebSocket handlers for processing URLs and managing connections."""
from fastapi import WebSocket
from app.services.multi_login_service import MultiLoginService
from app.services.batch_processing_orchestrator import BatchProcessingOrchestrator
from app.adapters.websocket_notifier import WebSocketNotifier
from app.services.profile_allocation_service import ProfileAllocationService
async def process_multiple_urls(
    websocket: WebSocket,
    urls: list[str],
    processor: MultiLoginService,
    profile_allocator: ProfileAllocationService,
    max_concurrency: int = 3
):
    """Process multiple URLs using batch processing with WebSocket notifications.

    Args:
        websocket (WebSocket): The WebSocket connection for sending status updates.
        urls (list[str]): List of URLs to process.
        processor (MultiLoginService): Service for handling multi-login operations.
        profile_allocator (ProfileAllocationService): Service for allocating browser profiles.
        max_concurrency (int): Maximum number of concurrent processing tasks. Defaults to 3.
    """
    notifier = WebSocketNotifier(
        websocket=websocket,
    )
    
    orchestrator = BatchProcessingOrchestrator(
        multi_login_service=processor,
        notifier=notifier,
        max_concurrency=max_concurrency,
        profile_allocator=profile_allocator
    )
    await orchestrator.process_batch(urls=urls)