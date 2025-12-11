import pytest
from unittest.mock import AsyncMock, Mock

from app.infrastructure.redis.redis_key_manager import RedisKeyManager
from app.services.redis_profile_reporter import RedisProfileStatusReporter


@pytest.fixture
def mock_redis_client():
    """Create a mock Redis client"""
    mock = Mock()
    mock.sdiff = AsyncMock()
    mock.scard = AsyncMock()
    mock_pipeline = AsyncMock()
    mock_pipeline.scard.return_value = mock_pipeline
    mock_pipeline.scard.return_value = mock_pipeline
    mock_pipeline.execute = AsyncMock()
    mock.pipeline.return_value.__aenter__.return_value = mock_pipeline
    mock.pipeline.return_value.__aenter__.return_value = mock_pipeline
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
def status_reporter(mock_redis_client, mock_key_manager):
    """Create RedisProfileStatusReporter with mocked dependencies"""
    return RedisProfileStatusReporter(mock_redis_client, mock_key_manager)

@pytest.mark.asyncio
async def test_get_available_profiles(status_reporter, mock_redis_client):
    """Test getting available profiles (pool - in_use - deleted)"""
    
    mock_redis_client.sdiff.return_value = {"profile1", "profile3"}
    
    
    result = await status_reporter.get_available_profiles()
    
    
    assert result == ["profile1", "profile3"]
    mock_redis_client.sdiff.assert_called_once_with(
        "profiles:pool",
        "profiles:in_use", 
        "profiles:deleted"
    )

@pytest.mark.asyncio
async def test_get_available_profiles_empty(status_reporter, mock_redis_client):
    """Test getting available profiles when none are available"""
    
    mock_redis_client.sdiff.return_value = set()
    
    
    result = await status_reporter.get_available_profiles()
    
    
    assert result == []

@pytest.mark.asyncio
async def test_get_status(status_reporter, mock_redis_client):
    """Test getting comprehensive status with pipeline"""
    
    mock_pipeline = mock_redis_client.pipeline.return_value.__aenter__.return_value
    mock_pipeline.execute.return_value = [
        100,  
        25,   
        10,   
        {"profile1", "profile2", "profile3"}  
    ]
    
    
    result = await status_reporter.get_status()
    
    
    expected_status = {
        "total_profiles": 100,
        "in_use": 25,
        "deleted": 10,
        "available": 3  
    }
    assert result == expected_status
    
    
    mock_redis_client.pipeline.assert_called_once_with(transaction=False)
    
    
    assert mock_pipeline.scard.call_count == 3
    mock_pipeline.scard.assert_any_call("profiles:pool")
    mock_pipeline.scard.assert_any_call("profiles:in_use")
    mock_pipeline.scard.assert_any_call("profiles:deleted")
    mock_pipeline.sdiff.assert_called_once_with(
        "profiles:pool",
        "profiles:in_use",
        "profiles:deleted"
    )

@pytest.mark.asyncio
async def test_get_utilization_percentage_normal(status_reporter, mock_redis_client):
    """Test utilization percentage with normal usage"""
    
    mock_pipeline = mock_redis_client.pipeline.return_value.__aenter__.return_value
    mock_pipeline.execute.return_value = [
        100,  
        25,   
        10,   
        {"profile1", "profile2", "profile3"}  
    ]
    
    
    result = await status_reporter.get_utilization_percentage()
    
    
    assert result == 25.0

@pytest.mark.asyncio
async def test_get_utilization_percentage_zero_total(status_reporter, mock_redis_client):
    """Test utilization percentage when no profiles exist"""
    
    mock_pipeline = mock_redis_client.pipeline.return_value.__aenter__.return_value
    mock_pipeline.execute.return_value = [
        0,    
        0,    
        0,    
        set() 
    ]
    
    
    result = await status_reporter.get_utilization_percentage()
    
    
    assert result == 0.0

@pytest.mark.asyncio
async def test_get_utilization_percentage_full_usage(status_reporter, mock_redis_client):
    """Test utilization percentage when all profiles are in use"""
    
    mock_pipeline = mock_redis_client.pipeline.return_value.__aenter__.return_value
    mock_pipeline.execute.return_value = [
        50,   
        50,   
        0,    
        set() 
    ]
    
    
    result = await status_reporter.get_utilization_percentage()
    
    
    assert result == 100.0

@pytest.mark.asyncio
async def test_get_status_empty_pool(status_reporter, mock_redis_client):
    """Test status when pool is completely empty"""
    
    mock_pipeline = mock_redis_client.pipeline.return_value.__aenter__.return_value
    mock_pipeline.execute.return_value = [
        0,    
        0,    
        0,    
        set() 
    ]
    
    
    result = await status_reporter.get_status()
    
    
    expected_status = {
        "total_profiles": 0,
        "in_use": 0,
        "deleted": 0,
        "available": 0
    }
    assert result == expected_status

@pytest.mark.asyncio
async def test_get_status_all_in_use(status_reporter, mock_redis_client):
    """Test status when all profiles are in use"""
    
    mock_pipeline = mock_redis_client.pipeline.return_value.__aenter__.return_value
    mock_pipeline.execute.return_value = [
        50,   
        50,   
        0,    
        set() 
    ]
    
    
    result = await status_reporter.get_status()
    
    
    expected_status = {
        "total_profiles": 50,
        "in_use": 50,
        "deleted": 0,
        "available": 0
    }
    assert result == expected_status

@pytest.mark.asyncio
async def test_get_status_some_deleted(status_reporter, mock_redis_client):
    """Test status when some profiles are deleted"""
    
    mock_pipeline = mock_redis_client.pipeline.return_value.__aenter__.return_value
    mock_pipeline.execute.return_value = [
        100,  
        25,   
        15,   
        {"profile1", "profile2", "profile3", "profile4", "profile5"}  
    ]
    
    
    result = await status_reporter.get_status()
    
    
    expected_status = {
        "total_profiles": 100,
        "in_use": 25,
        "deleted": 15,
        "available": 5
    }
    assert result == expected_status

@pytest.mark.asyncio
async def test_is_pool_exhausted_true(status_reporter, mock_redis_client):
    """Test pool exhausted when no profiles are available"""
    
    mock_redis_client.sdiff.return_value = set()
    
    
    result = await status_reporter.is_pool_exhausted()
    
    
    assert result is True

@pytest.mark.asyncio
async def test_is_pool_exhausted_false(status_reporter, mock_redis_client):
    """Test pool not exhausted when profiles are available"""
    
    mock_redis_client.sdiff.return_value = {"profile1", "profile2", "profile3"}
    
    
    result = await status_reporter.is_pool_exhausted()
    
    
    assert result is False