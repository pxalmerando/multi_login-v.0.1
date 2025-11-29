import json, os
from .auth_service import UserAuth
class TokenManager:
    """
        Class to manage authentication tokens.

        Args:
            user_auth (UserAuth): An instance of UserAuth used to login.
            token_path (str): The path to the file where tokens are stored. Defaults to 'tokens.json'.
    """

    def __init__(self, user_auth: UserAuth, token_path: str = 'tokens.json'):
        self.token_path = token_path
        self.user_auth = user_auth

    def load_tokens(self):
        """
            Loads tokens from a file at the given path. If the file does not exist, returns None.
            
            Returns:
                dict: A dictionary containing the access token, refresh token, and token expiration time.
        """
        if os.path.exists(self.token_path):
            with open(self.token_path, 'r') as token:
                return json.load(token)

        return None

    def save(self, tokens: dict):
        """
            Saves the given tokens to a file at the given path.

            Args:
                tokens (dict): A dictionary containing the access token, refresh token, and token expiration time.
        """
        with open(self.token_path, 'w') as token:
            json.dump(tokens, token)

    async def get_tokens(self):
        """
            Retrieves authentication tokens from storage or by calling the UserAuth login method.

            Returns:
                dict: A dictionary containing the access token, refresh token, and token expiration time.
        """
        tokens = self.load_tokens()

        if tokens:
            self.user_auth.set_tokens(
                access_token=tokens['access_token'],
                refresh_token=tokens['refresh_token'],
                token_expiration=tokens['token_expiration']
            )
            if not self.user_auth.is_expired():
                return self.user_auth.to_dict()
            
        try:
            await self.user_auth.login()
            tokens = self.user_auth.to_dict()
            self.save(tokens)
            return tokens
        except Exception as e:
            raise Exception('Authentication failed.', e)
