from dataclasses import dataclass

@dataclass
class RedisKeyManager:

    prefix: str = "profiles"

    @property
    def pool_key(self) -> str:
        """Key for the pool of all available profiles"""
        return f"{self.prefix}:pool"
    
    @property
    def in_use_key(self) -> str:
        """Key for profiles currently in use"""
        return f"{self.prefix}:in_use"
    
    @property
    def deleted_key(self) -> str:
        """Key for deleted/blacklisted profiles"""
        return f"{self.prefix}:deleted"
    
    def get_all_keys(self) -> tuple[str, str, str]:
        """Get all keys as a tuple (pool, in_use, deleted)"""
        return (self.pool_key, self.in_use_key, self.deleted_key)