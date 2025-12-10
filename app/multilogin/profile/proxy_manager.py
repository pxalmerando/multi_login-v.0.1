import random

from app.multilogin.profile.base_manager import BaseManagerApi

class ProxyManager(BaseManagerApi):

    def __init__(self, api_url: str, api_token: str) -> None:
        """Initialize the ProxyManager.

        Simply forwards parameters to the BaseManagerApi constructor.

        Args:
            api_url: Base URL for the API endpoints.
            api_token: API token used for authenticated requests.
        """
        super().__init__(api_url, api_token)

    async def generate_proxy(self) -> dict:
        
        protocol = ['socks5', 'http']
        sesionType = ['rotating', 'sticky']

        payload = {
            "country": "any",
            "protocol": random.choice(protocol),
            "sessionType": random.choice(sesionType)
        }

        result = await self.request('POST', 'v1/proxy/connection_url', include_auth=True, json=payload)
        data = result.get('data')
        host, port, username, password = data.split(':', 4)

        return {
            "username": username,
            "password": password,
            "host": host,
            "port": port
        }
    
    async def fetch_proxy_data(self):
        return await self.request('GET', 'v1/user', include_auth=True)