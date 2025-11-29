from typing import List
import pytest
import logging

from app.services.profile_state_manager import ProfileStateManager


@pytest.fixture
def caplog(caplog):
    caplog.set_level(logging.INFO)
    return caplog

class TestProfileStateManager:

    @pytest.fixture
    def state_manager(self):
        return ProfileStateManager()
    

    def test_initial_state(self, state_manager: ProfileStateManager):

        assert state_manager.get_cached_profiles() == []

        assert state_manager.get_available_profiles() == []

        assert state_manager.is_cache_dirty() == True

        status = state_manager.get_status()

        assert status["total_profiles"] == 0
        assert status["in_use"] == 0
        assert status["available"] == 0
        assert status["deleted"] == 0


    def test_update_cache(self, state_manager: ProfileStateManager):
        profiles = [
            "p1",
            "p2",
            "p3",
        ]

        state_manager.update_cache(profiles)

        assert state_manager.get_cached_profiles() == profiles

        assert state_manager.is_cache_dirty() == False

    def test_update_cache_returns_copy(self, state_manager: ProfileStateManager):

        original_profiles = [
            "p1",
            "p2",
            "p3",
            "p4",
        ]

        state_manager.update_cache(original_profiles)

        cache = state_manager.get_cached_profiles()
        cache.append("person")

        assert state_manager.get_cached_profiles() == original_profiles

    def test_get_available_profiles_basic(self, state_manager: ProfileStateManager):

        profiles = [
            "p1",
            "p2",
            "p33"
        ]

        state_manager.update_cache(profiles)

        available = state_manager.get_available_profiles()

        assert available == profiles

    def test_get_available_profiles_exclude_in_use(self, state_manager: ProfileStateManager):


        profiles = [
            "p1",
            "p2",
            "p33"
        ]
        
        state_manager.update_cache(profiles)

        state_manager.mark_in_use("p2")

        available = state_manager.get_available_profiles()

        assert available == [
            "p1",
            "p33"
            ]
        
    def test_get_available_profiles_excludes_deleted(self, state_manager: ProfileStateManager):
        """Test that deleted profiles are excluded from available"""
        profiles = ["profile1", "profile2", "profile3"]
        state_manager.update_cache(profiles)
        
        
        state_manager.mark_deleted("profile1")
        
        available = state_manager.get_available_profiles()
        assert available == ["profile2", "profile3"]

    def test_get_available_profiles_excludes_both(self, state_manager: ProfileStateManager):
        """Test that profiles are excluded if either in-use OR deleted"""
        profiles = ["profile1", "profile2", "profile3", "profile4"]
        state_manager.update_cache(profiles)
        
        state_manager.mark_in_use("profile1")    
        state_manager.mark_deleted("profile2")   
        
        
        available = state_manager.get_available_profiles()
        assert available == ["profile3", "profile4"]

    def test_mark_in_use(self, state_manager: ProfileStateManager):
        """Test marking a profile as in-use"""
        state_manager.update_cache(["profile1", "profile2"])
        
        state_manager.mark_in_use("profile1")
        
        
        available = state_manager.get_available_profiles()
        assert "profile1" not in available
        assert "profile2" in available

    def test_mark_available(self, state_manager: ProfileStateManager):
        """Test marking a profile as available after use"""
        state_manager.update_cache(["profile1", "profile2"])
        state_manager.mark_in_use("profile1")
        
        
        state_manager.mark_available("profile1")
        
        
        available = state_manager.get_available_profiles()
        assert "profile1" in available
        assert "profile2" in available

    def test_mark_available_not_in_use(self, state_manager: ProfileStateManager):
        """Test marking available a profile that wasn't in use (should be safe)"""
        state_manager.update_cache(["profile1"])
        
        
        state_manager.mark_available("profile1")  
        
        
        assert "profile1" in state_manager.get_available_profiles()

    def test_mark_deleted(self, state_manager: ProfileStateManager):
        """Test marking a profile as deleted"""
        state_manager.update_cache(["profile1", "profile2", "profile3"])
        
        state_manager.mark_deleted("profile2")
        
        
        cached = state_manager.get_cached_profiles()
        available = state_manager.get_available_profiles()
        
        assert "profile2" not in cached
        assert "profile2" not in available
        assert state_manager._deleted_profiles == {"profile2"}

    def test_mark_deleted_while_in_use(self, state_manager: ProfileStateManager):
        """Test deleting a profile that's currently in use"""
        state_manager.update_cache(["profile1", "profile2"])
        state_manager.mark_in_use("profile1")
        
        
        state_manager.mark_deleted("profile1")
        
        
        assert "profile1" not in state_manager.get_cached_profiles()
        assert "profile1" not in state_manager._in_use_profiles
        assert "profile1" in state_manager._deleted_profiles

    def test_mark_deleted_twice(self, state_manager: ProfileStateManager):
        """Test deleting the same profile multiple times (idempotent)"""
        state_manager.update_cache(["profile1"])
        
        state_manager.mark_deleted("profile1")
        state_manager.mark_deleted("profile1")  
        
        
        assert len(state_manager._deleted_profiles) == 1
    def test_add_to_pool(self, state_manager: ProfileStateManager):
        """Test adding a new profile to the pool"""
        state_manager.update_cache(["existing_profile"])
        
        state_manager.add_to_pool("new_profile")
        
        
        cached = state_manager.get_cached_profiles()
        assert "new_profile" in cached
        assert "existing_profile" in cached

    def test_add_to_pool_duplicate(self, state_manager: ProfileStateManager):
        """Test adding a profile that already exists (should not duplicate)"""
        state_manager.update_cache(["profile1"])
        
        
        state_manager.add_to_pool("profile1")
        
        
        cached = state_manager.get_cached_profiles()
        assert cached == ["profile1"]  

    def test_add_to_pool_empty(self, state_manager: ProfileStateManager):
        """Test adding to an empty pool"""
        state_manager.add_to_pool("first_profile")
        
        cached = state_manager.get_cached_profiles()
        assert cached == ["first_profile"]
    
    def test_is_cache_dirty_initial(self, state_manager: ProfileStateManager):
        """Test cache is dirty initially"""
        assert state_manager.is_cache_dirty() == True

    def test_is_cache_dirty_after_update(self, state_manager: ProfileStateManager):
        """Test cache is clean after update"""
        state_manager.update_cache(["profile1"])
        assert state_manager.is_cache_dirty() == False

    def test_is_cache_dirty_when_empty(self, state_manager: ProfileStateManager):
        """Test cache is dirty when empty (even after update)"""
        state_manager.update_cache([])  
        assert state_manager.is_cache_dirty() == True

    def test_is_cache_dirty_after_deletion(self, state_manager: ProfileStateManager):
        """Test cache state after deletions"""
        state_manager.update_cache(["profile1", "profile2"])
        assert state_manager.is_cache_dirty() == False  
        
        state_manager.mark_deleted("profile1")
        
        assert state_manager.is_cache_dirty() == False

        state_manager.mark_deleted("profile2")

        assert state_manager.is_cache_dirty() == True

    def test_get_status_comprehensive(self, state_manager: ProfileStateManager):
        """Test comprehensive status reporting"""
        
        state_manager.update_cache(["p1", "p2", "p3", "p4", "p5"])
        state_manager.mark_in_use("p1")
        state_manager.mark_in_use("p2") 
        state_manager.mark_deleted("p3")
        
        
        status = state_manager.get_status()
        
        assert status["total_profiles"] == 4  
        assert status["in_use"] == 2
        assert status["available"] == 2  
        assert status["deleted"] == 1
        assert status["profiles"] == ["p1", "p2", "p4", "p5"]  

    def test_get_status_empty(self, state_manager: ProfileStateManager):
        """Test status when no profiles exist"""
        status = state_manager.get_status()
        
        assert status["total_profiles"] == 0
        assert status["in_use"] == 0
        assert status["available"] == 0
        assert status["deleted"] == 0
        assert status["profiles"] == []

    def test_complete_workflow(self, state_manager: ProfileStateManager):
        """Test a complete profile lifecycle workflow"""
        
        state_manager.update_cache(["profile1", "profile2", "profile3"])
        assert state_manager.get_available_profiles() == ["profile1", "profile2", "profile3"]
        
        
        state_manager.mark_in_use("profile1")
        assert state_manager.get_available_profiles() == ["profile2", "profile3"]
        
        
        state_manager.mark_available("profile1")
        assert state_manager.get_available_profiles() == ["profile1", "profile2", "profile3"]
        
        
        state_manager.add_to_pool("profile4")
        assert "profile4" in state_manager.get_cached_profiles()
        
        
        state_manager.mark_deleted("profile2")
        assert state_manager.get_available_profiles() == ["profile1", "profile3", "profile4"]
        
        
        status = state_manager.get_status()
        assert status["total_profiles"] == 3
        assert status["available"] == 3
        assert status["deleted"] == 1

    def test_logging_behavior(self, state_manager: ProfileStateManager, caplog):
        """Test that appropriate logging happens"""
        state_manager.update_cache(["p1", "p2"])
        
        
        assert "Cache updated with 2 profiles" in caplog.text
        
        state_manager.mark_deleted("p1")
        assert "Profile p1 marked deleted" in caplog.text