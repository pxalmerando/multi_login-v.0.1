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
    max_concurrency: int = 5
):
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