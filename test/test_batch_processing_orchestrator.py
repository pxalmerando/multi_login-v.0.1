import pytest
from app.services.batch_processing_orchestrator import BatchProcessingOrchestrator
from app.models.schemas.processing_results import ProcessingResult
from unittest.mock import AsyncMock, Mock

class TestBatchProcessingOrchestrator:
    
    @pytest.mark.asyncio
    async def test_process_batch_empty_urls(self, mock_multi_login_service):
        """Test processing with empty URL list"""
        
        notifier = AsyncMock()
        profile_allocator = AsyncMock()
        
        orchestrator = BatchProcessingOrchestrator(
            multi_login_service=mock_multi_login_service,
            notifier=notifier,
            max_concurrency=3,
            profile_allocator=profile_allocator
        )
        
        
        result = await orchestrator.process_batch([])
        
        
        assert result.total_urls == 0
        assert result.successful_urls == 0
        assert result.failed_urls == 0
        notifier.notify_error.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_process_batch_successful(self, mock_multi_login_service):
        """Test successful batch processing"""
        
        notifier = AsyncMock()
        profile_allocator = AsyncMock()
        profile_allocator.pair_urls_with_profile = AsyncMock(return_value=[
            ("https://example.com", "profile_1"),
            ("https://test.com", "profile_2")
        ])
        
        orchestrator = BatchProcessingOrchestrator(
            multi_login_service=mock_multi_login_service,
            notifier=notifier,
            max_concurrency=2,
            profile_allocator=profile_allocator
        )
        
        
        orchestrator._process_single_with_profile = AsyncMock(
            return_value=ProcessingResult(
                success=True,
                url="https://example.com",
                web_title="Test Page"
            )
        )
        
        
        result = await orchestrator.process_batch(["https://example.com", "https://test.com"])
        
        
        assert result.total_urls == 2
        assert result.successful_urls == 2
        assert result.failed_urls == 0
        notifier.notify_batch_started.assert_called_once()
        notifier.notify_batch_completed.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_process_batch_with_failures(self, mock_multi_login_service):
        """Test batch processing with some failures"""
        
        notifier = AsyncMock()
        profile_allocator = AsyncMock()
        profile_allocator.pair_urls_with_profile = AsyncMock(return_value=[
            ("https://example.com", "profile_1"),
            ("https://fail.com", "profile_2")
        ])
        
        orchestrator = BatchProcessingOrchestrator(
            multi_login_service=mock_multi_login_service,
            notifier=notifier,
            max_concurrency=2,
            profile_allocator=profile_allocator
        )
        
        
        def mock_process(url, profile_id):
            if "fail" in url:
                return ProcessingResult(
                    success=False,
                    url=url,
                    error_message="Failed to process"
                )
            return ProcessingResult(
                success=True,
                url=url,
                web_title="Test Page"
            )
        
        orchestrator._process_single_with_profile = AsyncMock(side_effect=mock_process)
        
        
        result = await orchestrator.process_batch(["https://example.com", "https://fail.com"])
        
        
        assert result.total_urls == 2
        assert result.successful_urls == 1
        assert result.failed_urls == 1