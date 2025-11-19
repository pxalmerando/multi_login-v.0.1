import pytest
from unittest.mock import AsyncMock, Mock
from app.adapters.websocket_notifier import WebSocketNotifier
from app.models.schemas.processing_results import ProcessingResult
from app.services.batch_processing_orchestrator import BatchProcessingOrchestrator
from app.services.multi_login_service import MultiLoginService
from app.services.profile_allocation_service import ProfileAllocationService

class TestBatchProcessingOrchestrator:
    """Test BatchProcessingOrchestrator - coordinates entire batch processing workflow"""
    
    @pytest.fixture
    def mock_multi_login_service(self):
        mock = Mock()
        mock.get_folder_id = AsyncMock(return_value="folder-123")
        return mock
    
    @pytest.fixture
    def mock_notifier(self):
        mock = Mock()
        mock.notify_batch_started = AsyncMock()
        mock.notify_processing = AsyncMock()
        mock.notify_error = AsyncMock()
        mock.notify_completed = AsyncMock()
        mock.notify_batch_completed = AsyncMock()
        return mock
    
    @pytest.fixture
    def mock_profile_allocator(self):
        mock = Mock()
        mock.acquire_profile = AsyncMock()
        mock.release_profile = AsyncMock()
        mock.delete_profile = AsyncMock()
        return mock
    
    @pytest.fixture
    def orchestrator(self, mock_multi_login_service:MultiLoginService, mock_notifier:WebSocketNotifier, mock_profile_allocator:ProfileAllocationService):
        return BatchProcessingOrchestrator(
            multi_login_service=mock_multi_login_service,
            notifier=mock_notifier,
            max_concurrency=3,
            profile_allocator=mock_profile_allocator
        )
    
    @pytest.mark.asyncio
    async def test_process_batch_successful(self, orchestrator:BatchProcessingOrchestrator, mock_notifier:WebSocketNotifier, mock_profile_allocator:ProfileAllocationService):
        """Test successful batch processing of all URLs"""
        
        orchestrator.url_processor.process_with_profile = AsyncMock(
            return_value=ProcessingResult(
                success=True,
                url="https://example.com",
                captcha_detected=False
            )
        )
        orchestrator.lifecycle_manager.acquire_profile = AsyncMock(return_value="profile-123")
        
        
        urls = ["https://example1.com", "https://example2.com", "https://example3.com"]
        batch_result = await orchestrator.process_batch(urls)
        
        
        assert batch_result.total_urls == 3
        assert batch_result.successful_urls == 3
        assert batch_result.failed_urls == 0
        
        
        mock_notifier.notify_batch_started.assert_called_once()
        mock_notifier.notify_batch_completed.assert_called_once_with(
            total_urls=3, successful_urls=3, failed_urls=0
        )
        
        
        mock_profile_allocator.release_profile.assert_called()
        mock_profile_allocator.delete_profile.assert_not_called()

    @pytest.mark.asyncio
    async def test_process_batch_with_captcha(self, orchestrator:BatchProcessingOrchestrator, mock_notifier:WebSocketNotifier):
        """Test batch processing with CAPTCHA detection"""
        
        orchestrator.url_processor.process_with_profile = AsyncMock(
            return_value=ProcessingResult(
                success=False,
                url="https://example.com",
                captcha_detected=True
            )
        )

        orchestrator.lifecycle_manager.acquire_profile = AsyncMock(return_value="profile-123")
        
        
        urls = ["https://example1.com"]
        batch_result = await orchestrator.process_batch(urls)
        
        
        assert batch_result.successful_urls == 0
        assert batch_result.failed_urls == 1
        
        
        mock_notifier.notify_error.assert_called_once_with("CAPTCHA detected for URL: https://example1.com")

    @pytest.mark.asyncio
    async def test_process_batch_profile_acquisition_fails(self, orchestrator):
        """Test when profile acquisition fails for some URLs"""
        
        orchestrator.lifecycle_manager.acquire_profile = AsyncMock()
        orchestrator.lifecycle_manager.acquire_profile.side_effect = [
            "profile-123",  
            None,           
            "profile-456"   
        ]
        
        orchestrator.url_processor.process_with_profile = AsyncMock(
            return_value=ProcessingResult(success=True, url="https://example.com")
        )
        
        
        urls = ["https://example1.com", "https://example2.com", "https://example3.com"]
        batch_result = await orchestrator.process_batch(urls)
        
        
        assert batch_result.total_urls == 3
        assert batch_result.successful_urls == 2  
        assert batch_result.failed_urls == 1

    @pytest.mark.asyncio
    async def test_process_batch_empty(self, orchestrator, mock_notifier):
        """Test processing empty URL list"""
        
        batch_result = await orchestrator.process_batch([])
        
        
        assert batch_result.total_urls == 0
        assert batch_result.successful_urls == 0
        assert batch_result.failed_urls == 0
        
        
        mock_notifier.notify_error.assert_called_once_with("No URLs provided")

    @pytest.mark.asyncio
    async def test_process_single_url_exception(self, orchestrator):
        """Test exception handling in single URL processing"""
        # Setup: Mock the URLProcessor instance to raise an exception
        mock_url_processor = AsyncMock()
        mock_url_processor.process_with_profile.side_effect = Exception("Unexpected error")
        orchestrator.url_processor = mock_url_processor  # Replace the real instance with mock
        
        orchestrator.lifecycle_manager.acquire_profile = AsyncMock(return_value="profile-123")
        orchestrator.lifecycle_manager.cleanup_on_error = AsyncMock()  # Mock cleanup method
        
        # Execute: Process single URL
        result = await orchestrator._process_single_url("https://example.com", "folder-123")
        
        # Verify: Exception converted to ProcessingResult
        assert result.success is False
        assert "Unexpected error" in result.error_message
        assert result.url == "https://example.com"
        
        # Verify: Emergency cleanup was called
        orchestrator.lifecycle_manager.cleanup_on_error.assert_called_once_with("profile-123")