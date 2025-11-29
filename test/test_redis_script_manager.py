import pytest
from unittest.mock import AsyncMock, Mock

from app.services.redis_script_manager import RedisScriptManager


@pytest.fixture
def mock_redis_client():
    """Create a mock Redis client with script methods"""
    mock = Mock()
    mock.script_load = AsyncMock()
    mock.evalsha = AsyncMock()
    return mock


@pytest.fixture
def script_manager(mock_redis_client):
    """Create RedisScriptManager with mocked Redis client"""
    return RedisScriptManager(mock_redis_client)


@pytest.mark.asyncio
async def test_register_scripts(script_manager, mock_redis_client):
    """Test that all scripts are registered correctly"""
    
    mock_redis_client.script_load.return_value = "fake_sha_hash"
    
    
    await script_manager.register_scripts()
    
    
    expected_scripts = ['acquire', 'release', 'delete', 'add', 'replace']
    assert len(script_manager._scripts) == len(expected_scripts)
    
    
    assert mock_redis_client.script_load.call_count == 5
    
    
    for script_name in expected_scripts:
        assert script_name in script_manager._scripts
        assert script_manager._scripts[script_name] == "fake_sha_hash"

@pytest.mark.asyncio
async def test_get_script_sha_success(script_manager, mock_redis_client):
    """Test getting SHA for a registered script"""
    
    mock_redis_client.script_load.return_value = "fake_sha_hash"
    await script_manager.register_scripts()
    
    
    sha = script_manager.get_script_sha('acquire')
    
    
    assert sha == "fake_sha_hash"


def test_get_script_sha_not_found(script_manager):
    """Test getting SHA for a non-existent script raises KeyError"""
    
    
    
    with pytest.raises(KeyError):
        script_manager.get_script_sha('unknown_script')


@pytest.mark.asyncio
async def test_execute_script_success(script_manager, mock_redis_client):
    """Test executing a script with correct parameters"""
    
    mock_redis_client.script_load.return_value = "fake_sha_hash"
    mock_redis_client.evalsha.return_value = 1  
    await script_manager.register_scripts()
    
    
    result = await script_manager.execute_script(
        'acquire', 
        3, 
        'key1', 'key2', 'key3', 'arg1'
    )
    
    
    assert result == 1
    mock_redis_client.evalsha.assert_called_once_with(
        "fake_sha_hash",  
        3,                
        'key1', 'key2', 'key3', 'arg1'  
    )


@pytest.mark.asyncio
async def test_execute_script_different_num_keys(script_manager, mock_redis_client):
    """Test executing a script with different number of keys"""
    
    mock_redis_client.script_load.return_value = "fake_sha_hash"
    mock_redis_client.evalsha.return_value = 1
    await script_manager.register_scripts()
    
    
    result = await script_manager.execute_script(
        'release',
        1,
        'in_use_key',
        'profile123'
    )
    
    
    mock_redis_client.evalsha.assert_called_once_with(
        "fake_sha_hash",
        1,
        'in_use_key',
        'profile123'
    )