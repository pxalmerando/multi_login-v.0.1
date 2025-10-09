import pytest
from unittest.mock import patch
from src.profile_manager import (
    ProfileManager, ProfileConfig, ScreenConfig, ProxyConfig, StorageConfig
)


@pytest.fixture
def profile_manager():
    return ProfileManager(base_url="http://localhost:8000", api_token="testtoken")

@pytest.fixture
def basic_profile_config():
    return ProfileConfig(
        name="Test Profile",
        folder_id="folder123"
    )

@pytest.fixture
def profile_config_with_screen():
    return ProfileConfig(
        name="Test Profile with Screen",
        folder_id="folder123",
        screen=ScreenConfig(width=1366, height=768, pixel_ratio=1.0)
    )

@pytest.fixture
def profile_config_with_proxy():
    return ProfileConfig(
        name="Test Profile with Proxy",
        folder_id="folder123",
        proxy=ProxyConfig(type="http", host="proxy.example.com", port=8080)
    )

@pytest.fixture
def profile_config_full():
    return ProfileConfig(
        name="Full Config Profile",
        folder_id="folder123",
        screen=ScreenConfig(width=1366, height=768, pixel_ratio=1.0),
        proxy=ProxyConfig(type="http", host="proxy.example.com", port=8080)
    )

class TestScreenConfig:
    """Test the ScreenConfig dataclass"""
    
    def test_screen_config_defaults(self):
        """Test that ScreenConfig has correct default values"""
        screen = ScreenConfig()
        assert screen.width == 1920
        assert screen.height == 1080
        assert screen.pixel_ratio == 1.0
    
    def test_screen_config_custom_values(self):
        """Test that ScreenConfig accepts custom values"""
        screen = ScreenConfig(width=2560, height=1440, pixel_ratio=2.0)
        assert screen.width == 2560
        assert screen.height == 1440
        assert screen.pixel_ratio == 2.0


class TestProxyConfig:
    """Test the ProxyConfig dataclass"""
    
    def test_proxy_config_defaults(self):
        """Test that ProxyConfig has correct default values"""
        proxy = ProxyConfig()
        assert proxy.type is None
        assert proxy.host is None
        assert proxy.port is None
        assert proxy.username is None
        assert proxy.password is None
        assert proxy.save_traffic is False
    
    def test_proxy_config_is_configured_false_when_empty(self):
        """Test that is_configured returns False when proxy is not set"""
        proxy = ProxyConfig()
        assert proxy.is_configured() is False
    
    def test_proxy_config_is_configured_false_when_partial(self):
        """Test that is_configured returns False when only type is set"""
        proxy = ProxyConfig(type="http")
        assert proxy.is_configured() is False
    
    def test_proxy_config_is_configured_true_when_complete(self):
        """Test that is_configured returns True when type and host are set"""
        proxy = ProxyConfig(type="http", host="proxy.example.com")
        assert proxy.is_configured() is True


class TestStorageConfig:
    """Test the StorageConfig dataclass"""
    
    def test_storage_config_defaults(self):
        """Test that StorageConfig has correct default values"""
        storage = StorageConfig()
        assert storage.is_local is True
        assert storage.save_service_worker is True


class TestProfileConfig:
    """Test the ProfileConfig dataclass"""
    
    def test_profile_config_required_fields(self):
        """Test that ProfileConfig requires name and folder_id"""
        config = ProfileConfig(name="Test", folder_id="folder123")
        assert config.name == "Test"
        assert config.folder_id == "folder123"
    
    def test_profile_config_defaults(self):
        """Test that ProfileConfig has correct default values"""
        config = ProfileConfig(name="Test", folder_id="folder123")
        assert config.profile_id is None
        assert config.browser_type == "mimic"
        assert config.os_type == "windows"
        assert config.auto_update_core is True
        assert config.times == 1
        assert config.notes == ''
        assert config.screen is None
        assert config.proxy is None

