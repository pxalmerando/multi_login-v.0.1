import pytest
from unittest.mock import Mock, patch, mock_open
from src.token_manager import TokenManager
from src.auth import UserAuth
import json
class TestTokenManager:
    @pytest.fixture
    def mock_user_auth(self):
        return Mock(spec=UserAuth)
    
    def test_init(self, mock_user_auth):
        """
            Test that the TokenManager class is initialized correctly.
            It should take the user_auth and token_path parameters and store them as
            instance variables.
        """
        token_path = 'token.json'
        user_auth = mock_user_auth
        token_manager = TokenManager(user_auth, token_path)
        assert token_manager.token_path == token_path
        assert token_manager.user_auth == user_auth

    def test_load_tokens(self, mock_user_auth):
        """
            Test that the load_tokens method reads the tokens from the file correctly.
        """
        expected_tokens = {'access_token': '123', 'refresh_token': '456', 'token_expiration': 123.456}
        m = mock_open(read_data=json.dumps(expected_tokens))
        with patch('builtins.open', m):
            token_manager = TokenManager(mock_user_auth)
            token_manager.token_path = 'token.json'
            result = token_manager.load_tokens()
            m.assert_called_once_with('token.json', 'r')
            assert result == expected_tokens

    def test_save(self, mock_user_auth):
        """
            Test that the save method writes the tokens to the file correctly.
        """
        expected_tokens = {'access_token': '123', 'refresh_token': '456', 'token_expiration': 123.456}
        m = mock_open()
        with patch('builtins.open', m):
            with patch('json.dump') as mock_json_dump:
                token_manager = TokenManager(mock_user_auth)
                token_manager.token_path = 'token.json'
                token_manager.save(expected_tokens)
                m.assert_called_once_with('token.json', 'w')
                mock_json_dump.assert_called_once_with(expected_tokens, m())
        
    def test_get_tokens_valid_not_expired(self, mock_user_auth):
        """Case 1: load_tokens returns valid tokens that are not expired"""
        token_manager = TokenManager(mock_user_auth)
        mock_tokens = {
            'access_token': 'valid_access',
            'refresh_token': 'valid_refresh',
            'token_expiration': 123.456
        }
        token_manager.load_tokens = Mock(return_value=mock_tokens)
        mock_user_auth.is_expired.return_value = False
        mock_user_auth.to_dict.return_value = mock_tokens
        token_manager.save = Mock()
        
        result = token_manager.get_tokens()
        
        mock_user_auth.set_tokens.assert_called_once_with(
            access_token='valid_access',
            refresh_token='valid_refresh',
            token_expiration=123.456
        )
        mock_user_auth.is_expired.assert_called_once()
        mock_user_auth.login.assert_not_called()
        token_manager.save.assert_not_called()
        assert result == mock_tokens

    def test_get_tokens_expired(self, mock_user_auth):
        """Case 2: load_tokens returns expired tokens, triggers login"""
        token_manager = TokenManager(mock_user_auth)
        
        old_tokens = {
            'access_token': 'old_access',
            'refresh_token': 'old_refresh',
            'token_expiration': 100.0
        }
        new_tokens = {
            'access_token': 'new_access',
            'refresh_token': 'new_refresh',
            'token_expiration': 999.999
        }
        token_manager.load_tokens = Mock(return_value=old_tokens)
        mock_user_auth.is_expired.return_value = True
        mock_user_auth.to_dict.return_value = new_tokens
        token_manager.save = Mock()
        
        result = token_manager.get_tokens()
        
        mock_user_auth.set_tokens.assert_called_once_with(
            access_token='old_access',
            refresh_token='old_refresh',
            token_expiration=100.0
        )
        mock_user_auth.is_expired.assert_called_once()
        mock_user_auth.login.assert_called_once()
        token_manager.save.assert_called_once_with(new_tokens)
        assert result == new_tokens

    def test_get_tokens_no_tokens(self, mock_user_auth):
        """Case 3: no tokens at all, must login and save"""
        token_manager = TokenManager(mock_user_auth)
        
        fresh_tokens = {
            'access_token': 'fresh_access',
            'refresh_token': 'fresh_refresh',
            'token_expiration': 888.888
        }
        token_manager.load_tokens = Mock(return_value=None)
        mock_user_auth.to_dict.return_value = fresh_tokens
        token_manager.save = Mock()
        
        result = token_manager.get_tokens()
        mock_user_auth.set_tokens.assert_not_called()
        mock_user_auth.is_expired.assert_not_called()
        mock_user_auth.login.assert_called_once()
        token_manager.save.assert_called_once_with(fresh_tokens)
        assert result == fresh_tokens
