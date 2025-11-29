import logging
from typing import Optional

from .token_repository import TokenRepository
from .token_validator import TokenValidator
from .auth_service import UserAuth

logger = logging.getLogger(__name__)


class TokenService:
    
    def __init__(
        self,
        repository: TokenRepository,
        validator: TokenValidator,
        user_auth: UserAuth
    ):
        self.repository = repository
        self.validator = validator
        self.user_auth = user_auth
    
    async def get_tokens(self) -> dict:
        cached_tokens = await self._try_load_cached_tokens()
        
        if cached_tokens and self.validator.is_valid(cached_tokens):
            logger.info(f"[TokenService] Using valid cached tokens")
            return cached_tokens
        
        if cached_tokens:
            logger.info(f"[TokenService] Cached tokens expired, re-authenticating")
        else:
            logger.info(f"[TokenService] No cached tokens, authenticating")
        
        fresh_tokens = await self._authenticate_and_cache()
        return fresh_tokens
    
    async def _try_load_cached_tokens(self) -> Optional[dict]:
        try:
            tokens = await self.repository.load()
            
            if tokens:
                
                if not self.validator.has_required_fields(tokens):
                    logger.warning(
                        f"[TokenService] Cached tokens missing required fields"
                    )
                    return None
                
                logger.debug(f"[TokenService] Loaded tokens from cache")
                return tokens
            
            logger.debug(f"[TokenService] No tokens in cache")
            return None
            
        except Exception as e:
            logger.exception(
                f"[TokenService] Error loading cached tokens, will re-authenticate {e}"
            )
            return None
    
    async def _authenticate_and_cache(self) -> dict:
        try:
            
            await self.user_auth.login()
            
            
            tokens = self.user_auth.to_dict()
            
            logger.info(f"[TokenService] Authentication successful")
            
            
            await self._try_cache_tokens(tokens)
            
            return tokens
            
        except Exception as e:
            logger.exception(f"[TokenService] Authentication failed")
            raise Exception(f"[TokenService] Authentication failed") from e
    
    async def _try_cache_tokens(self, tokens: dict) -> None:
        try:
            await self.repository.save(tokens)
            logger.info(f"[TokenService] Successfully cached new tokens")
            
        except Exception as e:
            logger.warning(
                f"[TokenService] Failed to cache tokens, continuing anyway. Error: {e}"
            )
            
    async def refresh_tokens(self) -> dict:
        logger.info(f"[TokenService] Forcing token refresh")
        return await self._authenticate_and_cache()
    
    async def clear_cache(self) -> bool:
        try:
            deleted = await self.repository.delete()
            
            if deleted:
                logger.info(f"[TokenService] Cleared cached tokens")
            else:
                logger.debug(f"[TokenService] No cached tokens to clear")
            
            return deleted
            
        except Exception as e:
            logger.exception(f"[TokenService] Error clearing cache {e}")
            return False
    
    async def get_cached_tokens_if_valid(self) -> Optional[dict]:
        cached_tokens = await self._try_load_cached_tokens()
        
        if cached_tokens and self.validator.is_valid(cached_tokens):
            logger.debug(f"[TokenService] Retrieved valid cached tokens")
            return cached_tokens
        
        logger.debug(f"[TokenService] No valid cached tokens available")
        return None