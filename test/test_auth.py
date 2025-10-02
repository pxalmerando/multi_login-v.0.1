import pytest
from src.auth import UserAuth
from src.http_client import HttpClient
from unittest.mock import Mock, patch
import hashlib
import time

@pytest.fixture
def mock_http_client():
    return Mock(spec=HttpClient)

@pytest.fixture
def auth_credentials():
    return {
        "base_url": "https://example.com",
        "email": "email",
        "password": "password",
        "token_duration_minutes": 30
    }

@pytest.fixture
def auth(mock_http_client, auth_credentials):
    return UserAuth(**auth_credentials, http_client=mock_http_client)

class TestUserAuthInitialization:
    def test_init_stores(self, mock_http_client, auth_credentials, auth):        
        
        """Test that UserAuth stores the given parameters correctly and that the
        access_token, refresh_token and token_expiration can be set and retrieved
        correctly."""

        assert auth.base_url == "https://example.com"
        assert auth.email == "email"
        assert auth.password == "password"
        assert auth.http_client == mock_http_client
        assert auth.token_duration_seconds == auth_credentials["token_duration_minutes"] * 60

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
        
        """Test that the _hash_password method returns the correct hash for a given password."""

        test_password = "secret"
        expected_hash = hashlib.md5(test_password.encode("utf-8")).hexdigest()

        auth = UserAuth(
            base_url="https://example.com",
            email="email",
            password=test_password,
            http_client=mock_http_client,
            token_duration_minutes=30,
        )

        assert auth._hash_password() == expected_hash

    def test_to_dict(self, auth):

        """Test that the to_dict method returns the correct dictionary based on the
        values of access_token, refresh_token and token_expiration."""

        initial_dict = {
            "access_token": None,
            "refresh_token": None,
            "token_expiration": 0
        }

        assert auth.to_dict() == initial_dict

        auth.access_token = 'access_token'
        auth.refresh_token = 'refresh_token'
        auth.token_expiration = 123

        expected_dict = {
            "access_token": 'access_token',
            "refresh_token": 'refresh_token',
            "token_expiration": 123,
        }

        assert auth.to_dict() == expected_dict

    def test_is_expired(self, auth):

        """
            Test that the is_expired method returns True if the token has expired and False
            otherwise.

            It first checks that the method returns True when the token has expired,
            then sets the token expiration to be in the future and checks that the
            method returns False, and finally sets the token expiration to be in
            the past and checks that the method returns True again.
        """
        assert auth.is_expired() is True

        auth.token_expiration = int(time.time()) + 1

        assert auth.is_expired() is False

        auth.token_expiration = int(time.time()) - 1 

        assert auth.is_expired() is True

    def test_get_auth_header(self, auth):

        """
            Test that the get_auth_header method returns the correct dictionary based on the
            access_token.
            
            It first checks that the method raises a ValueError when the access_token is
            None, then sets the access_token and checks that the method returns the
            correct dictionary.
        """

        # Check that the method raises a ValueError when the access_token is None
        with pytest.raises(ValueError, match="You need to login first"):
            auth.get_auth_header()

        auth.access_token = 'access_token'

        assert auth.get_auth_header() == {'Authorization': 'Bearer access_token'}

    def test_set_tokens(self, auth):  

        """Set tokens and check that the instance variables are set correctly"""
        auth.set_tokens('access_token', 'refresh_token', 123)
        assert auth._access_token == 'access_token'
        assert auth._refresh_token == 'refresh_token'
        assert auth._token_expiration == 123

        """Test setting tokens with None values"""
        auth.set_tokens(None, None, None)
        assert auth._access_token is None
        assert auth._refresh_token is None
        assert auth._token_expiration is None

        """Test setting tokens with empty strings"""
        auth.set_tokens('', '', 0)
        assert auth._access_token == ''
        assert auth._refresh_token == ''
        assert auth._token_expiration == 0

    def test_set_new_tokens(self, auth):
        """
            Test that the set_new_tokens method sets the access_token and refresh_token instance variables
            correctly and that the token_expiration is set to be 30 minutes in the future.

            It first checks that the method sets the instance variables correctly and that the
            token_expiration is within 10 seconds of the expected value. Then it checks that the
            is_expired method returns False when the token has not expired and True when the token has
            expired.
        """
        auth.set_new_tokens('access_token', 'refresh_token')

        now = int(time.time())
        assert auth.access_token == 'access_token'
        assert auth.refresh_token == 'refresh_token'
        assert now + 1700 < auth._token_expiration < now + 1900

        expected_expiration = now + 30 * 60
        assert abs(auth._token_expiration - expected_expiration) < 100

        with patch('time.time', return_value= now + 30 * 60):
            assert not auth.is_expired()

        with patch('time.time', return_value= now + 31 * 60):
            assert auth.is_expired()

    def test_login(self, mock_http_client, auth):
        """
            Test that the login method correctly calls the HttpClient's post method and
            sets the access_token and refresh_token instance variables correctly.

            It first checks that the method calls the HttpClient's post method with the
            correct arguments. Then it checks that the method sets the access_token and
            refresh_token instance variables correctly and that the method returns the
            correct dictionary.

            Parameters:
                mock_http_client (Mock): A mock object of the HttpClient class.
                auth (UserAuth): A UserAuth object.
        """
        response = {'data':{
            'access_token': 'access_token',
            'refresh_token': 'refresh_token'
        }}

        mock_http_client.post.return_value = response

        result = auth.login()

        mock_http_client.post.assert_called_once_with(
                '/user/signin',
                json=
                    {
                        "email": auth.email, 
                    "password": auth._hash_password()
                    }
            )

        assert auth.access_token == 'access_token'
        assert auth.refresh_token == 'refresh_token'    
        assert result == auth.to_dict()
