"""Application configuration and constants."""
from decouple import config

# Security Configuration
SECRET_KEY = config("SECRET_KEY")
ALGORITHM = config("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = config("ACCESS_TOKEN_EXPIRE_MINUTES", cast=float)

# HTTP Status Codes
STATUS_BAD_REQUEST = 400

# Error Messages
ERROR_INVALID_CREDENTIALS = "Incorrect username or password"
ERROR_EMAIL_REGISTERED = "Email already registered"
ERROR_USERNAME_REGISTERED = "Username already registered"
ERROR_CANNOT_VALIDATE = "Could not validate credentials"
ERROR_INACTIVE_USER = "Inactive user"

# Headers
AUTH_HEADER_NAME = {"WWW-Authenticate": "Bearer"}

# URLS:
BASE_URL = "https://api.multilogin.com"
LAUNCHER_URL = "https://launcher.mlx.yt:45001"