

import pytest
import asyncio
from unittest.mock import AsyncMock, Mock

from app.services.profile_lifecycle_manager import ProfileLifecycleManager

class TestProfileLifecycleManager:
    """Test ProfileLifecycleManager - decides when to reuse vs delete profiles"""
    
    @pytest.fixture
    def mock_profile_allocator(self):
        mock = Mock()
        mock.acquire_profile = AsyncMock()
        mock.release_profile = AsyncMock()
        mock.delete_profile = AsyncMock()
        return mock
    
    @pytest.fixture
    def lifecycle_manager(self, mock_profile_allocator):
        return ProfileLifecycleManager(mock_profile_allocator)

    @pytest.mark.asyncio
    async def test_acquire_profile_success(self, lifecycle_manager, mock_profile_allocator):
        """Test successfully acquiring a profile"""
        
        mock_profile_allocator.acquire_profile.return_value = "profile-123"
        
        
        profile_id = await lifecycle_manager.acquire_profile("folder-1")
        
        
        assert profile_id == "profile-123"
        mock_profile_allocator.acquire_profile.assert_called_once_with("folder-1")

    @pytest.mark.asyncio
    async def test_acquire_profile_failure(self, lifecycle_manager, mock_profile_allocator):
        """Test when profile acquisition fails"""
        
        mock_profile_allocator.acquire_profile.return_value = None
        
        
        profile_id = await lifecycle_manager.acquire_profile("folder-1")
        
        
        assert profile_id is None

    @pytest.mark.asyncio
    async def test_acquire_profile_exception(self, lifecycle_manager, mock_profile_allocator, caplog):
        """Test when profile acquisition throws exception"""
        
        mock_profile_allocator.acquire_profile.side_effect = Exception("Allocation service down")
        caplog.set_level("ERROR")
        
        
        profile_id = await lifecycle_manager.acquire_profile("folder-1")
        
        
        assert profile_id is None
        assert "Failed to acquire profile" in caplog.text

    @pytest.mark.asyncio
    async def test_handle_success_releases_profile(self, lifecycle_manager, mock_profile_allocator):
        """Test releasing profile after successful processing"""
        
        await lifecycle_manager.handle_success("profile-123")
        
        
        mock_profile_allocator.release_profile.assert_called_once_with("profile-123")

    @pytest.mark.asyncio
    async def test_handle_failure_deletes_profile(self, lifecycle_manager, mock_profile_allocator, caplog):
        """Test deleting profile after failure (e.g., CAPTCHA)"""
        caplog.set_level("WARNING")
        
        
        await lifecycle_manager.handle_failure("profile-123", "CAPTCHA detected")
        
        
        mock_profile_allocator.delete_profile.assert_called_once_with("profile-123")
        assert "Deleted profile profile-123 due to: CAPTCHA detected" in caplog.text

    @pytest.mark.asyncio
    async def test_cleanup_on_error_deletes_profile(self, lifecycle_manager, mock_profile_allocator):
        """Test emergency cleanup when exception occurs"""
        
        await lifecycle_manager.cleanup_on_error("profile-123")
        
        
        mock_profile_allocator.delete_profile.assert_called_once_with("profile-123")

    @pytest.mark.asyncio
    async def test_cleanup_on_error_none_profile(self, lifecycle_manager, mock_profile_allocator):
        """Test cleanup when no profile was acquired"""
        
        await lifecycle_manager.cleanup_on_error(None)
        
        
        mock_profile_allocator.delete_profile.assert_not_called()