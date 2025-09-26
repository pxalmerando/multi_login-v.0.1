import requests
from typing import Dict, Any
class HttpClient:

    def __init__(self, base_url: str, timeout: int = 10):
        self.base_url = base_url
        self.timeout = timeout


    def _full_url(self, endpoint: str) -> str:
        return f"{self.base_url.rstrip('/')}/{endpoint.lstrip('/')}"
    
    def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:

        url = self._full_url(endpoint)

        if 'timeout' not in kwargs:
            kwargs['timeout'] = self.timeout

        response = requests.request(method, url, **kwargs)
        response.raise_for_status()
        return response.json()
    
    def get(self, endpoint: str, **kwargs) -> Dict[str, Any]:
        return self._make_request('GET', endpoint, **kwargs)
    
    def post(self, endpoint: str, **kwargs) -> Dict[str, Any]:
        return self._make_request('POST', endpoint, **kwargs)
    
    def put(self, endpoint: str, **kwargs) -> Dict[str, Any]:
        return self._make_request('PUT', endpoint, **kwargs)
    
    def delete(self, endpoint: str, **kwargs) -> Dict[str, Any]:
        return self._make_request('DELETE', endpoint, **kwargs)
    
    def patch(self, endpoint: str, **kwargs) -> Dict[str, Any]:
        return self._make_request('PATCH', endpoint, **kwargs)