class TestProfileManagerHelpers:
    """Test the private helper methods of ProfileManager"""
    
    def test_should_use_custom_screen_false(self, profile_manager, basic_profile_config):
        """Test that _should_use_custom_screen returns False when no screen is set"""
        result = profile_manager._should_use_custom_screen(basic_profile_config)
        assert result is False
    
    def test_should_use_custom_screen_true(self, profile_manager, profile_config_with_screen):
        """Test that _should_use_custom_screen returns True when screen is set"""
        result = profile_manager._should_use_custom_screen(profile_config_with_screen)
        assert result is True
    
    def test_should_use_custom_proxy_false(self, profile_manager, basic_profile_config):
        """Test that _should_use_custom_proxy returns False when no proxy is set"""
        result = profile_manager._should_use_custom_proxy(basic_profile_config)
        assert result is False
    
    def test_should_use_custom_proxy_true(self, profile_manager, profile_config_with_proxy):
        """Test that _should_use_custom_proxy returns True when proxy is configured"""
        result = profile_manager._should_use_custom_proxy(profile_config_with_proxy)
        assert result is True
    
    def test_build_flags_default(self, profile_manager, basic_profile_config):
        """Test that _build_flags creates correct default flags"""
        flags = profile_manager._build_flags(basic_profile_config)
        
        # Check that all expected flags are present
        assert flags['audio_masking'] == 'natural'
        assert flags['screen_masking'] == 'natural'
        assert flags['proxy_masking'] == 'disabled'
        assert flags['canvas_noise'] == 'natural'
    
    def test_build_flags_with_custom_screen(self, profile_manager, profile_config_with_screen):
        """Test that _build_flags sets screen_masking to custom when screen is configured"""
        flags = profile_manager._build_flags(profile_config_with_screen)
        assert flags['screen_masking'] == 'custom'
    
    def test_build_flags_with_custom_proxy(self, profile_manager, profile_config_with_proxy):
        """Test that _build_flags sets proxy_masking to custom when proxy is configured"""
        flags = profile_manager._build_flags(profile_config_with_proxy)
        assert flags['proxy_masking'] == 'custom'
    
    def test_build_fingerprint_empty(self, profile_manager, basic_profile_config):
        """Test that _build_fingerprint returns empty dict when no custom settings"""
        fingerprint = profile_manager._build_fingerprint(basic_profile_config)
        assert fingerprint == {}
    
    def test_build_fingerprint_with_screen(self, profile_manager, profile_config_with_screen):
        """Test that _build_fingerprint includes screen data when configured"""
        fingerprint = profile_manager._build_fingerprint(profile_config_with_screen)
        assert 'screen' in fingerprint
        assert fingerprint['screen']['width'] == 1366
        assert fingerprint['screen']['height'] == 768
        assert fingerprint['screen']['pixel_ratio'] == 1.0
    
    def test_build_storage(self, profile_manager):
        """Test that _build_storage returns correct storage configuration"""
        storage = profile_manager._build_storage()
        assert storage['is_local'] is True
        assert storage['save_service_worker'] is True
    
    def test_build_proxy_none_when_not_configured(self, profile_manager, basic_profile_config):
        """Test that _build_proxy returns None when proxy is not configured"""
        proxy = profile_manager._build_proxy(basic_profile_config)
        assert proxy is None
    
    def test_build_proxy_data_when_configured(self, profile_manager, profile_config_with_proxy):
        """Test that _build_proxy returns proxy data when configured"""
        proxy = profile_manager._build_proxy(profile_config_with_proxy)
        assert proxy is not None
        assert proxy['type'] == 'http'
        assert proxy['host'] == 'proxy.example.com'
        assert proxy['port'] == 8080
    
