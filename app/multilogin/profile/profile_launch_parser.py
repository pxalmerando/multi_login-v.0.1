from app.multilogin.exceptions import MultiLoginServiceError
from app.multilogin.schemas import MultiLoginProfileSession

def parse_profile_start_response(response: dict, profile_id: str) -> MultiLoginProfileSession:

    try:
        if not isinstance(response, dict):
            raise MultiLoginServiceError(f"Invalid response: {response}")
        
        status = response.get("status")
        if not isinstance(status, dict):
            raise MultiLoginServiceError(f"Invalid status: {status}")
        
        http_code = status.get("http_code")

        if http_code is None:
            raise MultiLoginServiceError(f"Invalid response: missing http_code {profile_id}")
        
        selenium_port = status.get("message")
        if selenium_port is None:
            raise MultiLoginServiceError(f"Invalid response: missing selenium_port {profile_id}")
        
        return MultiLoginProfileSession(
            status_code=http_code,
            profile_id=profile_id,
            selenium_port=selenium_port
        )
    
    except Exception as e:
        raise MultiLoginServiceError(f"Invalid response: {e}")