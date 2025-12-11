import pytest
from unittest.mock import AsyncMock, Mock

from app.infrastructure.redis.redis_key_manager import RedisKeyManager
from app.services.redis_profile_operation import RedisProfileOperations
from app.services.redis_script_manager import RedisScriptManager

@pytest.fixture
def mock_script_manager():
    """Create a mock RedisScriptManager with Redis client"""
    mock = Mock()
    mock.execute_script = AsyncMock()
    mock.client = Mock()  
    mock.client.delete = AsyncMock()  
    return mock

@pytest.fixture
def mock_key_manager():
    """Create a mock RedisKeyManager"""
    mock = Mock(spec=RedisKeyManager)
    mock.pool_key = "profiles:pool"
    mock.in_use_key = "profiles:in_use" 
    mock.deleted_key = "profiles:deleted"
    return mock

@pytest.fixture
def profile_ops(mock_script_manager, mock_key_manager):
    """Create RedisProfileOperations with mocked dependencies"""
    return RedisProfileOperations(mock_script_manager, mock_key_manager)

@pytest.mark.asyncio
async def test_try_acquire_profile_success(profile_ops, mock_script_manager):
    """Test successful profile acquisition"""
    mock_script_manager.execute_script.return_value = 1

    result = await profile_ops.try_acquire_profile("profile123")

    assert result is True

    mock_script_manager.execute_script.assert_called_once_with(
        'acquire',
        3,
        "profiles:pool",
        "profiles:in_use", 
        "profiles:deleted",
        "profile123"
    )

@pytest.mark.asyncio
async def test_try_acquire_profile_failure(profile_ops, mock_script_manager):
    """Test failed profile acquisition"""
    
    mock_script_manager.execute_script.return_value = 0
    
    
    result = await profile_ops.try_acquire_profile("profile123")
    
    
    assert result is False
    mock_script_manager.execute_script.assert_called_once()

@pytest.mark.asyncio
async def test_release_profile(profile_ops, mock_script_manager):
    mock_script_manager.execute_script.return_value = 1

    result = await profile_ops.release_profile("profile123")

    assert result is True
    mock_script_manager.execute_script.assert_called_once_with(
        'release',
        1,
        "profiles:in_use",
        "profile123"
    )

@pytest.mark.asyncio
async def test_release_profile_failure(profile_ops, mock_script_manager):
    """Test failed profile release (profile not in use)"""
    
    mock_script_manager.execute_script.return_value = 0
    
    
    result = await profile_ops.release_profile("profile123")
    
    
    assert result is False
    mock_script_manager.execute_script.assert_called_once_with(
        'release',
        1,
        "profiles:in_use",
        "profile123"
    )

@pytest.mark.asyncio
async def test_mark_deleted_success(profile_ops, mock_script_manager):
    """Test successfully marking a profile as deleted"""
    
    mock_script_manager.execute_script.return_value = 1
    
    
    result = await profile_ops.mark_deleted("profile123")
    
    
    assert result is True
    mock_script_manager.execute_script.assert_called_once_with(
        'delete',
        3,
        "profiles:pool",
        "profiles:in_use",
        "profiles:deleted", 
        "profile123"
    )

@pytest.mark.asyncio
async def test_mark_deleted_failure(profile_ops, mock_script_manager):
    """Test failing to mark profile as deleted (already deleted)"""
    
    mock_script_manager.execute_script.return_value = 0
    
    
    result = await profile_ops.mark_deleted("profile123")
    
    
    assert result is False

@pytest.mark.asyncio
async def test_add_profile_success(profile_ops, mock_script_manager):
    """Test successfully adding a new profile"""
    
    mock_script_manager.execute_script.return_value = 1
    
    
    result = await profile_ops.add_profile("profile123")
    
    
    assert result is True
    mock_script_manager.execute_script.assert_called_once_with(
        'add',
        2,
        "profiles:pool",
        "profiles:deleted",
        "profile123"
    )

@pytest.mark.asyncio
async def test_add_profile_failure(profile_ops, mock_script_manager):
    """Test failing to add profile (already exists or deleted)"""
    
    mock_script_manager.execute_script.return_value = 0
    
    
    result = await profile_ops.add_profile("profile123")
    
    
    assert result is False

@pytest.mark.asyncio
async def test_replace_all_profiles_empty_list(profile_ops, mock_script_manager):
    """Test replacing with empty profile list"""
    
    mock_script_manager.client.delete = AsyncMock()
    
    
    result = await profile_ops.replace_all_profiles([])
    
    
    assert result == 0
    mock_script_manager.client.delete.assert_called_once_with("profiles:pool")
    mock_script_manager.execute_script.assert_not_called()

@pytest.mark.asyncio
async def test_replace_all_profiles_with_profiles(profile_ops, mock_script_manager):
    """Test replacing with multiple profiles"""
    
    mock_script_manager.execute_script.return_value = 3
    profiles = ["profile1", "profile2", "profile3"]
    
    
    result = await profile_ops.replace_all_profiles(profiles)
    
    
    assert result == 3
    mock_script_manager.execute_script.assert_called_once_with(
        'replace',
        2,
        "profiles:pool",
        "profiles:deleted",
        "profile1",
        "profile2", 
        "profile3"
    )