class TestValidation:
    """Test validation methods"""
    
    def test_validate_create_config_success(self, profile_manager, basic_profile_config):
        """Test that _validate_create_config passes with valid config"""
        # Should not raise any exception
        profile_manager._validate_create_config(basic_profile_config)
    
    def test_validate_create_config_missing_name(self, profile_manager):
        """Test that _validate_create_config raises error when name is missing"""
        config = ProfileConfig(name="", folder_id="folder123")
        with pytest.raises(ValueError, match="Name and folder_id are required"):
            profile_manager._validate_create_config(config)
    
    def test_validate_create_config_missing_folder_id(self, profile_manager):
        """Test that _validate_create_config raises error when folder_id is missing"""
        config = ProfileConfig(name="Test", folder_id="")
        with pytest.raises(ValueError, match="Name and folder_id are required"):
            profile_manager._validate_create_config(config)
    
    def test_validate_create_config_with_profile_id(self, profile_manager):
        """Test that _validate_create_config raises error when profile_id is set"""
        config = ProfileConfig(name="Test", folder_id="folder123", profile_id="profile123")
        with pytest.raises(ValueError, match="Profile ID should not be set"):
            profile_manager._validate_create_config(config)
    
    def test_validate_update_config_success(self, profile_manager):
        """Test that _validate_update_config passes with valid profile_id"""
        # Should not raise any exception
        profile_manager._validate_update_config("profile123")
    
    def test_validate_update_config_missing_id(self, profile_manager):
        """Test that _validate_update_config raises error when profile_id is missing"""
        with pytest.raises(ValueError, match="Profile ID is required for updates"):
            profile_manager._validate_update_config("")

class TestDataBuilding:
    """Test the data building methods"""
    
    def test_build_common_data(self, profile_manager, basic_profile_config):
        """Test that _build_common_data returns correct common fields"""
        data = profile_manager._build_common_data(basic_profile_config)
        assert data == {'name': 'Test Profile'}
    
    def test_build_create_data(self, profile_manager, basic_profile_config):
        """Test that _build_create_data returns correct fields for creation"""
        data = profile_manager._build_create_data(basic_profile_config)
        
        assert data['browser_type'] == 'mimic'
        assert data['folder_id'] == 'folder123'
        assert data['os_type'] == 'windows'
        assert data['auto_update_core'] is True
        assert data['times'] == 1
        assert data['notes'] == ''
    
    def test_build_update_data(self, profile_manager):
        """Test that _build_update_data returns profile_id"""
        config = ProfileConfig(name="Test", folder_id="folder123", profile_id="profile123")
        data = profile_manager._build_update_data(config)
        assert data == {'profile_id': 'profile123'}
    
    def test_build_parameters(self, profile_manager, basic_profile_config):
        """Test that _build_parameters creates correct structure"""
        params = profile_manager._build_parameters(basic_profile_config)
        
        # Check structure
        assert 'flags' in params
        assert 'storage' in params
        assert 'fingerprint' in params
        assert 'proxy' not in params  # No proxy configured
    
    def test_build_parameters_with_proxy(self, profile_manager, profile_config_with_proxy):
        """Test that _build_parameters includes proxy when configured"""
        params = profile_manager._build_parameters(profile_config_with_proxy)
        
        assert 'proxy' in params
        assert params['proxy']['type'] == 'http'
        assert params['proxy']['host'] == 'proxy.example.com'
    
    def test_build_profile_data_for_create(self, profile_manager, basic_profile_config):
        """Test that _build_profile_data creates correct data for new profile"""
        data = profile_manager._build_profile_data(basic_profile_config, is_update=False)
        
        # Check common fields
        assert data['name'] == 'Test Profile'
        
        # Check create-specific fields
        assert data['browser_type'] == 'mimic'
        assert data['folder_id'] == 'folder123'
        
        # Check parameters
        assert 'parameters' in data
        assert 'flags' in data['parameters']
        
        # Should not have profile_id for create
        assert 'profile_id' not in data
    
    def test_build_profile_data_for_update(self, profile_manager):
        """Test that _build_profile_data creates correct data for update"""
        config = ProfileConfig(
            name="Updated Profile",
            folder_id="folder123",
            profile_id="profile123"
        )
        data = profile_manager._build_profile_data(config, is_update=True)
        
        # Check common fields
        assert data['name'] == 'Updated Profile'
        
        # Check update-specific fields
        assert data['profile_id'] == 'profile123'
        
        # Check parameters
        assert 'parameters' in data
        
        # Should not have create-only fields
        assert 'browser_type' not in data
        assert 'folder_id' not in data
    
    def test_build_profile_data_raises_on_missing_profile_id_for_update(self, profile_manager, basic_profile_config):
        """Test that _build_profile_data raises error when updating without profile_id"""
        with pytest.raises(ValueError, match="Profile ID is required for updates"):
            profile_manager._build_profile_data(basic_profile_config, is_update=True)
    
    def test_build_profile_data_raises_on_profile_id_for_create(self, profile_manager):
        """Test that _build_profile_data raises error when creating with profile_id"""
        config = ProfileConfig(name="Test", folder_id="folder123", profile_id="should_not_be_here")
        with pytest.raises(ValueError, match="Profile ID should not be set"):
            profile_manager._build_profile_data(config, is_update=False)

