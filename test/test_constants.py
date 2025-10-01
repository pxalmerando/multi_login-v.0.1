import pytest
from src.constants import APIEndpoints


class TestAPIEndpoints:
    """Test suite for APIEndpoints class"""
    
    @pytest.fixture(autouse=True)
    def reset_config(self):
        """Reset configuration before each test"""
        APIEndpoints.config = {
            'host': 'localhost',
            'port': 45001,
            'base_path': '/api/'
        }
        yield
        
        APIEndpoints.config = {
            'host': 'localhost',
            'port': 45001,
            'base_path': '/api/'
        }
    
    def test_default_config(self):
        """Test default configuration values"""
        assert APIEndpoints.config['host'] == 'localhost'
        assert APIEndpoints.config['port'] == 45001
        assert APIEndpoints.config['base_path'] == '/api/'
    
    def test_configure_host(self):
        """Test configuring only the host"""
        APIEndpoints.configure(host='example.com')
        assert APIEndpoints.config['host'] == 'example.com'
        assert APIEndpoints.config['port'] == 45001
        assert APIEndpoints.config['base_path'] == '/api/'
    
    def test_configure_port(self):
        """Test configuring only the port"""
        APIEndpoints.configure(port=8080)
        assert APIEndpoints.config['host'] == 'localhost'
        assert APIEndpoints.config['port'] == 8080
        assert APIEndpoints.config['base_path'] == '/api/'
    
    def test_configure_base_path(self):
        """Test configuring only the base path"""
        APIEndpoints.configure(base_path='/v2/api/')
        assert APIEndpoints.config['host'] == 'localhost'
        assert APIEndpoints.config['port'] == 45001
        assert APIEndpoints.config['base_path'] == '/v2/api/'
    
    def test_configure_all_parameters(self):
        """Test configuring all parameters at once"""
        APIEndpoints.configure(
            host='api.example.com',
            port=443,
            base_path='/v1/'
        )
        assert APIEndpoints.config['host'] == 'api.example.com'
        assert APIEndpoints.config['port'] == 443
        assert APIEndpoints.config['base_path'] == '/v1/'
    
    def test_configure_with_none_values(self):
        """Test that None values don't change configuration"""
        original_config = APIEndpoints.config.copy()
        APIEndpoints.configure(host=None, port=None, base_path=None)
        assert APIEndpoints.config == original_config
    
    def test_get_base_url_default(self):
        """Test get_base_url with default configuration"""
        expected = "http://localhost:45001/api/"
        assert APIEndpoints.get_base_url() == expected
    
    def test_get_base_url_custom_config(self):
        """Test get_base_url with custom configuration"""
        APIEndpoints.configure(
            host='api.example.com',
            port=8080,
            base_path='/v2/'
        )
        expected = "http://api.example.com:8080/v2/"
        assert APIEndpoints.get_base_url() == expected
    
    def test_launcher_endpoint_default(self):
        """Test LAUNCHER endpoint with default configuration"""
        expected = "http://localhost:45001/api/launcher"
        assert APIEndpoints.LAUNCHER() == expected
    
    def test_launcher_endpoint_custom_config(self):
        """Test LAUNCHER endpoint with custom configuration"""
        APIEndpoints.configure(host='test.com', port=9000, base_path='/custom/')
        expected = "http://test.com:9000/custom/launcher"
        assert APIEndpoints.LAUNCHER() == expected
    
    def test_client_endpoint(self):
        """Test CLIENT endpoint is always constant"""
        expected = "https://api.multilogin.com/user/signin"
        assert APIEndpoints.CLIENT() == expected
        
        
        APIEndpoints.configure(host='different.com', port=9999)
        assert APIEndpoints.CLIENT() == expected
    
    def test_multiple_reconfigurations(self):
        """Test multiple configuration changes"""
        APIEndpoints.configure(host='first.com')
        assert APIEndpoints.config['host'] == 'first.com'
        
        APIEndpoints.configure(host='second.com')
        assert APIEndpoints.config['host'] == 'second.com'
        
        APIEndpoints.configure(port=7777)
        assert APIEndpoints.config['host'] == 'second.com'
        assert APIEndpoints.config['port'] == 7777
    
    @pytest.mark.parametrize("host,port,base_path,expected", [
        ('localhost', 45001, '/api/', 'http://localhost:45001/api/'),
        ('example.com', 80, '/', 'http://example.com:80/'),
        ('api.test.com', 443, '/v1/api/', 'http://api.test.com:443/v1/api/'),
        ('192.168.1.1', 3000, '/api/v2/', 'http://192.168.1.1:3000/api/v2/'),
    ])
    def test_get_base_url_parametrized(self, host, port, base_path, expected):
        """Test get_base_url with various configurations"""
        APIEndpoints.configure(host=host, port=port, base_path=base_path)
        assert APIEndpoints.get_base_url() == expected
    
    def test_base_path_without_trailing_slash(self):
        """Test base path without trailing slash"""
        APIEndpoints.configure(base_path='/api')
        expected = "http://localhost:45001/api/launcher"
        assert APIEndpoints.LAUNCHER() == expected