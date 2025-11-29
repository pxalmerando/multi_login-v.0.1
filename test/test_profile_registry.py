import pytest
from app.services.profile_registry import ProfileRegistry
from app.models.schemas.profile_models import MultiLoginProfileSession

class TestProfileRegistry:
    
    def test_register_new_profile(self, sample_profile_session):
        """Test registering a new profile"""
        
        registry = ProfileRegistry()
        
        
        registry.register(sample_profile_session)
        
        
        assert registry.is_running(sample_profile_session.profile_id)
        assert registry.count() == 1
    
    def test_register_duplicate_profile_raises_error(self, sample_profile_session):
        """Test that registering duplicate profile raises ValueError"""
        
        registry = ProfileRegistry()
        registry.register(sample_profile_session)
        
        
        with pytest.raises(ValueError, match="already registered"):
            registry.register(sample_profile_session)
    
    def test_unregister_profile(self, sample_profile_session):
        """Test unregistering a profile"""
        
        registry = ProfileRegistry()
        registry.register(sample_profile_session)
        
        
        registry.unregister(sample_profile_session.profile_id)
        
        
        assert not registry.is_running(sample_profile_session.profile_id)
        assert registry.count() == 0
    
    def test_get_session(self, sample_profile_session):
        """Test retrieving a session"""
        
        registry = ProfileRegistry()
        registry.register(sample_profile_session)
        
        
        session = registry.get_session(sample_profile_session.profile_id)
        
        
        assert session == sample_profile_session
    
    def test_get_all_sessions(self):
        """Test getting all sessions"""
        
        registry = ProfileRegistry()
        session1 = MultiLoginProfileSession(
            status_code=200,
            profile_id="profile_1",
            selenium_port="4444"
        )
        session2 = MultiLoginProfileSession(
            status_code=200,
            profile_id="profile_2",
            selenium_port="4445"
        )
        
        registry.register(session1)
        registry.register(session2)
        
        
        sessions = registry.get_all_sessions()
        
        
        assert len(sessions) == 2
        assert session1 in sessions
        assert session2 in sessions
    
    def test_clear(self, sample_profile_session):
        """Test clearing all sessions"""
        
        registry = ProfileRegistry()
        registry.register(sample_profile_session)
        
        
        registry.clear()
        
        
        assert registry.count() == 0