import pytest
from app.services.multi_login_service import MultiLoginService
from unittest.mock import patch, AsyncMock, Mock


class TestMultiLoginService:
    
    @pytest.mark.asyncio
    async def test_start_profile_new_profile(self):
        """Test starting a new profile"""
        # Arrange
        with patch('app.services.multi_login_service.HttpClient') as mock_http:
            service = MultiLoginService()
            service._access_token = "test_token"
            service.headers = {"Authorization": "Bearer test_token"}
            service.profile_registry = Mock()
            service.profile_registry.get_session = Mock(return_value=None)
            service.profile_registry.register = Mock()
            
            service.http_launcher = AsyncMock()
            service.http_launcher.get = AsyncMock(return_value={
                "status": {
                    "http_code": 200,
                    "message": "4444"
                }
            })
            
            service.get_folder_id = AsyncMock(return_value="folder_123")
            
            # Act
            result = await service.start_profile("profile_123")
            
            # Assert
            assert result == "http://localhost:4444"
            service.profile_registry.register.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_start_profile_already_running(self):
        """Test starting an already running profile"""
        # Arrange
        service = MultiLoginService()
        existing_session = Mock()
        existing_session.selenium_url = "http://127.0.0.1:5555"
        
        service.profile_registry = Mock()
        service.profile_registry.get_session = Mock(return_value=existing_session)
        
        # Act
        result = await service.start_profile("profile_123")
        
        # Assert
        assert result == "http://127.0.0.1:5555"
    
    @pytest.mark.asyncio
    async def test_stop_profile_success(self):
        """Test stopping a running profile"""
        # Arrange
        service = MultiLoginService()
        service._access_token = "test_token"
        service.headers = {"Authorization": "Bearer test_token"}
        
        service.profile_registry = Mock()
        service.profile_registry.is_running = Mock(return_value=True)
        service.profile_registry.unregister = Mock()
        
        service.http_launcher = AsyncMock()
        service.http_launcher.get = AsyncMock()
        
        # Act
        await service.stop_profile("profile_123")
        
        # Assert
        service.profile_registry.unregister.assert_called_once_with("profile_123")
        service.http_launcher.get.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_stop_profile_not_running(self):
        """Test stopping a profile that's not running"""
        # Arrange
        service = MultiLoginService()
        service.profile_registry = Mock()
        service.profile_registry.is_running = Mock(return_value=False)
        
        # Act
        await service.stop_profile("profile_123")
        
        # Assert - should return early, no API call
        service.profile_registry.is_running.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_cleanup_multiple_profiles(self):
        """Test cleanup with multiple running profiles"""
        # Arrange
        service = MultiLoginService()
        service._access_token = "test_token"
        service.headers = {"Authorization": "Bearer test_token"}
        
        mock_sessions = [
            Mock(profile_id="profile_1"),
            Mock(profile_id="profile_2"),
        ]
        
        service.profile_registry = Mock()
        service.profile_registry.get_all_sessions = Mock(return_value=mock_sessions)
        service.profile_registry.is_running = Mock(return_value=True)
        service.profile_registry.unregister = Mock()
        service.profile_registry.clear = Mock()
        
        service.http_launcher = AsyncMock()
        service.http_launcher.get = AsyncMock()
        service._profile_locks = {}
        
        # Act
        await service.cleanup()
        
        # Assert
        assert service.http_launcher.get.call_count == 0
        service.profile_registry.clear.assert_called_once()