class TestCreateProfile:
    """Test the create_profile method"""
    
    def test_create_profile_success(self, profile_manager, basic_profile_config):
        """Test that create_profile makes correct API call"""
        # Mock the request method
        with patch.object(profile_manager, 'request') as mock_request:
            mock_request.return_value = {'success': True, 'profile_id': 'new123'}
            
            result = profile_manager.create_profile(basic_profile_config)
            
            # Verify request was called correctly
            mock_request.assert_called_once()
            call_args = mock_request.call_args
            
            assert call_args[0][0] == 'POST'
            assert call_args[0][1] == 'profile/create'
            assert call_args[1]['include_auth'] is True
            assert 'json' in call_args[1]
            
            # Verify the returned result
            assert result['success'] is True
            assert result['profile_id'] == 'new123'
    
    def test_create_profile_with_full_config(self, profile_manager, profile_config_full):
        """Test that create_profile handles full configuration"""
        with patch.object(profile_manager, 'request') as mock_request:
            mock_request.return_value = {'success': True}
            
            profile_manager.create_profile(profile_config_full)
            
            # Get the json data that was passed
            json_data = mock_request.call_args[1]['json']
            
            # Verify all data is included
            assert json_data['name'] == 'Full Config Profile'
            assert json_data['browser_type'] == 'mimic'
            assert json_data['os_type'] == 'windows'
            assert json_data['parameters']['fingerprint']['screen']['width'] == 1366
            assert json_data['parameters']['fingerprint']['screen']['height'] == 768
            assert json_data['parameters']['fingerprint']['screen']['pixel_ratio'] == 1.0
            assert json_data['parameters']['proxy']['type'] == 'http'
    
    def test_create_profile_validation_error(self, profile_manager):
        """Test that create_profile raises validation errors"""
        invalid_config = ProfileConfig(name="", folder_id="folder123")
        
        with pytest.raises(ValueError, match="Name and folder_id are required"):
            profile_manager.create_profile(invalid_config)
    
    def test_create_profile_with_profile_id_error(self, profile_manager):
        """Test that create_profile rejects config with profile_id"""
        invalid_config = ProfileConfig(
            name="Test",
            folder_id="folder123",
            profile_id="should_not_exist"
        )
        
        with pytest.raises(ValueError, match="Profile ID should not be set"):
            profile_manager.create_profile(invalid_config)


