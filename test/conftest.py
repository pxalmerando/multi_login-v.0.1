import pytest
from unittest.mock import Mock, AsyncMock
from fastapi import WebSocket
from app.services.multi_login_service import MultiLoginService
from app.multilogin.schemas import MultiLoginProfileSession

@pytest.fixture
def mock_websocket():
    
    ws = AsyncMock(spec=WebSocket)
    ws.send_json = AsyncMock()
    ws.receive_json = AsyncMock()
    ws.accept = AsyncMock()
    ws.close = AsyncMock()
    return ws

@pytest.fixture
def mock_multi_login_service():
    
    service = AsyncMock(spec=MultiLoginService)
    service.initialize = AsyncMock()
    service.get_folder_id = AsyncMock(return_value="folder_123")
    service.start_profile = AsyncMock(return_value="http://localhost:4444")
    service.stop_profile = AsyncMock()
    service.delete_profile = AsyncMock()
    service.cleanup = AsyncMock()
    
    
    service.profile_manager = AsyncMock()
    service.profile_manager.get_profile_ids = AsyncMock(return_value=["profile_1", "profile_2", "profile_3"])
    service.profile_manager.create_profile = AsyncMock(return_value={"id": "new_profile"})
    service.profile_manager.delete_profile = AsyncMock()
    
    
    service.profile_registry = Mock()
    service.profile_registry.get_session = Mock(return_value=None)
    service.profile_registry.is_running = Mock(return_value=False)
    service.profile_registry.register = Mock()
    service.profile_registry.unregister = Mock()
    service.profile_registry.get_all_sessions = Mock(return_value=[])
    service.profile_registry.clear = Mock()
    
    return service

@pytest.fixture
def sample_profile_session():
    
    return MultiLoginProfileSession(
        status_code=200,
        profile_id="test_profile_123",
        selenium_port="4444"
    )

@pytest.fixture
def sample_urls():
    
    return [
        "https://example.com",
        "https://test.com",
        "https://demo.com"
    ]