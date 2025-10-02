import pytest
from src.client import Client

@pytest.fixture
def mock_token_manager(mocker):
    """
        Returns a mock of TokenManager, with get_tokens returning a valid access
        token, refresh token and token expiration time. The mock is suitable for
        use in unit tests of code that uses TokenManager.
    """
    mock = mocker.Mock()

    mock.get_tokens.return_value = {
        'access_token': 'access_token',
        'refresh_token': 'refresh_token',
        'token_expiration': 123
    }

    return mock

@pytest.fixture
def client(mock_token_manager):
    return Client(mock_token_manager)

class TestClientAuthentication:

    def test_ensure_authenticated_retrieves_tokens(self, client, mock_token_manager):

        """
            Test that calling ensure_authenticated on a Client instance calls get_tokens on
            the underlying TokenManager instance, and that the call to get_tokens is made
            only once.
        """
        client.ensure_authenticated()

        mock_token_manager.get_tokens.assert_called_once()

    def test_ensure_authenticated_handles_valid_tokens(self, client, mock_token_manager):
        """
            Test ensure_authenticated handles valid tokens correctly.
        """
        expected_tokens = {
            'access_token': 'valid_token',
            'refresh_token': 'valid_token',
            'token_expiration': 1234567890
        }

        mock_token_manager.get_tokens.return_value = expected_tokens

        client.ensure_authenticated()

        mock_token_manager.get_tokens.assert_called_once()

    def test_ensure_authenticated_raises_on_auth_failure(self, client, mock_token_manager):
        """Test that authentication failure raises appropriate exception"""
        mock_token_manager.get_tokens.side_effect = Exception("Authentication failed.")
        
        with pytest.raises(Exception, match="Authentication failed."):
            client.ensure_authenticated()
    
    def test_ensure_authenticated_propagates_token_manager_errors(self, client, mock_token_manager):
        """Test that token manager errors are propagated"""
        mock_token_manager.get_tokens.side_effect = RuntimeError("Token manager error")
        
        with pytest.raises(RuntimeError, match="Token manager error"):
            client.ensure_authenticated()
    def test_ensure_authenticated_called_multiple_times(self, client, mock_token_manager):
        """Test that multiple authentication calls work correctly"""
        client.ensure_authenticated()
        client.ensure_authenticated()
        client.ensure_authenticated()
        
        # Each call should trigger get_tokens
        assert mock_token_manager.get_tokens.call_count == 3
    
    def test_ensure_authenticated_with_none_response(self, client, mock_token_manager):
        """Test behavior when token manager returns None"""
        mock_token_manager.get_tokens.return_value = None
        
        # Should complete without error
        client.ensure_authenticated()
        mock_token_manager.get_tokens.assert_called_once()