class TestListProfiles:
    """Test the list_profiles method"""
    
    def test_list_profiles_basic(self, profile_manager):
        """Test that list_profiles makes correct API call with defaults"""
        with patch.object(profile_manager, 'request') as mock_request:
            mock_request.return_value = {'profiles': [], 'total': 0}
            
            result = profile_manager.list_profiles(folder_id="folder123")
            
            # Verify request
            mock_request.assert_called_once()
            call_args = mock_request.call_args
            
            assert call_args[0][0] == 'POST'
            assert call_args[0][1] == 'profile/search'
            assert call_args[1]['include_auth'] is True
            
            # Verify json data with defaults
            json_data = call_args[1]['json']
            assert json_data['folder_id'] == 'folder123'
            assert json_data['is_removed'] is False
            assert json_data['limit'] == 10
            assert json_data['offset'] == 0
            assert json_data['search_text'] == ''
            assert json_data['storage_type'] == 'all'
            assert json_data['order_by'] == 'created_at'
            assert json_data['sort'] == 'asc'
    
    def test_list_profiles_with_all_parameters(self, profile_manager):
        """Test that list_profiles handles all optional parameters"""
        with patch.object(profile_manager, 'request') as mock_request:
            mock_request.return_value = {'profiles': [], 'total': 0}
            
            profile_manager.list_profiles(
                folder_id="folder123",
                is_removed=True,
                limit=50,
                offset=10,
                search_text="test",
                storage_type="local",
                order_by="name",
                sort="desc"
            )
            
            json_data = mock_request.call_args[1]['json']
            assert json_data['is_removed'] is True
            assert json_data['limit'] == 50
            assert json_data['offset'] == 10
            assert json_data['search_text'] == 'test'
            assert json_data['storage_type'] == 'local'
            assert json_data['order_by'] == 'name'
            assert json_data['sort'] == 'desc'
    
    def test_list_profiles_returns_data(self, profile_manager):
        """Test that list_profiles returns the API response"""
        expected_response = {
            'profiles': [
                {'id': 'prof1', 'name': 'Profile 1'},
                {'id': 'prof2', 'name': 'Profile 2'}
            ],
            'total': 2
        }
        
        with patch.object(profile_manager, 'request') as mock_request:
            mock_request.return_value = expected_response
            
            result = profile_manager.list_profiles(folder_id="folder123")
            
            assert result == expected_response
            assert len(result['profiles']) == 2


class TestUpdateProfile:
    """Test the update_profile method"""
    
    def test_update_profile_success(self, profile_manager, basic_profile_config):
        """Test that update_profile makes correct API call"""
        with patch.object(profile_manager, 'request') as mock_request:
            mock_request.return_value = {'success': True}
            
            result = profile_manager.update_profile("profile123", basic_profile_config)
            
            # Verify request
            mock_request.assert_called_once()
            call_args = mock_request.call_args
            
            assert call_args[0][0] == 'POST'
            assert call_args[0][1] == 'profile/update'
            assert call_args[1]['include_auth'] is True
            
            # Verify json data
            json_data = call_args[1]['json']
            assert json_data['name'] == 'Test Profile'
            assert json_data['profile_id'] == 'profile123'
            assert 'parameters' in json_data
    
    def test_update_profile_sets_profile_id(self, profile_manager, basic_profile_config):
        """Test that update_profile correctly sets profile_id in config"""
        with patch.object(profile_manager, 'request') as mock_request:
            mock_request.return_value = {'success': True}
            
            # Config initially has no profile_id
            assert basic_profile_config.profile_id is None
            
            profile_manager.update_profile("profile123", basic_profile_config)
            
            # profile_id should be set by update_profile
            assert basic_profile_config.profile_id == "profile123"
    
    def test_update_profile_with_full_config(self, profile_manager, profile_config_full):
        """Test that update_profile handles full configuration"""
        with patch.object(profile_manager, 'request') as mock_request:
            mock_request.return_value = {'success': True}
            
            profile_manager.update_profile("profile123", profile_config_full)
            
            json_data = mock_request.call_args[1]['json']
            
            # Verify parameters are included
            assert json_data['parameters']['fingerprint']['screen']['width'] == 1366
            assert json_data['parameters']['fingerprint']['screen']['height'] == 768
            assert json_data['parameters']['fingerprint']['screen']['pixel_ratio'] == 1.
            assert json_data['parameters']['proxy']['type'] == 'http'
    
    def test_update_profile_missing_id_error(self, profile_manager, basic_profile_config):
        """Test that update_profile raises error with empty profile_id"""
        with pytest.raises(ValueError, match="Profile ID is required for updates"):
            profile_manager.update_profile("", basic_profile_config)
    
    def test_update_profile_none_id_error(self, profile_manager, basic_profile_config):
        """Test that update_profile raises error with None profile_id"""
        with pytest.raises(ValueError, match="Profile ID is required for updates"):
            profile_manager.update_profile(None, basic_profile_config)


