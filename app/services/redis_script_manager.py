    
import logging
from typing import Dict
import redis.asyncio as redis

logger = logging.getLogger(__name__)


class RedisScriptManager:

    """
    Single Responsibility: Manage Lua script loading and execution for Redis
    """
    
    def __init__(self, client: redis.Redis):
        self.client = client
        self._scripts: Dict[str, str] = {}
    
    async def register_scripts(self) -> None:

        """Load all Lua scripts into Redis and cache their SHAs"""
        
        self._scripts['release'] = await self.client.script_load(
            """
                if redis.call('SISMEMBER', KEYS[1], ARGV[1]) == 0 then
                    return 0
                end
                return redis.call('SREM', KEYS[1], ARGV[1])
            """
        )
        
        self._scripts['delete'] = await self.client.script_load(
            """
                local pool, in_use, deleted, profile_id = KEYS[1], KEYS[2], KEYS[3], ARGV[1]

                if redis.call('SISMEMBER', deleted, profile_id) == 1 then 
                    return 0
                end

                redis.call('SREM', in_use, profile_id)
                redis.call('SREM', pool, profile_id)
                redis.call('SADD', deleted, profile_id)
                return 1
            """
        )

        self._scripts['replace'] = await self.client.script_load(
            """
                local pool, deleted = KEYS[1], KEYS[2]

                redis.call('DEL', pool)

                local added = 0

                for i = 1, #ARGV do
                    local profile_id = ARGV[i]
                    if redis.call('SISMEMBER', deleted, profile_id) == 0 then
                        redis.call('SADD', pool, profile_id)
                        added = added + 1
                    end
                end

                return added
            """
        )

        self._scripts['add_if_under_limit'] = await self.client.script_load(
            """
                local pool, deleted, profile_id, max_limit = KEYS[1], KEYS[2], ARGV[1], tonumber(ARGV[2])

                if redis.call('SISMEMBER', pool, profile_id) == 1 then
                    return 0
                end

                if redis.call('SISMEMBER', deleted, profile_id) == 1 then
                    return 0
                end

                local current_count = redis.call('SCARD', pool)

                if current_count >= max_limit then
                    return 0
                end

                redis.call('SADD', pool, profile_id)
                
                return 1
            """
        )

        self._scripts["acquire_any_available"] = await self.client.script_load(
            """
                local pool, in_use, deleted = KEYS[1], KEYS[2], KEYS[3]

                local available = redis.call("SDIFF", pool, in_use, deleted)

                if #available == 0 then
                    return nil
                end

                local profile_id = available[1]

                redis.call("SADD", in_use, profile_id)

                return profile_id
            """
        )

        logger.info(f"[ScriptManager] Registered {len(self._scripts)} scripts")

    def get_script_sha(self, script_name: str) -> str:
        """Get the SHA for a registered script"""
        return self._scripts[script_name]
    
    async def execute_script(self, script_name: str, num_keys: int, *args):
        """Execute a registered script by name"""
        sha = self.get_script_sha(script_name)
        return await self.client.evalsha(sha, num_keys, *args) # type: ignore