"""Application configuration and constants."""
from decouple import config
from app.core.secret_loader import load_secrets

load_secrets()

EMAIL = str(config("EMAIL", default=""))
PASSWORD = str(config("PASSWORD", default=""))
REDIS_URL = str(config("REDISURL", default=config("REDIS_URL", default="")))

# Security Configuration
SECRET_KEY = str(config("SECRET_KEY"))
ALGORITHM = str(config("ALGORITHM"))
ACCESS_TOKEN_EXPIRE_MINUTES = float(config("ACCESS_TOKEN_EXPIRE_MINUTES"))

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
LAUNCHER_URL = "http://host.docker.internal:45000"
# LAUNCHER_URL = "https://launcher.mlx.yt:45001"