class TestDeleteProfile:
    """Test the delete_profile method"""
    
    def test_delete_profile_permanent_default(self, profile_manager):
        """Test that delete_profile permanently deletes by default"""
        with patch.object(profile_manager, 'request') as mock_request:
            mock_request.return_value = {'success': True}
            
            result = profile_manager.delete_profile("profile123")
            
            # Verify request
            mock_request.assert_called_once()
            call_args = mock_request.call_args
            
            assert call_args[0][0] == 'POST'
            assert call_args[0][1] == 'profile/remove'
            assert call_args[1]['include_auth'] is True
            
            # Verify json data
            json_data = call_args[1]['json']
            assert json_data['ids'] == ['profile123']
            assert json_data['permanently'] is True
    
    def test_delete_profile_temporary(self, profile_manager):
        """Test that delete_profile can do soft delete"""
        with patch.object(profile_manager, 'request') as mock_request:
            mock_request.return_value = {'success': True}
            
            profile_manager.delete_profile("profile123", is_permanent=False)
            
            json_data = mock_request.call_args[1]['json']
            assert json_data['permanently'] is False
    
    def test_delete_profile_empty_id_error(self, profile_manager):
        """Test that delete_profile raises error with empty profile_id"""
        with pytest.raises(ValueError, match="Profile ID is required"):
            profile_manager.delete_profile("")
    
    def test_delete_profile_none_id_error(self, profile_manager):
        """Test that delete_profile raises error with None profile_id"""
        with pytest.raises(ValueError, match="Profile ID is required"):
            profile_manager.delete_profile(None)
    
    def test_delete_profile_returns_response(self, profile_manager):
        """Test that delete_profile returns the API response"""
        expected_response = {'success': True, 'deleted_count': 1}
        
        with patch.object(profile_manager, 'request') as mock_request:
            mock_request.return_value = expected_response
            
            result = profile_manager.delete_profile("profile123")
            
            assert result == expected_response

class TestIntegration:
    """Test complete workflows that combine multiple methods"""
    
    def test_create_profile_complete_workflow(self, profile_manager):
        """Test creating a profile with all features enabled"""
        config = ProfileConfig(
            name="Complete Test Profile",
            folder_id="folder123",
            browser_type="chromium",
            os_type="macos",
            screen=ScreenConfig(width=3840, height=2160, pixel_ratio=2.0),
            proxy=ProxyConfig(
                type="https",
                host="secure-proxy.example.com",
                port=443,
                username="proxyuser",
                password="proxypass123"
            ),
            notes="This is a test profile with all features"
        )
        
        with patch.object(profile_manager, 'request') as mock_request:
            mock_request.return_value = {'success': True, 'profile_id': 'new_profile'}
            
            result = profile_manager.create_profile(config)
            
            json_data = mock_request.call_args[1]['json']
            
            # Verify all data is correctly structured
            assert json_data['name'] == 'Complete Test Profile'
            assert json_data['browser_type'] == 'chromium'
            assert json_data['os_type'] == 'macos'
            assert json_data['notes'] == 'This is a test profile with all features'
            
            # Verify parameters structure
            params = json_data['parameters']
            assert params['flags']['screen_masking'] == 'custom'
            assert params['flags']['proxy_masking'] == 'custom'
            assert params['fingerprint']['screen']['width'] == 3840
            assert params['proxy']['host'] == 'secure-proxy.example.com'
            
            assert result['success'] is True
    
    def test_update_profile_change_settings(self, profile_manager):
        """Test updating a profile's settings"""
        # Original config
        config = ProfileConfig(
            name="Original Name",
            folder_id="folder123"
        )
        
        # Update to add screen and proxy
        config.screen = ScreenConfig(width=1366, height=768)
        config.proxy = ProxyConfig(type="http", host="new-proxy.com", port=8080)
        
        with patch.object(profile_manager, 'request') as mock_request:
            mock_request.return_value = {'success': True}
            
            profile_manager.update_profile("profile123", config)
            
            json_data = mock_request.call_args[1]['json']
            
            # Verify flags changed to custom
            assert json_data['parameters']['flags']['screen_masking'] == 'custom'
            assert json_data['parameters']['flags']['proxy_masking'] == 'custom'
            
            # Verify new configurations are present
            assert json_data['parameters']['fingerprint']['screen']['width'] == 1366
            assert json_data['parameters']['proxy']['host'] == 'new-proxy.com'

