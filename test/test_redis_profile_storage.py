import pytest
from unittest.mock import Mock, AsyncMock, patch
from app.services.redis_profile_storage import RedisProfileStorage


@pytest.fixture
def mock_redis_client():
    """Mock Redis client with all necessary async methods"""
    mock = Mock()
    mock.ping = AsyncMock()
    mock.script_load = AsyncMock(return_value="fake_script_sha")
    mock.evalsha = AsyncMock()
    mock.sdiff = AsyncMock()
    mock.scard = AsyncMock()
    return mock


@pytest.fixture
def mock_key_manager():
    """Mock RedisKeyManager"""
    mock = Mock()
    mock.pool_key = "profiles:pool"
    mock.in_use_key = "profiles:in_use"
    mock.deleted_key = "profiles:deleted"
    return mock


@pytest.fixture
def mock_script_manager():
    """Mock RedisScriptManager"""
    mock = Mock()
    mock.register_scripts = AsyncMock()
    mock.execute_script = AsyncMock()
    return mock


@pytest.fixture
def mock_operations():
    """Mock RedisProfileOperations"""
    mock = Mock()
    mock.try_acquire_profile = AsyncMock()
    mock.release_profile = AsyncMock()
    mock.mark_deleted = AsyncMock()
    mock.add_profile = AsyncMock()
    mock.replace_all_profiles = AsyncMock()
    return mock


@pytest.fixture
def mock_reporter():
    """Mock RedisProfileStatusReporter"""
    mock = Mock()
    mock.get_available_profiles = AsyncMock()
    mock.get_status = AsyncMock()
    return mock


@pytest.fixture
@patch('app.services.redis_profile_storage.RedisProfileStatusReporter')
@patch('app.services.redis_profile_storage.RedisProfileOperations')
@patch('app.services.redis_profile_storage.RedisScriptManager')
@patch('app.services.redis_profile_storage.RedisKeyManager')
@patch('app.services.redis_profile_storage.redis.from_url')
def profile_storage(
    mock_from_url,
    mock_key_manager_class,
    mock_script_manager_class,
    mock_operations_class,
    mock_reporter_class,
    mock_redis_client,
    mock_key_manager,
    mock_script_manager,
    mock_operations,
    mock_reporter
):
    """Complete fixture mocking ALL internal dependencies"""
    
    mock_from_url.return_value = mock_redis_client
    mock_key_manager_class.return_value = mock_key_manager
    mock_script_manager_class.return_value = mock_script_manager
    mock_operations_class.return_value = mock_operations
    mock_reporter_class.return_value = mock_reporter
    
    
    storage = RedisProfileStorage(url="redis://localhost:6379", prefix="test")
    
    return storage


@pytest.mark.asyncio
async def test_redis_connection_mocked(profile_storage, mock_redis_client, mock_script_manager):
    """Test that redis.from_url was properly mocked"""
    
    assert profile_storage.client == mock_redis_client
    
    
    await profile_storage.initialize()
    
    mock_redis_client.ping.assert_called_once()
    mock_script_manager.register_scripts.assert_called_once()


@pytest.mark.asyncio
async def test_delegation_to_operations(profile_storage, mock_operations):
    """Test that storage methods delegate to operations"""
    
    mock_operations.try_acquire_profile.return_value = True
    result = await profile_storage.try_acquire_profile("profile123")
    assert result is True
    mock_operations.try_acquire_profile.assert_called_once_with(profile_id="profile123")
    
    
    mock_operations.release_profile.return_value = True
    result = await profile_storage.release_profile("profile123")
    assert result is True
    mock_operations.release_profile.assert_called_once_with(profile_id="profile123")


@pytest.mark.asyncio
async def test_delegation_to_reporter(profile_storage, mock_reporter):
    """Test that storage methods delegate to reporter"""
    
    expected_profiles = ["profile1", "profile2"]
    mock_reporter.get_available_profiles.return_value = expected_profiles
    result = await profile_storage.get_available_profiles()
    assert result == expected_profiles
    mock_reporter.get_available_profiles.assert_called_once()
    
    
    expected_status = {"total": 10, "in_use": 2}
    mock_reporter.get_status.return_value = expected_status
    result = await profile_storage.get_status()
    assert result == expected_status
    mock_reporter.get_status.assert_called_once()