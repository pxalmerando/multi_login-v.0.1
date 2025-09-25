class APIEndpoints:
    config = {
        'host': 'localhost',
        'port': 45001,
        'base_path': '/api/'
    }
    
    @classmethod
    def configure(cls, host=None, port=None, base_path=None):
        """Update configuration"""
        if host: cls.config['host'] = host
        if port: cls.config['port'] = port
        if base_path: cls.config['base_path'] = base_path
    
    @classmethod
    def get_base_url(cls):
        return f"http://{cls.config['host']}:{cls.config['port']}{cls.config['base_path']}"
    
    @classmethod
    def LAUNCHER(cls):
        return f"{cls.get_base_url()}launcher"
    
    @classmethod
    def CLIENT(cls):
        return f"https://api.multilogin.com/user/signin"
