import hashlib
import time
from http_client import HttpClient
class UserAuth:
    def __init__(self, base_url: str, email: str, password: str, http_client: HttpClient, token_duration_minutes: int = 30):
        self.base_url = base_url
        self.email = email
        self.password = password
        self.http_client = http_client
        self.token_duration_seconds = token_duration_minutes * 60

        self._access_token = None
        self._refresh_token = None
        self._token_expiration = 0

    @property
    def access_token(self) -> str:
        return self._access_token
    
    @property
    def refresh_token(self) -> str:
        return self._refresh_token
    
    @property
    def token_expiration(self) -> float:
        return self._token_expiration
    
    @access_token.setter
    def access_token(self, value: str):
        self._access_token = value

    @refresh_token.setter
    def refresh_token(self, value: str):
        self._refresh_token = value

    @token_expiration.setter
    def token_expiration(self, value: float):
        self._token_expiration = value

    def _hash_password(self) -> str:
        return hashlib.md5(self.password.encode('utf-8')).hexdigest()
    def to_dict(self) -> dict:
        return {
            "access_token": self.access_token,
            "refresh_token": self.refresh_token,
            "token_expiration": self.token_expiration
        }
    def is_expired(self) -> bool:
        return not self._token_expiration or time.time() > self._token_expiration
    
    def get_auth_header(self):
        if self.access_token:
            return {'Authorization': f'Bearer {self.access_token}'}
        else:
            raise ValueError("You need to login first")
    def set_tokens(self, access_token: str, refresh_token: str, token_expiration: float):
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.token_expiration = token_expiration 

    def set_new_tokens(self, access_token: str, refresh_token: str):

        self.set_tokens(
            access_token=access_token,
            refresh_token=refresh_token,
            token_expiration= time.time() + self.token_duration_seconds
        )
    def login(self):

        response = self.http_client.post('/user/signin', json={"email": self.email, "password": self._hash_password()}).get('data')

        self.set_new_tokens(
            access_token=response['access_token'],
            refresh_token=response['refresh_token']
        )

        return self.to_dict()