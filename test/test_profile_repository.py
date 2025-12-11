import pytest
from unittest.mock import AsyncMock, MagicMock
import logging

from app.multilogin.repositories.profile_repository import ProfileRepository
from app.multilogin.application.multi_login_service import MultiLoginService

logger = logging.getLogger(__name__)

class TestProfileRepository:
    """Test suite for ProfileRepository - focusing on API interaction"""
    
    @pytest.fixture
    def mock_multi_login_service(self):
        """Create a mock MultiLoginService with all required attributes"""
        
        mock_service = MagicMock()
        
        
        mock_service.profile_manager = MagicMock()
        mock_service.profile_manager.create_profile = AsyncMock()
        mock_service.profile_manager.get_profile_ids = AsyncMock()
        mock_service.delete_profile = AsyncMock()
        
        return mock_service
    
    @pytest.fixture
    def repository(self, mock_multi_login_service:MultiLoginService):
        """Create ProfileRepository with mocked service"""
        return ProfileRepository(mock_multi_login_service)

    
    @pytest.mark.asyncio
    async def test_create_profile_success(self, repository:ProfileRepository, mock_multi_login_service:MultiLoginService):
        """Test successful profile creation"""
        
        mock_multi_login_service.profile_manager.create_profile.return_value = {
            "data": {
                "ids": ["new-profile-123"]
            }
        }
        
        
        profile_id = await repository.create_profile("folder1", "Test Profile")
        
        
        assert profile_id == "new-profile-123"
        
        
        mock_multi_login_service.profile_manager.create_profile.assert_called_once_with(
            folder_id="folder1",
            name="Test Profile"
        )

    @pytest.mark.asyncio
    async def test_create_profile_no_data(self, repository:ProfileRepository, mock_multi_login_service:MultiLoginService):
        """Test profile creation when API returns no data"""
        mock_multi_login_service.profile_manager.create_profile.return_value = {"data": None}
        
        profile_id = await repository.create_profile("folder1", "Test Profile")
        assert profile_id is None

    @pytest.mark.asyncio
    async def test_create_profile_empty_ids(self, repository:ProfileRepository, mock_multi_login_service:MultiLoginService):
        """Test profile creation when API returns empty IDs list"""
        mock_multi_login_service.profile_manager.create_profile.return_value = {
            "data": {
                "ids": []
            }
        }
        
        profile_id = await repository.create_profile("folder1", "Test Profile")
        assert profile_id is None

    @pytest.mark.asyncio
    async def test_create_profile_api_exception(self, repository:ProfileRepository, mock_multi_login_service:MultiLoginService):
        """Test profile creation when API raises an exception"""
        mock_multi_login_service.profile_manager.create_profile.side_effect = Exception("API timeout")
        
        profile_id = await repository.create_profile("folder1", "Test Profile")
        assert profile_id is None

    
    @pytest.mark.asyncio
    async def test_fetch_all_profiles_success(self, repository:ProfileRepository, mock_multi_login_service:MultiLoginService):
        """Test successfully fetching all profiles"""
        expected_profiles = ["profile1", "profile2", "profile3"]
        mock_multi_login_service.profile_manager.get_profile_ids.return_value = expected_profiles
        
        profiles = await repository.fetch_all_profiles("folder1")
        assert profiles == expected_profiles
        mock_multi_login_service.profile_manager.get_profile_ids.assert_called_once_with(
            folder_id="folder1"
        )

    @pytest.mark.asyncio
    async def test_fetch_all_profiles_empty(self, repository:ProfileRepository, mock_multi_login_service:MultiLoginService):
        """Test fetching profiles from empty folder"""
        mock_multi_login_service.profile_manager.get_profile_ids.return_value = []
        
        profiles = await repository.fetch_all_profiles("folder1")
        assert profiles == []

    @pytest.mark.asyncio
    async def test_fetch_all_profiles_api_exception(self, repository:ProfileRepository, mock_multi_login_service:MultiLoginService):
        """Test fetching profiles when API fails"""
        mock_multi_login_service.profile_manager.get_profile_ids.side_effect = Exception("Network error")
        
        profiles = await repository.fetch_all_profiles("folder1")
        assert profiles == []

    
    @pytest.mark.asyncio
    async def test_delete_profile_success(self, repository:ProfileRepository, mock_multi_login_service:MultiLoginService):
        """Test successful profile deletion"""
        mock_multi_login_service.delete_profile.return_value = None  
        
        result = await repository.delete_profile("profile-to-delete")
        assert result is True
        mock_multi_login_service.delete_profile.assert_called_once_with("profile-to-delete")

    @pytest.mark.asyncio
    async def test_delete_profile_api_exception(self, repository:ProfileRepository, mock_multi_login_service:MultiLoginService):
        """Test profile deletion when API fails"""
        mock_multi_login_service.delete_profile.side_effect = Exception("Profile not found")
        
        result = await repository.delete_profile("non-existent-profile")
        assert result is False

    
    @pytest.mark.asyncio
    async def test_logging_on_success(self, repository:ProfileRepository, mock_multi_login_service:MultiLoginService, caplog):
        """Test that successful operations are logged"""
        import logging
        caplog.set_level(logging.INFO)
        
        
        mock_multi_login_service.profile_manager.create_profile.return_value = {
            "data": {"ids": ["new-profile"]}
        }
        await repository.create_profile("folder1", "Test Profile")
        assert "Created profile new-profile" in caplog.text
        
        
        mock_multi_login_service.profile_manager.get_profile_ids.return_value = ["p1", "p2"]
        await repository.fetch_all_profiles("folder1")
        assert "Fetched 2 profiles" in caplog.text
        
        
        mock_multi_login_service.delete_profile.return_value = None
        await repository.delete_profile("old-profile")
        assert "Deleted profile old-profile" in caplog.text

    @pytest.mark.asyncio
    async def test_logging_on_errors(self, repository:ProfileRepository, mock_multi_login_service:MultiLoginService, caplog):
        """Test that errors are logged appropriately"""
        import logging
        caplog.set_level(logging.ERROR)
        
        
        mock_multi_login_service.profile_manager.create_profile.side_effect = Exception("API down")
        await repository.create_profile("folder1", "Test Profile")
        assert "Creation error" in caplog.text
        
        
        mock_multi_login_service.profile_manager.get_profile_ids.side_effect = Exception("Network issue")
        await repository.fetch_all_profiles("folder1")
        assert "Fetch error" in caplog.text
        
        
        mock_multi_login_service.delete_profile.side_effect = Exception("Not found")
        await repository.delete_profile("missing-profile")
        assert "Delete error for missing-profile" in caplog.text