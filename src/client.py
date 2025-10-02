from .token_manager import TokenManager
class Client:
    """
        Client class used to interact with the API.

        Args:
            token_manager (TokenManager): Instance of TokenManager used to manage authentication tokens.
    """
    
    def __init__(self, token_manager: TokenManager):
        self.token_manager = token_manager

    def ensure_authenticated(self):
        """
            Ensures that the client has a valid access token before making requests to the API.

            If the token has expired, it will be refreshed using the refresh token.
        """
        self.token_manager.get_tokens()
