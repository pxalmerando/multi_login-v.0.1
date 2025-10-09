import requests
from typing import Dict, Any
class HttpClient:
    """
        A class used to make HTTP requests to a given base URL.

        Attributes:
            base_url (str): Base URL to make requests to

        Methods:
            get(endpoint, **kwargs): Make a GET request to the given endpoint
            post(endpoint, **kwargs): Make a POST request to the given endpoint
            put(endpoint, **kwargs): Make a PUT request to the given endpoint
            delete(endpoint, **kwargs): Make a DELETE request to the given endpoint
            patch(endpoint, **kwargs): Make a PATCH request to the given endpoint
    """

    def __init__(self, base_url: str):
        self.base_url = base_url


    def _full_url(self, endpoint: str) -> str:
        return f"{self.base_url.rstrip('/')}/{endpoint.lstrip('/')}"
    
    def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """
        Make an HTTP request to the given endpoint using the specified method.

        Args:
            method (str): HTTP method to use (e.g. GET, POST, PUT, DELETE)
            endpoint (str): Endpoint to make the request to
            **kwargs: Additional keyword arguments to pass to the requests library

        Returns:
            Dict[str, Any]: JSON response from the server
        """

        url = self._full_url(endpoint)

        try:
            response = requests.request(method, url, **kwargs)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            error_json = response.json()
            print(f"Request failed with status code {response.status_code}: {error_json}")

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
