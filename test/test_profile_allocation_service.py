import pytest
from unittest.mock import AsyncMock
from app.services.profile_allocation_service import ProfileAllocationService


class TestProfileAllocationService:
    
    @pytest.mark.asyncio
    async def test_pair_urls_with_profile_sufficient_profiles(self, mock_multi_login_service):
        """Test pairing when enough profiles exist"""

        service = ProfileAllocationService(multi_login_service=mock_multi_login_service)
        urls = ["https://example.com", "https://test.com", "https://demo.com"]
        
        result = await service.pair_urls_with_profile(urls=urls, max_profiles=2)
        
        assert len(result) == 3
        assert all(isinstance(pair, tuple) for pair in result)
        assert result[0][0] == "https://example.com"
        assert result[1][0] == "https://test.com"
        assert result[2][0] == "https://demo.com"
        
        mock_multi_login_service.profile_manager.create_profile.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_pair_urls_with_profile_insufficient_profiles(self, mock_multi_login_service):
        """Test pairing when profiles need to be created"""

        mock_multi_login_service.profile_manager.get_profile_ids = AsyncMock(
            side_effect=[
                ["profile_1"],
                ["profile_1", "profile_2", "profile_3"]
            ]
        )
        
        service = ProfileAllocationService(multi_login_service=mock_multi_login_service)
        urls = ["https://example.com", "https://test.com"]
        
        result = await service.pair_urls_with_profile(urls=urls, max_profiles=3)
        
        assert len(result) == 2
        assert mock_multi_login_service.profile_manager.create_profile.call_count == 2
    
    @pytest.mark.asyncio
    async def test_pair_urls_invalid_max_profiles(self, mock_multi_login_service):
        """Test that invalid max_profiles raises ValueError"""

        service = ProfileAllocationService(multi_login_service=mock_multi_login_service)
        urls = ["https://example.com"]
        
        with pytest.raises(ValueError, match="max_profiles must be greater than 0"):
            await service.pair_urls_with_profile(urls=urls, max_profiles=0)
    
    @pytest.mark.asyncio
    async def test_pair_urls_round_robin_distribution(self, mock_multi_login_service):
        """Test round-robin distribution of profiles"""

        service = ProfileAllocationService(multi_login_service=mock_multi_login_service)
        urls = [f"https://example{i}.com" for i in range(6)]
        
        result = await service.pair_urls_with_profile(urls=urls, max_profiles=2)
        
        assert len(result) == 6

        profile_ids = [pair[1] for pair in result]
        assert profile_ids[0] == profile_ids[2] == profile_ids[4]
        assert profile_ids[1] == profile_ids[3] == profile_ids[5]