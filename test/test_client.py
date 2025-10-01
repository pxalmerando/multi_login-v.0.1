import pytest

from src.client import Client

@pytest.fixture
def mock_token_manager(mocker):
    return mocker.Mock()

@pytest.fixture
def client(mock_token_manager):
    return Client(mock_token_manager)


class TestClient:
    def test_ensure_authenticated_calls_get_tokens(self, client, mock_token_manager):
        client.ensure_authenticated()
        mock_token_manager.get_tokens.assert_called_once()
