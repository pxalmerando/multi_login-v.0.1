import pytest
from src.http_client import HttpClient
from unittest.mock import Mock, patch
import requests

class TestHttpClientInitialization:
    """Test HttpClient initialization and properties."""
    
    def test_client_stores_base_url_and_timeout(self):
        client = HttpClient("https://example.com")
        assert client.base_url == "https://example.com"
        assert client.timeout == 10
        
        client_custom = HttpClient("https://example.com/", timeout=20)
        assert client_custom.base_url == "https://example.com/"
        assert client_custom.timeout == 20

class TestUrlConstruction:
    """Test URL construction with various endpoint formats."""
    
    @pytest.fixture
    def client(self):
        return HttpClient(base_url="https://example.com")

    @pytest.mark.parametrize("endpoint,expected", [
        ("users", "https://example.com/users"),
        ("/users", "https://example.com/users"), 
        ("//users", "https://example.com/users"),
        ("/users/1/2/posts", "https://example.com/users/1/2/posts"),
        ("/users?param1=value1", "https://example.com/users?param1=value1"),
    ])
    def test_full_url_various_endpoints(self, client, endpoint, expected):
        assert client._full_url(endpoint) == expected

class TestHttpClientRequests:
    """Test HTTP method requests with common mock setup."""
    
    @pytest.fixture
    def client(self):
        return HttpClient(base_url="https://example.com", timeout=20)
    
    @pytest.fixture
    def mock_response(self):
        mock = Mock()
        mock.json.return_value = {'Status': 'Success', 'Code': 200, 'Message': 'OK'}
        mock.raise_for_status.return_value = None
        return mock

    @pytest.mark.parametrize("method,client_method,data", [
        ("GET", "get", None),
        ("POST", "post", {'email': 'test@example.com'}),
        ("PUT", "put", {"name": "John Doe"}),
        ("DELETE", "delete", None),
        ("PATCH", "patch", {"name": "John Doe"}),
    ])
    @patch('src.http_client.requests.request')
    def test_http_methods(self, mock_request, client, mock_response, method, client_method, data):
        mock_request.return_value = mock_response
        
        client_func = getattr(client, client_method)
        endpoint = "users/123" if method != "POST" else "users"
        kwargs = {'json': data} if data else {}
        
        result = client_func(endpoint, **kwargs)
        
        expected_url = f"https://example.com/{endpoint}"
        expected_call_kwargs = {'timeout': 20, **kwargs}
        mock_request.assert_called_once_with(method, expected_url, **expected_call_kwargs)
        assert result == {'Status': 'Success', 'Code': 200, 'Message': 'OK'}

class TestTimeoutHandling:
    """Test timeout configuration and override behavior."""
    
    @pytest.fixture
    def client(self):
        return HttpClient(base_url="https://example.com", timeout=15)
    
    @pytest.fixture
    def mock_response(self):
        mock = Mock()
        mock.json.return_value = {"data": "test"}
        mock.raise_for_status.return_value = None
        return mock

    @patch('src.http_client.requests.request')
    @pytest.mark.parametrize("custom_timeout,expected_timeout", [
        (None, None),
        (30, 30),
        (15, 15),  
    ])
    def test_timeout_override(self, mock_request, client, mock_response, 
                            custom_timeout, expected_timeout):
        mock_request.return_value = mock_response
        
        if custom_timeout is None:
            client.get("users", timeout=custom_timeout)
        else:
            client.get("users", timeout=custom_timeout)
            
        mock_request.assert_called_once_with(
            'GET', 'https://example.com/users', timeout=expected_timeout
        )

class TestErrorHandling:
    """Test HTTP error handling and exception propagation."""
    
    @pytest.fixture
    def client(self):
        return HttpClient(base_url="https://example.com")

    @patch('src.http_client.requests.request')
    @pytest.mark.parametrize("exception_class,exception_msg", [
        (requests.HTTPError, "404 Not Found"),
        (requests.ConnectionError, "Connection refused"),
        (requests.Timeout, "Request timed out"),
        (requests.exceptions.JSONDecodeError, "Expecting value"),
    ])
    def test_exceptions_raised(self, mock_request, client, exception_class, exception_msg):
        if exception_class == requests.exceptions.JSONDecodeError:
            mock_response = Mock()
            mock_response.raise_for_status.return_value = None
            mock_response.json.side_effect = exception_class(exception_msg, "", 0)
            mock_request.return_value = mock_response
        else:
            mock_request.side_effect = exception_class(exception_msg)
        
        with pytest.raises(exception_class) as exc_info:
            client.get("test-endpoint")
        assert exception_msg in str(exc_info.value)

class TestKwargsPassthrough:
    """Test that additional kwargs are passed through to requests."""
    
    @pytest.fixture
    def client(self):
        return HttpClient(base_url="https://example.com")
    
    @pytest.fixture
    def mock_response(self):
        mock = Mock()
        mock.json.return_value = {"data": "test"}
        mock.raise_for_status.return_value = None
        return mock

    @patch('src.http_client.requests.request')
    def test_kwargs_passthrough(self, mock_request, client, mock_response):
        mock_request.return_value = mock_response
        
        kwargs = {
            'headers': {"Authorization": "Bearer token"},
            'params': {"limit": 10},
            'timeout': 30
        }
        client.get("users", **kwargs)
        
        mock_request.assert_called_once_with('GET', 'https://example.com/users', **kwargs)

class TestEdgeCases:
    """Test edge cases and special scenarios."""
    
    @pytest.fixture
    def client(self):
        return HttpClient(base_url="https://example.com")
    
    @pytest.fixture
    def mock_response(self):
        mock = Mock()
        mock.json.return_value = {}
        mock.raise_for_status.return_value = None
        return mock

    @patch('src.http_client.requests.request')
    @pytest.mark.parametrize("endpoint,expected_url", [
        ("", "https://example.com/"),
        ("///users", "https://example.com/users"),
    ])
    def test_edge_case_endpoints(self, mock_request, client, mock_response, endpoint, expected_url):
        mock_request.return_value = mock_response
        client.get(endpoint)
        mock_request.assert_called_once_with('GET', expected_url, timeout=10)
    
    def test_base_url_modification(self):
        client = HttpClient(base_url="https://example.com")
        client.base_url = "https://api.production.com"
        assert client.base_url == "https://api.production.com"