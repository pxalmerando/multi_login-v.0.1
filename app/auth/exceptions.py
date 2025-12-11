from fastapi import HTTPException


class InvalidCredentialsError(HTTPException):
    pass

class EmailAlreadyRegisteredError(HTTPException):
    pass