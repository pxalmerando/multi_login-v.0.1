import pytest
from src.auth import UserAuth
from src.http_client import HttpClient
from unittest.mock import Mock
import hashlib
import time

class TestUserAuthInitialization:
    @pytest.fixture
    def mock_http_client(self):
        return Mock(spec=HttpClient)
    
    def test_init_stores(self, mock_http_client, ):

        base_url = "https://example.com"
        email = "email"
        password = "password"
        token_duration_minutes = 30

        auth = UserAuth(
            base_url=base_url,
            email=email,
            password=password,
            http_client=mock_http_client,
            token_duration_minutes=token_duration_minutes
        )
        
        assert auth.base_url == "https://example.com"
        assert auth.email == "email"
        assert auth.password == "password"
        assert auth.http_client == mock_http_client
        assert auth.token_duration_seconds == token_duration_minutes * 60

        assert auth._access_token is None
        assert auth._refresh_token is None
        assert auth._token_expiration == 0

        auth.access_token = "access_token"
        auth.refresh_token = "refresh_token"
        auth.token_expiration = 123

        assert auth._access_token == "access_token"
        assert auth._refresh_token == "refresh_token"
        assert auth._token_expiration == 123
    
    def test_hash_password(self, mock_http_client):

        password = "secret"
        expected_hash = hashlib.md5(password.encode("utf-8")).hexdigest()

        auth = UserAuth(
            base_url="https://example.com",
            email="email",
            password=password,
            http_client=mock_http_client,
            token_duration_minutes=30,
        )

        # Call without arguments because it uses self.password
        assert auth._hash_password() == expected_hash



    def test_to_dict(self, mock_http_client):

        auth = UserAuth(
            base_url="https://example.com",
            email="email",
            password="password",
            http_client=mock_http_client,
            token_duration_minutes=30,
        )

        initial_dict = {
            "access_token": None,
            "refresh_token": None,
            "token_expiration": 0
        }

        assert auth.to_dict() == initial_dict

        assert auth.to_dict() == {
            "access_token": None,
            "refresh_token": None,
            "token_expiration": 0
        }

        auth._access_token = 'access_token'
        auth._refresh_token = 'refresh_token'
        auth._token_expiration = 123


        expected_dict = {
            "access_token": 'access_token',
            "refresh_token": 'refresh_token',
            "token_expiration": 123,
        }

        assert auth.to_dict() == expected_dict

    def test_is_expired(self, mock_http_client):

        auth = UserAuth(
            base_url="https://example.com",
            email="email",
            password="password",
            http_client=mock_http_client,
            token_duration_minutes=30,
        )

        assert auth.is_expired() is True

        auth._token_expiration = int(time.time()) + 100  # expires 100s from now

        assert auth.is_expired() is False

        auth._token_expiration = int(time.time()) - 10  # expired 10s ago

        assert auth.is_expired() is True

    def test_get_auth_header(self, mock_http_client):

        auth = UserAuth(
            base_url="https://example.com",
            email="email",
            password="password",
            http_client=mock_http_client,
            token_duration_minutes=30,
        )

        with pytest.raises(ValueError, match="You need to login first"):
            auth.get_auth_header()

        auth._access_token = 'access_token'

        assert auth.get_auth_header() == {'Authorization': 'Bearer access_token'}

    def test_set_tokens(self, mock_http_client):

        auth = UserAuth(
            base_url="https://example.com",
            email="email",
            password="password",
            http_client=mock_http_client,
            token_duration_minutes=30,
        )

        auth.set_tokens('access_token', 'refresh_token', 123)

        assert auth._access_token == 'access_token'
        assert auth._refresh_token == 'refresh_token'
        assert auth._token_expiration == 123

    def test_set_new_tokens(self, mock_http_client):

        auth = UserAuth(
            base_url="https://example.com",
            email="email",
            password="password",
            http_client=mock_http_client,
            token_duration_minutes=30,
        )

        auth.set_new_tokens('access_token', 'refresh_token')

        now = int(time.time())
        assert auth._access_token == 'access_token'
        assert auth._refresh_token == 'refresh_token'
        assert now + 1700 < auth._token_expiration < now + 1900


    def test_login(self, mock_http_client):

        response = {'data':{
            'access_token': 'access_token',
            'refresh_token': 'refresh_token'
        }}

        mock_http_client.post.return_value = response

        auth = UserAuth(
            base_url="https://example.com",
            email="email",
            password="password",
            http_client=mock_http_client,
            token_duration_minutes=30,
        )

        result = auth.login()

        mock_http_client.post.assert_called_once_with('/user/signin', json={"email": "email", "password": auth._hash_password()})

        assert result == auth.to_dict()