class TestEdgeCases:
    """Test edge cases and unusual inputs"""
    
    def test_profile_config_with_empty_notes(self, profile_manager):
        """Test that empty notes are handled correctly"""
        config = ProfileConfig(name="Test", folder_id="folder123", notes="")
        
        with patch.object(profile_manager, 'request') as mock_request:
            mock_request.return_value = {'success': True}
            profile_manager.create_profile(config)
            
            json_data = mock_request.call_args[1]['json']
            assert json_data['notes'] == ''
    
    def test_profile_config_with_long_notes(self, profile_manager):
        """Test that long notes are handled correctly"""
        long_notes = "A" * 1000
        config = ProfileConfig(name="Test", folder_id="folder123", notes=long_notes)
        
        with patch.object(profile_manager, 'request') as mock_request:
            mock_request.return_value = {'success': True}
            profile_manager.create_profile(config)
            
            json_data = mock_request.call_args[1]['json']
            assert json_data['notes'] == long_notes
    
    def test_proxy_config_with_no_credentials(self, profile_manager):
        """Test proxy configuration without username/password"""
        config = ProfileConfig(
            name="Test",
            folder_id="folder123",
            proxy=ProxyConfig(type="http", host="proxy.com", port=8080)
        )
        
        with patch.object(profile_manager, 'request') as mock_request:
            mock_request.return_value = {'success': True}
            profile_manager.create_profile(config)
            
            json_data = mock_request.call_args[1]['json']
            proxy_data = json_data['parameters']['proxy']
            
            assert proxy_data['username'] is None
            assert proxy_data['password'] is None
    
    def test_screen_config_with_unusual_dimensions(self, profile_manager):
        """Test screen configuration with unusual dimensions"""
        config = ProfileConfig(
            name="Test",
            folder_id="folder123",
            screen=ScreenConfig(width=800, height=600, pixel_ratio=0.5)
        )
        
        with patch.object(profile_manager, 'request') as mock_request:
            mock_request.return_value = {'success': True}
            profile_manager.create_profile(config)
            
            json_data = mock_request.call_args[1]['json']
            screen_data = json_data['parameters']['fingerprint']['screen']
            
            assert screen_data['width'] == 800
            assert screen_data['height'] == 600
            assert screen_data['pixel_ratio'] == 0.5
    
    def test_list_profiles_with_zero_limit(self, profile_manager):
        """Test listing profiles with limit of 0"""
        with patch.object(profile_manager, 'request') as mock_request:
            mock_request.return_value = {'profiles': [], 'total': 0}
            
            profile_manager.list_profiles(folder_id="folder123", limit=0)
            
            json_data = mock_request.call_args[1]['json']
            assert json_data['limit'] == 0
    
    def test_list_profiles_with_large_offset(self, profile_manager):
        """Test listing profiles with large offset"""
        with patch.object(profile_manager, 'request') as mock_request:
            mock_request.return_value = {'profiles': [], 'total': 100}
            
            profile_manager.list_profiles(folder_id="folder123", offset=10000)
            
            json_data = mock_request.call_args[1]['json']
            assert json_data['offset'] == 10000
    
    def test_proxy_config_is_configured_with_only_host(self):
        """Test that proxy is not considered configured with only host"""
        proxy = ProxyConfig(host="proxy.com")
        assert proxy.is_configured() is False
    
    def test_proxy_config_is_configured_with_type_and_host(self):
        """Test that proxy is considered configured with type and host"""
        proxy = ProxyConfig(type="http", host="proxy.com")
        assert proxy.is_configured() is True
