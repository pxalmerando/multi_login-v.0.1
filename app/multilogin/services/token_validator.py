import logging
from typing import Optional
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

class TokenValidator:
    def __init__(self, grace_period_seconds: int = 60) -> bool:
        
        self.grace_period_seconds = grace_period_seconds
    
    def has_required_fields(self, tokens: Optional[dict]):
        if tokens is None:
            logger.debug(f"[TokenValidator] Tokens is None")
            return False
        
        if not isinstance(tokens, dict):
            logger.warning(f"[TokenValidator] Tokens is not a dict, got {type(tokens).__name__}")
            return False

        required_fields = {'access_token', 'refresh_token', 'token_expiration'}

        missing_fields = required_fields - set(tokens.keys())
        
        if missing_fields:
            logger.warning(f'[TokenValidator] Missing required fields: {missing_fields}')
            return False
        
        return True
    
    def is_expired(self, tokens: dict) -> bool:

        if not self.has_required_fields(tokens):
            logger.warning(f"[TokenValidator] Cannot check expiration - missing fields")
            return False
        
        try:
            expiration_timestamp = tokens["token_expiration"]

            if not isinstance(expiration_timestamp, (int, float)):
                logger.warning(f"[TokenValidator] token_expiration must be numeric, got {type(expiration_timestamp).__name__}")
                return True
            
            now = datetime.now(timezone.utc).timestamp()

            effective_expiration = expiration_timestamp + self.grace_period_seconds

            is_expired = now >= effective_expiration

            if is_expired:
                logger.info(
                    f"[TokenValidator] Token expired (now: {now}, expiration: {expiration_timestamp})"
                )
            else:
                time_remaining = effective_expiration - now
                logger.debug(
                    f"[TokenValidator] Token valid for {time_remaining:.0f} more seconds"
                )
            
            return is_expired
        
        except Exception as e:
            logger.exception(
                f"[TokenValidator] Unexpected error checking expiration {e}"
            )
            return True
    def is_valid(self, tokens: Optional[dict]) -> bool:
        
        if not self.has_required_fields(tokens):
            return False
        
        if self.is_expired(tokens):
            return False
        
        logger.debug("[TokenValidator] Tokens are valid")
        return True
