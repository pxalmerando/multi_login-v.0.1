class APIEndpoints:
    """
        A class used to store and manage the configuration of the API endpoints.
        
        Attributes:
            config (Dict[str, Any]): The configuration of the API endpoints.
    """
    config = {
        'host': 'localhost',
        'port': 45001,
        'base_path': '/api/'
    }
    
    @classmethod
    def configure(cls, host=None, port=None, base_path=None):
        """
            Update the configuration of the API endpoints.
            
            Args:
                host (str): The host of the API endpoints. Defaults to None.
                port (int): The port of the API endpoints. Defaults to None.
                base_path (str): The base path of the API endpoints. Defaults to None.
        """
        if host: cls.config['host'] = host
        if port: cls.config['port'] = port
        if base_path: cls.config['base_path'] = base_path
    
    @classmethod
    def get_base_url(cls):
        """
            Get the base URL of the API endpoints.
            
            Returns:
                str: The base URL of the API endpoints.
        """
        return f"http://{cls.config['host']}:{cls.config['port']}{cls.config['base_path']}"
    
    @classmethod
    def LAUNCHER(cls):
        """
            Get the URL of the LAUNCHER endpoint.
            
            Returns:
                str: The URL of the LAUNCHER endpoint.
        """
        base = cls.get_base_url()
        if not base.endswith('/'):
            base += '/'
        return f"{base}launcher"
    
    @classmethod
    def CLIENT(cls):
        """
            Get the URL of the CLIENT endpoint.
            
            Returns:
                str: The URL of the CLIENT endpoint.
        """
        return f"https://api.multilogin.com/user/signin"

