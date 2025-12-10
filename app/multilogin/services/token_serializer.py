

import json
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class TokenSerializer:

    def serialize(self, tokens: dict) -> str:
        try:
            return json.dumps(tokens, separators=(',', ':'))
        except Exception as e:
            logger.error(f"[TokenSerializer] Failed to serialize tokens: {e}")
            raise

    def deserialize(self, raw_data: bytes | str | None) -> Optional[dict]:
        if not raw_data:
            logger.debug("[TokenSerializer] No data to deserialize")
            return None

        try:
            if isinstance(raw_data, bytes):
                raw_data = raw_data.decode('utf-8')
            data = json.loads(raw_data)
            if not isinstance(data, dict):
                logger.warning(
                    f"[TokenSerializer] Deserialized data is not a dict, got {type(data).__name__}"
                )
                return None
            return data

        except (ValueError, json.JSONDecodeError) as e:
            logger.warning(
                f"[TokenSerializer] Invalid JSON format: {e}"
            )
            return None
               
        except Exception as e:
            logger.exception(
                f"[TokenSerializer] Unexpected error during deserialization"
            )
            return None
        
    def validate_structure(self, tokens: dict) -> bool:
        required_fields = {'access_token', 'refresh_token', 'token_expiration'}
        
        if not isinstance(tokens, dict):
            logger.warning("[TokenSerializer] Tokens is not a dictionary")
            return False
        
        missing_fields = required_fields - set(tokens.keys())
        
        if missing_fields:
            logger.warning(
                f"[TokenSerializer] Missing required fields: {missing_fields}"
            )
            return False
        
        return True