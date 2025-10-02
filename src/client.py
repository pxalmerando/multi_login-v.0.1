from .token_manager import TokenManager
class Client:
    def __init__(self, token_manager: TokenManager):
        self.token_manager = token_manager
    def ensure_authenticated(self):
        self.token_manager.get_tokens()