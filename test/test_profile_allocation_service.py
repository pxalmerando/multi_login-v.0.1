import pytest
import asyncio
import logging

from unittest.mock import AsyncMock, Mock, MagicMock, patch

from app.database.profile_repository import ProfileRepository
from app.services.profile_state_manager import ProfileStateManager
from app.services.profile_allocation_service import ProfileAllocationService

logger = logging.getLogger(__name__)

class TestProfileAllocationService:

    @pytest.fixture
    def mock_repository(self):
        mock = Mock(spec=ProfileRepository)
        mock.fetch_all_profiles = AsyncMock()
        mock.create_profile = AsyncMock()
        mock.delete_profile = AsyncMock()
        return mock
    
    @pytest.fixture
    def mock_state_manager(self):
        """Mock ProfileStateManager"""
        mock = Mock(spec=ProfileStateManager)
        mock.is_cache_dirty = Mock()
        mock.update_cache = Mock()
        mock.get_cached_profiles = Mock()
        mock.get_available_profiles = Mock()
        mock.mark_in_use = Mock()
        mock.mark_available = Mock()
        mock.mark_deleted = Mock()
        mock.add_to_pool = Mock()
        mock.get_status = Mock()
        return mock
    
    @pytest.fixture
    def allocation_service(self, mock_repository:ProfileRepository, mock_state_manager:ProfileStateManager):
        """Create ProfileAllocationService with mocked dependencies"""
        return ProfileAllocationService(
            repository=mock_repository,
            state_manager=mock_state_manager,
            max_profiles=5
        )
    
    @pytest.mark.asyncio
    async def test_acquire_profile_existing_available(self, allocation_service:ProfileAllocationService, mock_state_manager:ProfileStateManager):
        """Test acquiring an existing available profile"""
        
        mock_state_manager.is_cache_dirty.return_value = False
        mock_state_manager.get_available_profiles.return_value = ["profile1", "profile2"]
        mock_state_manager.get_cached_profiles.return_value = ["profile1", "profile2"]
        
        profile_id = await allocation_service.acquire_profile("folder1")
        
        assert profile_id in ["profile1", "profile2"]
        
        mock_state_manager.mark_in_use.assert_called_once_with(profile_id)

    @pytest.mark.asyncio
    async def test_acquire_profile_refreshes_cache_when_dirty(self, allocation_service:ProfileAllocationService, mock_state_manager:ProfileStateManager, mock_repository:ProfileRepository):
        """Test that cache is refreshed when dirty"""
        
        mock_state_manager.is_cache_dirty.return_value = True
        mock_repository.fetch_all_profiles.return_value = ["profile1", "profile2"]
        mock_state_manager.get_available_profiles.return_value = ["profile1", "profile2"]
        mock_state_manager.get_cached_profiles.return_value = ["profile1", "profile2"]
        
        
        profile_id = await allocation_service.acquire_profile("folder1")
        
        
        mock_repository.fetch_all_profiles.assert_called_once_with("folder1")
        mock_state_manager.update_cache.assert_called_once_with(["profile1", "profile2"])
        
        
        assert profile_id in ["profile1", "profile2"]
    
    @pytest.mark.asyncio
    async def test_acquire_profile_creates_new_when_none_available(self, allocation_service:ProfileAllocationService, mock_repository:ProfileRepository, mock_state_manager:ProfileStateManager):
        """Test creating new profile when no available profiles exist"""
        
        mock_state_manager.is_cache_dirty.return_value = False
        mock_state_manager.get_available_profiles.return_value = []  
        mock_state_manager.get_cached_profiles.return_value = ["profile1", "profile2"]  
        
        
        mock_repository.create_profile.return_value = "new-profile-123"
        
        
        profile_id = await allocation_service.acquire_profile("folder1")
        
        
        assert profile_id == "new-profile-123"
        mock_repository.create_profile.assert_called_once_with(
            folder_id="folder1",
            name="Profile 2"  
        )
        
        
        mock_state_manager.add_to_pool.assert_called_once_with("new-profile-123")
        mock_state_manager.mark_in_use.assert_called_once_with("new-profile-123")

    @pytest.mark.asyncio
    async def test_acquire_profile_respects_max_limit(self, allocation_service:ProfileAllocationService, mock_state_manager:ProfileStateManager):
        """Test that service respects maximum profile limit"""
        
        mock_state_manager.is_cache_dirty.return_value = False
        mock_state_manager.get_available_profiles.return_value = []  
        mock_state_manager.get_cached_profiles.return_value = ["p1", "p2", "p3", "p4", "p5"]  
        
        
        with patch('asyncio.sleep', new_callable=AsyncMock):
            
            profile_id = await allocation_service.acquire_profile("folder1", timeout=0.5)
        
        
        assert profile_id is None

    @pytest.mark.asyncio
    async def test_acquire_profile_timeout(self, allocation_service:ProfileAllocationService, mock_state_manager:ProfileStateManager):
        """Test timeout when no profile becomes available"""
        
        mock_state_manager.is_cache_dirty.return_value = False
        mock_state_manager.get_available_profiles.return_value = []  
        mock_state_manager.get_cached_profiles.return_value = ["p1", "p2", "p3", "p4", "p5"]
        
        
        with patch('asyncio.get_event_loop') as mock_loop:
            mock_loop.return_value.time.side_effect = [0, 10, 35]  
            
            
            profile_id = await allocation_service.acquire_profile("folder1", timeout=30.0)
        
        
        assert profile_id is None

    @pytest.mark.asyncio
    async def test_release_profile_success(self, allocation_service:ProfileAllocationService, mock_state_manager:ProfileStateManager):
        """Test successfully releasing a profile"""
        
        
        profile_id = "profile1"
        
        
        async with allocation_service._pool_lock:
            allocation_service._profile_locks[profile_id] = asyncio.Lock()
            await allocation_service._profile_locks[profile_id].acquire()
        
        
        await allocation_service.release_profile(profile_id)
        
        
        mock_state_manager.mark_available.assert_called_once_with(profile_id)
        
        
        lock = allocation_service._profile_locks[profile_id]
        
        acquired = await asyncio.wait_for(lock.acquire(), timeout=0.1)
        assert acquired is True  

    @pytest.mark.asyncio
    async def test_release_profile_none(self, allocation_service, caplog):
        """Test releasing a None profile (error case)"""
        caplog.set_level(logging.ERROR)
        
        await allocation_service.release_profile(None)
        
        assert "Attempted to release None profile" in caplog.text

    @pytest.mark.asyncio
    async def test_delete_profile_success(self, allocation_service:ProfileAllocationService, mock_repository:ProfileRepository, mock_state_manager:ProfileStateManager):
        """Test successfully deleting a profile"""
        
        profile_id = "profile-to-delete"
        
        async with allocation_service._pool_lock:
            allocation_service._profile_locks[profile_id] = asyncio.Lock()
            await allocation_service._profile_locks[profile_id].acquire()
        
        
        await allocation_service.delete_profile(profile_id)
        
        
        mock_state_manager.mark_deleted.assert_called_once_with(profile_id)
        
        
        assert profile_id not in allocation_service._profile_locks
        
        
        mock_repository.delete_profile.assert_called_once_with(profile_id)

    @pytest.mark.asyncio
    async def test_delete_profile_none(self, allocation_service, caplog):
        """Test deleting a None profile (error case)"""
        caplog.set_level(logging.ERROR)
        
        await allocation_service.delete_profile(None)
        
        assert "Attempted to delete None profile" in caplog.text
        
    @pytest.mark.asyncio
    async def test_concurrent_acquisitions(self, allocation_service, mock_state_manager):
        """Test multiple concurrent acquisition attempts"""
        
        mock_state_manager.is_cache_dirty.return_value = False
        mock_state_manager.get_available_profiles.return_value = ["profile1"]
        mock_state_manager.get_cached_profiles.return_value = ["profile1"]
        
        
        results = await asyncio.gather(
            allocation_service.acquire_profile("folder1"),
            allocation_service.acquire_profile("folder1"),
            allocation_service.acquire_profile("folder1"),
            return_exceptions=True
        )
        
        
        
        
        assert all(not isinstance(r, Exception) for r in results)

    @pytest.mark.asyncio
    async def test_acquire_after_release(self, allocation_service:ProfileAllocationService, mock_state_manager:ProfileStateManager):
        """Test that released profiles become available again"""
        profile_id = "profile1"
        
        
        mock_state_manager.is_cache_dirty.return_value = False
        mock_state_manager.get_available_profiles.return_value = [profile_id]
        mock_state_manager.get_cached_profiles.return_value = [profile_id]
        
        acquired_id = await allocation_service.acquire_profile("folder1")
        assert acquired_id == profile_id
        
        
        await allocation_service.release_profile(profile_id)
        
        
        mock_state_manager.get_available_profiles.return_value = [profile_id]
        
        
        acquired_again = await allocation_service.acquire_profile("folder1")
        assert acquired_again == profile_id

    @pytest.mark.asyncio
    async def test_get_pool_status(self, allocation_service:ProfileAllocationService, mock_state_manager:ProfileStateManager):
        """Test getting pool status"""
        expected_status = {
            "total_profiles": 3,
            "in_use": 1,
            "available": 2,
            "deleted": 0,
            "profiles": ["p1", "p2", "p3"]
        }
        mock_state_manager.get_status.return_value = expected_status
        
        status = allocation_service.get_pool_status()
        
        assert status == expected_status
        mock_state_manager.get_status.assert_called_once()