import json, os
from .auth import UserAuth
class TokenManager:

    def __init__(self, user_auth: UserAuth, token_path: str = 'token.json'):
        self.token_path = token_path
        self.user_auth = user_auth

    def load_tokens(self):

        if os.path.exists(self.token_path):
            with open(self.token_path, 'r') as token:
                return json.load(token)

        return None

    def save(self, tokens: dict):

        with open(self.token_path, 'w') as token:
            json.dump(tokens, token)

    def get_tokens(self):
        
        tokens = self.load_tokens()

        if tokens:
            self.user_auth.set_tokens(
                access_token=tokens['access_token'],
                refresh_token=tokens['refresh_token'],
                token_expiration=tokens['token_expiration']
            )

            if not self.user_auth.is_expired():
                return self.user_auth.to_dict()
            
        self.user_auth.login()
        tokens = self.user_auth.to_dict()
        self.save(tokens)
        return tokens