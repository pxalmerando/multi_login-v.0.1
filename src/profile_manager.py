from typing import Dict, Any, List
from base_manager import BaseManagerApi

class ProfileManager(BaseManagerApi):
    def __init__(self, base_url: str, api_token: str):
        super().__init__(base_url, api_token)    
    
    def create_profile(
            self, 
            folder_id: str,
            name: str, 
            browser_type: str = "mimic", 
            os_type: str = "windows", 
            proxy: dict = None
        ) -> Dict[str, Any]:
        """
            Create a new profile.

            Args:
                folder_id (str): The ID of the folder in which the profile will be created.
                name (str): The name of the profile.
                browser_type (str): The type of browser to use. Defaults to "mimic".
                os_type (str): The type of operating system to use. Defaults to "windows".
                proxy (dict): The proxy configuration to use. Defaults to None.

            Example for proxy configuration:
            proxy_config = {
                "type": "http",
                "host": "proxyhost.com",
                "port": 8081,
                "username": "user",
                "password": "pass",
                "save_traffic": True
            }

            Returns:
                dict: The response from the server.
        """
        json = {
            'name': name,
            'folder_id': folder_id,
            'browser_type': browser_type,
            'os_type': os_type,
        }

        if proxy:
            json['parameters'] = {
                'flags': {'proxy_masking': 'custom'},
                'proxy': proxy
            }

        return self.request('POST', 'profile/create', include_auth=True, json=json)
    
    def list_profiles(self, folder_id: str, 
                      is_removed: bool = False, 
                      limit: int = 10, offset: int = 0, 
                      search_text: str = '', 
                      storage_type: str = 'all', 
                      order_by: str = 'created_at', 
                      sort: str = 'asc'
                    ) -> Dict[str, Any]:
        """
            List profiles

            Args:
                folder_id (str): The ID of the folder to list profiles from
                is_removed (bool): Whether to include removed profiles in the result (default: False)
                limit (int): The maximum number of profiles to return (default: 10)
                offset (int): The offset from which to start listing profiles (default: 0)
                search_text (str): The text to search for in the profile names (default: empty string)
                storage_type (str): The type of storage to filter by (default: 'all')
                order_by (str): The field to order the profiles by (default: 'created_at')
                sort (str): The direction in which to sort the profiles (options: 'asc', 'desc')

            Returns:
                Dict[str, Any]: The response from the server
        """
        
        json = {
            'is_removed': is_removed,
            'limit': limit,
            'offset': offset,
            'search_text': search_text,
            'folder_id': folder_id,
            'storage_type': storage_type,
            'order_by': order_by,
            'sort': sort,
        }

        response = self.request('POST', 'profile/search', include_auth=True, json=json)
        return response
    def get_profile_names(self, folder_id: str) -> List[str]:
        if not folder_id:
            return []
        try:
            list_response = self.list_profiles(folder_id=folder_id)
            data = list_response.get('data', {}).get('profiles', [])
            return [name.get('name') for name in data]
        except Exception as e:
            print(f"Failed to get profile names for folder {folder_id} {e}")
            return []
    
    def get_profile_ids(
        self, 
        folder_id: str
    ) -> List[str]:
        
        try:
            response = self.list_profiles(folder_id=folder_id)
            profiles = response.get('data', {}).get('profiles', [])
            return [profile.get('id') for profile in profiles if profile.get('id')]
        except Exception as e:
            print(f"Failed to get profile ids for folder {folder_id} {e}")
            return []
    def update_profile(
        self,
        profile_id: str,
        folder_id: str,
        name: str,
        browser_type: str = "mimic",
        os_type: str = "windows",
        proxy: dict = None,
    ) -> Dict[str, Any]:
        """
            Update a profile.

            Args:
                profile_id (str): The ID of the profile to update
                folder_id (str): The ID of the folder to which the profile belongs
                name (str): The new name for the profile
                browser_type (str): The type of browser to use (default: "mimic")
                os_type (str): The type of operating system to use (default: "windows")
                proxy (dict): The proxy configuration to use (default: None)

            Example for proxy configuration:
            proxy_config = {
                "type": "http",
                "host": "proxyhost.com",
                "port": 8081,
                "username": "user",
                "password": "pass",
                "save_traffic": True
            }

            Returns:
                Dict[str, Any]: The response from the server

            Raises:
                ValueError: If profile_id is not provided
        """
        
        proxy_masking = "disabled" if not proxy else "custom"

        json_data = {
            "profile_id": profile_id,
            "name": name,
            "folder_id": folder_id,
            "browser_type": browser_type,
            "os_type": os_type,
            "parameters": {
                "flags": {
                    "proxy_masking": proxy_masking,
                    "audio_masking": "natural",
                    "fonts_masking": "natural",
                    "geolocation_masking": "mask",
                    "geolocation_popup": "prompt",
                    "graphics_masking": "natural",
                    "graphics_noise": "natural",
                    "localization_masking": "natural",
                    "media_devices_masking": "natural",
                    "navigator_masking": "natural",
                    "ports_masking": "natural",
                    "screen_masking": "natural",
                    "timezone_masking": "natural",
                    "webrtc_masking": "natural",
                },
                "fingerprint": {},
                "storage": {"is_local": True},
            },
        }

        if proxy:
            json_data["parameters"]["proxy"] = proxy

        print(f"Updating profile with data: {json_data}")
        return self.request("POST", "profile/update", include_auth=True, json=json_data)


    def delete_profile(self, profile_id: str, is_permanent: bool = True) -> Dict[str, Any]:
        """
            Delete a profile

            Args:
                profile_id (str): The ID of the profile to delete
                is_permanent (bool): Whether to delete the profile permanently.
                    Defaults to True.

            Returns:
                Dict[str, Any]: A dictionary containing the response from the API.

            Raises:
                ValueError: If profile_id is empty or None.
        """
        
        try:
            json = {
                'ids': [
                    profile_id
                ],
                'permanently': is_permanent
            }
            response = self.request('POST', 'profile/remove', include_auth=True, json=json)
            return response
        except ValueError as e:
            print(f"Failed to delete profile {profile_id} {e}")
            return {}