class TestParametrized:
    """Use pytest.mark.parametrize to test multiple scenarios"""
    
    @pytest.mark.parametrize("browser_type,os_type", [
        ("mimic", "windows"),
        ("chromium", "linux"),
        ("firefox", "macos"),
        ("webkit", "windows"),
    ])
    def test_different_browser_os_combinations(self, profile_manager, browser_type, os_type):
        """Test creating profiles with different browser and OS combinations"""
        config = ProfileConfig(
            name="Test",
            folder_id="folder123",
            browser_type=browser_type,
            os_type=os_type
        )
        
        with patch.object(profile_manager, 'request') as mock_request:
            mock_request.return_value = {'success': True}
            profile_manager.create_profile(config)
            
            json_data = mock_request.call_args[1]['json']
            assert json_data['browser_type'] == browser_type
            assert json_data['os_type'] == os_type
    
    @pytest.mark.parametrize("width,height,pixel_ratio", [
        (1920, 1080, 1.0),
        (2560, 1440, 1.5),
        (3840, 2160, 2.0),
        (1366, 768, 1.0),
    ])
    def test_different_screen_configurations(self, profile_manager, width, height, pixel_ratio):
        """Test creating profiles with different screen configurations"""
        config = ProfileConfig(
            name="Test",
            folder_id="folder123",
            screen=ScreenConfig(width=width, height=height, pixel_ratio=pixel_ratio)
        )
        
        with patch.object(profile_manager, 'request') as mock_request:
            mock_request.return_value = {'success': True}
            profile_manager.create_profile(config)
            
            json_data = mock_request.call_args[1]['json']
            screen_data = json_data['parameters']['fingerprint']['screen']
            
            assert screen_data['width'] == width
            assert screen_data['height'] == height
            assert screen_data['pixel_ratio'] == pixel_ratio
    
    @pytest.mark.parametrize("proxy_type,port", [
        ("http", 8080),
        ("https", 443),
        ("socks4", 1080),
        ("socks5", 9050),
    ])
    def test_different_proxy_types(self, profile_manager, proxy_type, port):
        """Test creating profiles with different proxy types"""
        config = ProfileConfig(
            name="Test",
            folder_id="folder123",
            proxy=ProxyConfig(type=proxy_type, host="proxy.com", port=port)
        )
        
        with patch.object(profile_manager, 'request') as mock_request:
            mock_request.return_value = {'success': True}
            profile_manager.create_profile(config)
            
            json_data = mock_request.call_args[1]['json']
            proxy_data = json_data['parameters']['proxy']
            
            assert proxy_data['type'] == proxy_type
            assert proxy_data['port'] == port
    
    @pytest.mark.parametrize("order_by,sort", [
        ("created_at", "asc"),
        ("created_at", "desc"),
        ("name", "asc"),
        ("name", "desc"),
        ("updated_at", "asc"),
    ])
    def test_list_profiles_sorting_options(self, profile_manager, order_by, sort):
        """Test listing profiles with different sorting options"""
        with patch.object(profile_manager, 'request') as mock_request:
            mock_request.return_value = {'profiles': [], 'total': 0}
            
            profile_manager.list_profiles(
                folder_id="folder123",
                order_by=order_by,
                sort=sort
            )
            
            json_data = mock_request.call_args[1]['json']
            assert json_data['order_by'] == order_by
            assert json_data['sort'] == sort

class TestFlagsCompletion:
    """Test that all expected flags are present"""
    
    def test_all_flags_present_in_build_flags(self, profile_manager, basic_profile_config):
        """Test that _build_flags returns all expected flag keys"""
        flags = profile_manager._build_flags(basic_profile_config)
        
        expected_flags = [
            'audio_masking',
            'fonts_masking',
            'geolocation_masking',
            'geolocation_popup',
            'graphics_masking',
            'graphics_noise',
            'localization_masking',
            'media_devices_masking',
            'navigator_masking',
            'ports_masking',
            'proxy_masking',
            'screen_masking',
            'timezone_masking',
            'webrtc_masking',
            'quic_mode',
            'canvas_noise',
        ]
        
        for flag in expected_flags:
            assert flag in flags, f"Missing flag: {flag}"
    
    def test_flags_have_valid_values(self, profile_manager, basic_profile_config):
        """Test that flag values are valid strings"""
        flags = profile_manager._build_flags(basic_profile_config)
        
        for key, value in flags.items():
            assert isinstance(value, str), f"Flag {key} should be a string"
            assert len(value) > 0, f"Flag {key} should not be empty"