import pytest
from app.api.websocket.websocket_handlers import process_multiple_urls
from unittest.mock import AsyncMock, patch

class TestWebSocketHandlers:
    
    @pytest.mark.asyncio
    async def test_process_multiple_urls(self, mock_websocket, mock_multi_login_service):
        """Test processing multiple URLs through WebSocket"""
        
        profile_allocator = AsyncMock()
        profile_allocator.pair_urls_with_profile = AsyncMock(return_value=[
            ("https://example.com", "profile_1")
        ])
        
        with patch('app.api.websocket.websocket_handlers.BatchProcessingOrchestrator') as MockOrchestrator:
            mock_orchestrator = AsyncMock()
            MockOrchestrator.return_value = mock_orchestrator
            
            
            await process_multiple_urls(
                websocket=mock_websocket,
                urls=["https://example.com"],
                processor=mock_multi_login_service,
                profile_allocator=profile_allocator,
                max_concurrency=3
            )
            
            
            MockOrchestrator.assert_called_once()
            mock_orchestrator.process_batch.assert_called_once()