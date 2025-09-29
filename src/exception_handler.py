from typing import Dict, Any, Optional

class ApiError(Exception):
    error_type = "api_error"
    default_message = "An API error occurred"

    def __init__(self, message: str = None, status_code: int = None, response: Optional[Any] = None, error_code: Optional[str] = None):

        final_message = message or getattr(self, "default_message", "An API error occurred")
        super().__init__(final_message)
        self.message = final_message
        self.status_code = status_code or getattr(self, "status_code", 500)
        self.response = response
        self.error_code = error_code or self.__class__.__name__


    def __str__(self):
        return f"[{self.status_code}] {self.message}"
    
    def __repr__(self):
        return f"{self.__class__.__name__}(status_code={self.status_code}, message={self.message})"

    def _add_additional_fields(self, data: Dict[str, Any], fields: list[str]) -> Dict[str, Any]:
        for field in fields:
            value = getattr(self, field, None)
            if value is not None:
                data[field] = value
        return data

    def to_dict(self) -> Dict[str, Any]:
        return {
            "message": self.message,
            "status_code": self.status_code,
            "response": self.response,
            "type": self.error_type
        }
    

class ClientError(ApiError):
    error_type = "client_error"
    
class ServerError(ApiError):
    error_type = "server_error"
    

class BadRequestError(ClientError):
    default_message = "The request was invalid or malformed. Check the request parameters and try again. This type typically relates to wrong or invalid data being sent"
    status_code = 400
    def __init__(self, message: str = None, response: Optional[Any] = None, invalid_fields: Optional[list] = None):

        super().__init__(message=message, response=response)

        self.invalid_fields = invalid_fields or []

    def to_dict(self) -> dict[str, Any]:
        data = super().to_dict()
        return self._add_additional_fields(data, ["invalid_fields"])
    
class UnauthorizedError(ClientError):
    default_message = "Authentication credentials are missing or invalid. Ensure you are using valid credentials and tokens"
    status_code = 401
    def __init__(self, message: str = None, response: Optional[Any] = None):
        super().__init__(message=message, response=response)

class ForbiddenError(ClientError):
    default_message = "The user does not have permission to access the requested resource."
    status_code = 403
    def __init__(self, message: str = None, response: Optional[Any] = None, required_permissions: Optional[str] = None):
        super().__init__(message=message, response=response)

        self.required_permissions = required_permissions

    def to_dict(self) -> dict[str, Any]:
        data = super().to_dict()
        return self._add_additional_fields(data, ["required_permissions"])

class TooManyRequestsError(ClientError):
    default_message = "Too many requests. You have exceeded the rate limit."
    status_code = 429
    def __init__(self, message: str = None, response: Optional[Any] = None, retry_after: Optional[int] = None, limit: Optional[int] = None):
    
        super().__init__(message=message, response=response)
        self.retry_after = retry_after
        self.limit = limit

    def to_dict(self):
        data = super().to_dict()
        return self._add_additional_fields(data, ["retry_after", "limit"])
    
class InternalServerError(ServerError):
    default_message = "Something went wrong on the server. Please try again later."
    status_code = 500
    def __init__(self, message: str = None, response: Optional[Any] = None, error_id: Optional[str] = None):
        super().__init__(message=message, response=response)

        self.error_id = error_id

    def to_dict(self):
        data = super().to_dict()
        return self._add_additional_fields(data, ["error_id"])
    
class ExceptionMapper:

    _error_map = {
        400: BadRequestError,
        401: UnauthorizedError,
        403: ForbiddenError,
        429: TooManyRequestsError,
        500: InternalServerError
    }

    @classmethod
    def from_response(cls, status_code: int, message: str = None, response: Any = None) -> ApiError:


        error_class = cls._error_map.get(status_code)

        if error_class:
            return error_class(message=message, response=response)

        else:
            return ApiError(message=message, status_code=status_code, response=response)
        
    @classmethod
    def raise_for_status(cls, status_code: int, message: str = None, response: Any = None):

        if status_code >= 400:
            raise cls.from_response(status_code, message, response)
        
    @classmethod
    def get_error_class(cls, status_code: int) -> type:
        return cls._error_map.get(status_code, ApiError)
        

def handle_api_errors(default_return = None, log_errors = True):

    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except ApiError as e:
                if log_errors:
                    error_type = e.__class__.__name__
                    print(f"{error_type} in {func.__name__}: {e}")
                    print(f"Response: {e.to_dict()}")
                return default_return
        return wrapper
    return decorator