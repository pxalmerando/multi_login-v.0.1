from app.services.redis_key_manager import RedisKeyManager

manager = RedisKeyManager()

def test_default_initialization():
    assert manager.prefix == "profiles"

def test_pool_key_property():
    """Test that pool_key returns correct formatted string"""
    assert manager.pool_key == "profiles:pool"

def test_in_use_key_property():
    """Test that in_use_key returns correct formatted string"""
    assert manager.in_use_key == "profiles:in_use"

def test_deleted_key_property():
    """Test that deleted_key returns correct formatted string"""
    assert manager.deleted_key == "profiles:deleted"

def test_get_all_keys():
    all_keys = manager.get_all_keys()

    assert isinstance(all_keys, tuple)

    assert len(all_keys) == 3

    assert all_keys[0] == "profiles:pool"
    assert all_keys[1] == "profiles:in_use" 
    assert all_keys[2] == "profiles:deleted"

    assert all_keys == (manager.pool_key, manager.in_use_key, manager.deleted_key)