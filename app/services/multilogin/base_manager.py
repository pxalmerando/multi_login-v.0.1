from app.utils.http_client import HttpClient
class BaseManagerApi(HttpClient):
    def __init__(self, base_url: str, api_token: str):
        self.api_token = api_token
        super().__init__(base_url)
    def _get_headers(self, include_auth: bool = False) -> dict:

        headers =  {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        }
            
        if include_auth and self.api_token:
            headers['Authorization'] = f"Bearer {self.api_token}"

        return headers
    
    async def request(self, method: str, endpoint: str, include_auth: bool = False, **kwargs) -> dict:
        headers = self._get_headers(include_auth)
        return await self._make_request(method, endpoint, headers=headers, **kwargs)