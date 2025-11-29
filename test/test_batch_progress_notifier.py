import pytest
import asyncio
from unittest.mock import AsyncMock, Mock
from app.models.schemas.processing_results import ProcessingResult
from app.services.batch_progress_notifier import BatchProgressNotifier

class TestBatchProgressNotifier:
    """Test BatchProgressNotifier - handles user notifications during batch processing"""
    
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
    def progress_notifier(self, mock_notifier):
        return BatchProgressNotifier(mock_notifier)

    @pytest.mark.asyncio
    async def test_notify_batch_start(self, progress_notifier, mock_notifier):
        """Test notifying when batch processing starts"""
        
        await progress_notifier.notify_batch_start(
            total_urls=100,
            max_concurrent=5
        )
        
        
        mock_notifier.notify_batch_started.assert_called_once_with(
            total_urls=100,
            max_concurrent=5
        )

    @pytest.mark.asyncio
    async def test_notify_url_processing(self, progress_notifier, mock_notifier):
        """Test notifying when specific URL processing starts"""
        
        await progress_notifier.notify_url_processing(
            url="https://example.com",
            step=2,
            total_steps=10
        )
        
        
        mock_notifier.notify_processing.assert_called_once_with(
            step=2,
            message="Processing URL: https://example.com",
            total_steps=10
        )

    @pytest.mark.asyncio
    async def test_notify_profile_started(self, progress_notifier, mock_notifier):
        """Test notifying when browser profile is ready"""
        
        await progress_notifier.notify_profile_started(
            selenium_url="http://localhost:4444",
            step=1,
            total_steps=3
        )
        
        
        mock_notifier.notify_processing.assert_called_once_with(
            message="Browser ready: http://localhost:4444",
            step=1,
            total_steps=3
        )

    @pytest.mark.asyncio
    async def test_notify_captcha_detected(self, progress_notifier, mock_notifier):
        """Test notifying when CAPTCHA is detected"""
        
        await progress_notifier.notify_captcha_detected("https://example.com")
        
        
        mock_notifier.notify_error.assert_called_once_with(
            "CAPTCHA detected for URL: https://example.com"
        )

    @pytest.mark.asyncio
    async def test_notify_url_completed(self, progress_notifier, mock_notifier):
        """Test notifying when URL processing completes"""
        
        result = ProcessingResult(
            success=True,
            url="https://example.com",
            metadata={"title": "Example Domain"}
        )
        
        
        await progress_notifier.notify_url_completed(result)
        
        
        mock_notifier.notify_completed.assert_called_once_with(
            message="URL processed successfully",
            data=result.to_dict()
        )

    @pytest.mark.asyncio
    async def test_notify_batch_complete(self, progress_notifier, mock_notifier):
        """Test notifying when entire batch completes"""
        
        await progress_notifier.notify_batch_complete(
            total=100,
            successful=85,
            failed=15
        )
        
        
        mock_notifier.notify_batch_completed.assert_called_once_with(
            successful_urls=85,
            total_urls=100,
            failed_urls=15
        )