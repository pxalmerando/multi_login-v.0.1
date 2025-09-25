import hashlib
import requests
import time
import json

class UserAuth:
    def __init__(self, base_url: str, email: str, password: str, token_file: str = "token.json"):
        self.base_url = base_url
        self.email = email
        self.password = password
        self.TOKEN_FILE = token_file

        self._access_token = None
        self._refresh_token = None
        self._token_expiration = 0

    @property
    def access_token(self):
        return self._access_token

    @access_token.setter
    def access_token(self, value):
        self._access_token = value
        self._save_tokens()

    @property
    def refresh_token(self):
        return self._refresh_token

    @refresh_token.setter
    def refresh_token(self, value):
        self._refresh_token = value
        self._save_tokens()

    @property
    def token_expiration(self):
        return self._token_expiration
    
    @token_expiration.setter
    def token_expiration(self, value):
        self._token_expiration = value
        self._save_tokens()
    
    def _hash_password(self) -> str:
        return hashlib.md5(self.password.encode('utf-8')).hexdigest()

    def get_auth_header(self):
        if self.access_token:
            return {'Authorization': f'Bearer {self.access_token}'}
        else:
            raise ValueError("You need to login first")
        
    def _save_tokens(self):
        data = {
            "access_token": self.access_token,
            "refresh_token": self.refresh_token,
            "token_expiration": self.token_expiration
        }
        with open(self.TOKEN_FILE, "w") as f:
            json.dump(data, f)
    
    def login(self) -> str:

        url = f"{self.base_url}/user/signin"
        payload = {
            "email": self.email,
            "password": self._hash_password()
        }

        response = requests.post(url=url, json=payload)

        response.raise_for_status()

        data = response.json().get('data')
        access_token = data.get("token")
        refresh_token = data.get("refresh_token")

        if not access_token or not refresh_token:
            raise Exception(f"Login failed: {data}")
    
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.token_expiration = time.time() + (25 * 60)

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_expiration": self.token_expiration
        }
    
    

    