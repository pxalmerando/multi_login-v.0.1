import pytest
from unittest.mock import AsyncMock, Mock
from app.models.schemas.processing_results import ProcessingResult
from app.services.multi_login_service import MultiLoginService
from app.services.url_processing_service import URLProcessingService
from app.services.url_processor import URLProcessor

class TestURLProcessor:
    """Test URLProcessor - handles browser automation for single URLs"""
    
    @pytest.fixture
    def mock_multi_login_service(self):
        mock = Mock()
        mock.start_profile = AsyncMock()
        return mock
    
    @pytest.fixture
    def mock_url_processing_service(self):
        mock = Mock()
        mock.process_url = AsyncMock()
        return mock
    
    @pytest.fixture
    def url_processor(self, mock_multi_login_service:MultiLoginService, mock_url_processing_service):
        return URLProcessor(mock_multi_login_service, mock_url_processing_service)

    @pytest.mark.asyncio
    async def test_process_successful_url(self, url_processor:URLProcessor, mock_multi_login_service:MultiLoginService, mock_url_processing_service:URLProcessingService):
        """Test successfully processing a URL through browser automation"""
        
        mock_multi_login_service.start_profile.return_value = "http://localhost:4444"
        mock_url_processing_service.process_url.return_value = ProcessingResult(
            success=True,
            url="https://example.com",
            captcha_detected=False
        )
        
        
        result = await url_processor.process_with_profile(
            url="https://example.com",
            profile_id="profile-123"
        )
        
        
        assert result.success is True
        assert result.url == "https://example.com"
        assert result.captcha_detected is False
        
        
        mock_multi_login_service.start_profile.assert_called_once_with("profile-123")
        
        
        mock_url_processing_service.process_url.assert_called_once_with(
            url="https://example.com",
            selenium_url="http://localhost:4444"
        )

    @pytest.mark.asyncio
    async def test_process_browser_start_fails(self, url_processor:URLProcessor, mock_multi_login_service:MultiLoginService):
        """Test when browser fails to start"""
        
        mock_multi_login_service.start_profile.return_value = None
        
        
        result = await url_processor.process_with_profile(
            url="https://example.com",
            profile_id="profile-123"
        )
        
        
        assert result.success is False
        assert "Failed to start browser profile" in result.error_message
        assert result.url == "https://example.com"

    @pytest.mark.asyncio
    async def test_process_captcha_detected(self, url_processor:URLProcessor, mock_multi_login_service:MultiLoginService, mock_url_processing_service:URLProcessingService):
        """Test when CAPTCHA is detected during processing"""
        
        mock_multi_login_service.start_profile.return_value = "http://localhost:4444"
        mock_url_processing_service.process_url.return_value = ProcessingResult(
            success=False,
            url="https://example.com",
            captcha_detected=True
        )
        
        
        result = await url_processor.process_with_profile(
            url="https://example.com", 
            profile_id="profile-123"
        )
        
        
        assert result.success is False
        assert result.captcha_detected is True
        assert "CAPTCHA detected" in result.error_message

    @pytest.mark.asyncio
    async def test_process_unexpected_exception(self, url_processor:URLProcessor, mock_multi_login_service:MultiLoginService):
        """Test when unexpected exception occurs during processing"""
        
        mock_multi_login_service.start_profile.side_effect = Exception("Network error")
        
        
        result = await url_processor.process_with_profile(
            url="https://example.com",
            profile_id="profile-123"
        )
        
        
        assert result.success is False
        assert "Network error" in result.error_message
        assert result.url == "https://example.com"