import pytest
from src.http_client import HttpClient
from unittest.mock import Mock, patch
import requests

class TestHttpClientInitialization:

    def test_client_stores_base_url(self):
        client = HttpClient("https://example.com")
        assert client.base_url == "https://example.com"

    def test_client_stores_timeout(self):
        client = HttpClient("https://example.com")
        assert client.timeout == 10

    def test_client_stores_custom_timeout(self):
        client = HttpClient("https://example.com", timeout=20)
        assert client.timeout == 20
    
    def test_client_base_url_without_trailing_slash(self):
        client = HttpClient("https://example.com")
        assert client.base_url == "https://example.com"
        assert not client.base_url.endswith("/")
    
    def test_client_base_url_with_trailing_slash(self):
        client = HttpClient("https://example.com/")
        assert client.base_url == "https://example.com/"
        assert client.base_url.endswith("/")

class TestUrlConstruction:

    @pytest.fixture
    def client(self):
        return HttpClient(base_url="https://example.com")

    def test_full_url_basic(self, client):
        url = client._full_url("users")

        assert url == "https://example.com/users"
    
    def test_full_url_remove_trailing_slash_from_base(self, client):

        url = client._full_url("users")

        assert url == "https://example.com/users"

    def test_full_url_removes_leading_slash_from_endpoint(self, client):
        url = client._full_url("/users")

        assert url == "https://example.com/users"

    def test_full_url_handles_both_slashes(self, client):
        url = client._full_url("//users")

        assert url == "https://example.com/users"
    

    def test_full_url_with_nested_endpoint(self, client):
        url = client._full_url("/users/1/2/posts")

        assert url == "https://example.com/users/1/2/posts"
    
    def test_full_url_with_query_parameters(self, client):
        url = client._full_url("/users?param1=value1&param2=value2")

        assert url == "https://example.com/users?param1=value1&param2=value2"


class TestHttpClientRequests:

    @pytest.fixture
    def client(self):
        return HttpClient(base_url="https://example.com", timeout=20)
    

    @pytest.fixture
    def mock_response(self):
        mock = Mock()

        mock.json.return_value = {'Status': 'Success', 'Code': 200, 'Message': 'OK'}

        mock.raise_for_status.return_value = None

        return mock
    
    @patch('src.http_client.requests.request')
    def test_get_request(self, mock_request, client, mock_response):

        mock_request.return_value = mock_response

        results = client.get('users')

        assert results == {'Status': 'Success', 'Code': 200, 'Message': 'OK'}

        mock_request.assert_called_once_with('GET', 'https://example.com/users', timeout=20)

        mock_response.raise_for_status.assert_called_once()

        mock_response.json.assert_called_once()

    @patch('src.http_client.requests.request')
    def test_post_request(self, mock_request, client, mock_response):

        mock_request.return_value = mock_response

        post_data = {'email': 'eQ2Ct@example.com', 'password': 'password'}

        result = client.post('users', json=post_data)

        assert result == {'Status': 'Success', 'Code': 200, 'Message': 'OK'}

        mock_request.assert_called_once_with('POST', 'https://example.com/users', json=post_data, timeout=20)

        mock_response.raise_for_status.assert_called_once()

        mock_response.json.assert_called_once()

    @patch('src.http_client.requests.request')
    def test_put_request(self, mock_request, client, mock_response):
        mock_request.return_value = mock_response
        update_data = {"name": "John Doe"}
        
        result = client.put("users/123", json=update_data)
        print(mock_request.call_args)
        mock_request.assert_called_once_with(
            'PUT',
            'https://example.com/users/123',
            json=update_data,
            timeout=20
        )
    
    @patch('src.http_client.requests.request')
    def test_delete_request(self, mock_request, client, mock_response):
        mock_request.return_value = mock_response
        client.delete("users/123")
        
        mock_request.assert_called_once_with(
            'DELETE',
            'https://example.com/users/123',
            timeout=20
        )
    
    @patch('src.http_client.requests.request')
    def test_patch_request(self, mock_request, client, mock_response):
        """Test PATCH request for updating resources."""
        mock_request.return_value = mock_response
        update_data = {"name": "John Doe"}
        
        result = client.patch("users/123", json=update_data)
        
        mock_request.assert_called_once_with(
            'PATCH',
            'https://example.com/users/123',
            json=update_data,
            timeout=20
        )


