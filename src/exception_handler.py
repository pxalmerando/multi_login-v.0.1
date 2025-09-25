

class BadRequestError(Exception):
    """400 Bad Request: Invalid or malformed request"""
    def __init__(self, message: str = "The request was invalid or malformed. Check the request parameters and try again. This type typically relates to wrong or invalid data being sent", response=None):
        super().__init__(message, 400, response)

class UnauthorizedError(Exception):
    """401 Unauthorized: Authentication credentials missing or invalid"""
    def __init__(self, message: str = "Authentication credentials are missing or invalid. Ensure you are using valid credentials and tokens", response=None):
        super().__init__(message, 401, response)

class ForbiddenError(Exception):
    """403 Forbidden: User lacks permission for the resource"""
    def __init__(self, message: str = "The user does not have permission to access the requested resource.", response=None):
        super().__init__(message, 403, response)

class TooManyRequestsError(Exception):
    """429 Too Many Requests: Rate limit exceeded"""
    def __init__(self, message: str = "Rate limit exceeded", response=None, retry_after: int = None):
        super().__init__(message, 429, response)
    