class TestTimeoutHandling:
    """
    Tests for timeout configuration.
    
    WHY: Timeouts prevent requests from hanging forever
    """
    
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
    def test_uses_default_timeout(self, mock_request, client, mock_response):
        """
        Test that default timeout is used when not specified.
        
        SCENARIO: No timeout in kwargs
        EXPECTED: Uses self.timeout
        """
        
        mock_request.return_value = mock_response
        
        
        client.get("users")
        
        
        mock_request.assert_called_once_with(
            'GET',
            'https://example.com/users',
            timeout=15  
        )
    
    @patch('src.http_client.requests.request')
    def test_custom_timeout_overrides_default(self, mock_request, client, mock_response):
        """
        Test that custom timeout overrides default.
        
        SCENARIO: User specifies timeout in method call
        EXPECTED: Uses custom timeout, not default
        """
        
        mock_request.return_value = mock_response
        
        
        client.get("users", timeout=30)
        
        
        mock_request.assert_called_once_with(
            'GET',
            'https://example.com/users',
            timeout=30  
        )
    
    @patch('src.http_client.requests.request')
    def test_timeout_none_overrides_default(self, mock_request, client, mock_response):
        
        mock_request.return_value = mock_response
        
        client.get("users", timeout=None)
        
        mock_request.assert_called_once_with(
            'GET',
            'https://example.com/users',
            timeout=None  
        )
class TestErrorHandling:
    """
    Tests for HTTP error handling.
    
    WHY: Network requests can fail in many ways
    - 404 Not Found
    - 500 Server Error
    - Connection timeout
    - Network unreachable
    """
    
    @pytest.fixture
    def client(self):
        return HttpClient(base_url="https://example.com")
    
    @patch('src.http_client.requests.request')
    def test_http_error_is_raised(self, mock_request, client):
        """
        Test that HTTP errors are raised.
        
        SCENARIO: Server returns 404 Not Found
        EXPECTED: HTTPError is raised
        
        KEYWORD: .side_effect - Makes mock raise exception
        """
        
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = requests.HTTPError("404 Not Found")
        
        
        
        mock_request.return_value = mock_response
        
        
        with pytest.raises(requests.HTTPError) as exc_info:
            
            
            client.get("nonexistent")
        
        
        assert "404 Not Found" in str(exc_info.value)
        
    
    @patch('src.http_client.requests.request')
    def test_connection_error_is_raised(self, mock_request, client):
        """
        Test that connection errors propagate.
        
        SCENARIO: Cannot connect to server (network down)
        """
        
        mock_request.side_effect = requests.ConnectionError("Connection refused")
        
        
        
        
        with pytest.raises(requests.ConnectionError) as exc_info:
            client.get("users")
        
        assert "Connection refused" in str(exc_info.value)
    
    @patch('src.http_client.requests.request')
    def test_timeout_error_is_raised(self, mock_request, client):
        """
        Test that timeout errors propagate.
        
        SCENARIO: Request takes too long
        """
        
        mock_request.side_effect = requests.Timeout("Request timed out")
        
        
        with pytest.raises(requests.Timeout):
            client.get("slow-endpoint")
    
    @patch('src.http_client.requests.request')
    def test_json_decode_error(self, mock_request, client):
        """
        Test when response is not valid JSON.
        
        SCENARIO: Server returns HTML instead of JSON
        WHY: API might return error page as HTML
        """
        
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.side_effect = requests.exceptions.JSONDecodeError(
            "Expecting value", "", 0
        )
        
        
        mock_request.return_value = mock_response
        
        
        with pytest.raises(requests.exceptions.JSONDecodeError):
            client.get("bad-endpoint")






class TestAllHttpMethods:
    """
    Use parametrization to test all HTTP methods with same logic.
    
    KEYWORD: @pytest.mark.parametrize
    WHY: Avoid duplicating test code for each HTTP method
    """
    
    @pytest.fixture
    def client(self):
        return HttpClient(base_url="https://example.com")
    
    @pytest.fixture
    def mock_response(self):
        mock = Mock()
        mock.json.return_value = {"result": "ok"}
        mock.raise_for_status.return_value = None
        return mock
    
    @pytest.mark.parametrize("method,client_method", [
        
        ("GET", "get"),
        ("POST", "post"),
        ("PUT", "put"),
        ("DELETE", "delete"),
        ("PATCH", "patch"),
    ])
    
    
    @patch('src.http_client.requests.request')
    def test_http_method(
        self, mock_request, client, mock_response, method, client_method
    ):
        """
        Test all HTTP methods use correct method string.
        
        PARAMETERS:
        - method: "GET", "POST", etc. (from parametrize)
        - client_method: "get", "post", etc. (from parametrize)
        
        WHY: Ensures each method calls requests.request with correct method
        """
        
        mock_request.return_value = mock_response
        
        
        client_func = getattr(client, client_method)
        
        
        
        
        result = client_func("test-endpoint")
        
        
        call_args = mock_request.call_args
        
        
        
        
        assert call_args[0][0] == method
        
        
        
        assert result == {"result": "ok"}






class TestKwargsPassthrough:
    """
    Test that additional kwargs are passed through to requests.
    
    WHY: Users might need to pass headers, auth, params, etc.
    """
    
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
    def test_headers_are_passed_through(self, mock_request, client, mock_response):
        """
        Test custom headers are passed to requests.
        
        SCENARIO: User wants to add Authorization header
        """
        
        mock_request.return_value = mock_response
        headers = {"Authorization": "Bearer token123"}
        
        
        client.get("users", headers=headers)
        
        
        mock_request.assert_called_once_with(
            'GET',
            'https://example.com/users',
            headers=headers,  
            timeout=10
        )
    
    @patch('src.http_client.requests.request')
    def test_params_are_passed_through(self, mock_request, client, mock_response):
        """
        Test query parameters are passed through.
        
        SCENARIO: GET request with query params
        """
        
        mock_request.return_value = mock_response
        params = {"limit": 10, "offset": 20}
        
        
        client.get("users", params=params)
        
        
        mock_request.assert_called_once_with(
            'GET',
            'https://example.com/users',
            params=params,  
            timeout=10
        )
    
    @patch('src.http_client.requests.request')
    def test_multiple_kwargs_passed_together(self, mock_request, client, mock_response):
        """
        Test multiple kwargs work together.
        
        SCENARIO: Headers + params + custom timeout
        """
        
        mock_request.return_value = mock_response
        
        
        client.get(
            "users",
            headers={"Authorization": "Bearer token"},
            params={"limit": 10},
            timeout=30
        )
        
        
        mock_request.assert_called_once_with(
            'GET',
            'https://example.com/users',
            headers={"Authorization": "Bearer token"},
            params={"limit": 10},
            timeout=30  
        )

class TestEdgeCases:
    
    
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
    def test_empty_endpoint(self, mock_request, client, mock_response):
        
        mock_request.return_value = mock_response
        
        client.get("")
        
        mock_request.assert_called_once_with(
            'GET',
            'https://example.com/',  
            timeout=10
        )
    
    @patch('src.http_client.requests.request')
    def test_endpoint_with_multiple_slashes(self, mock_request, client, mock_response):
        
        mock_request.return_value = mock_response
        
        client.get("///users")
        
        mock_request.assert_called_once_with(
            'GET',
            'https://example.com/users',  
            timeout=10
        )
    
    def test_base_url_can_be_updated(self):
        """
        Test that base_url can be modified after initialization.
        
        SCENARIO: User changes base_url (e.g., switching environments)
        WHY: Verify attribute is not read-only
        """
        
        client = HttpClient(base_url="https://example.com")
        
        
        client.base_url = "https://api.production.com"
        
        
        assert client.base_url == "https://api.production.com"