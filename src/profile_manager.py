from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any, List
from base_manager import BaseManagerApi

@dataclass
class ScreenConfig:
    width: int = 1920
    height: int = 1080
    pixel_ratio: float = 1.0

@dataclass
class ProxyConfig:
    type: Optional[str] = None
    host: Optional[str] = None
    port: Optional[int] = None
    username: Optional[str] = None
    password: Optional[str] = None
    save_traffic: bool = False
    def is_configured(self) -> bool:
        return bool(self.type and self.host)

@dataclass
class StorageConfig:
    is_local: bool = True
    save_service_worker: bool = True  
@dataclass
class ProfileConfig:
    name: str
    folder_id: str
    profile_id: Optional[str] = None

    browser_type: str = "mimic"
    os_type: str = "windows"
    auto_update_core: bool = True
    times: int = 1
    notes: str = ''

    screen: Optional[ScreenConfig] = None
    proxy: Optional[ProxyConfig] = None

class ProfileManager(BaseManagerApi):
    def __init__(self, base_url: str, api_token: str):
        super().__init__(base_url, api_token)
    
    def _should_use_custom_screen(self, config: ProfileConfig) -> bool:
        """Check if custom screen configuration should be used"""
        return config.screen is not None
    
    def _should_use_custom_proxy(self, config: ProfileConfig) -> bool:
        """Check if custom proxy configuration should be used"""
        return config.proxy is not None and config.proxy.is_configured()
    
    def _build_flags(self, config: ProfileConfig) -> Dict[str, str]:
        
        """
            Builds the flags for the profile based on the given configuration.

            Args:
                config (ProfileConfig): The configuration of the profile.

            Returns:
                Dict[str, str]: A dictionary containing the flags for the profile.
        """
        flags = {
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
            "proxy_masking": "disabled",
            "screen_masking": "natural",
            "timezone_masking": "natural",
            "webrtc_masking": "natural",
            "quic_mode": "natural",
            "canvas_noise": "natural",
        }

        if self._should_use_custom_screen(config):
            flags['screen_masking'] = 'custom'

        if self._should_use_custom_proxy(config):
            flags['proxy_masking'] = 'custom'
        
        return flags
    
    def _build_fingerprint(self, config: ProfileConfig) -> Dict[str, Any]:
        """
            Builds the fingerprint for the profile based on the given configuration.

            Args:
                config (ProfileConfig): The configuration of the profile.

            Returns:
                Dict[str, Any]: A dictionary containing the fingerprint for the profile.
        """
        
        fingerprint = {}
        if self._should_use_custom_screen(config):
            fingerprint['screen'] = asdict(config.screen)
        return fingerprint
    
    def _build_storage(self) -> Dict[str, Any]:
        """
            Builds the storage configuration for the profile based on the default configuration.

            Returns:
                Dict[str, Any]: A dictionary containing the storage configuration for the profile.
        """
        return asdict(StorageConfig())

    def _build_proxy(self, config: ProfileConfig) -> Dict[str, Any]:
        """
            Builds the proxy configuration for the profile based on the given configuration.

            If the given configuration has a custom proxy configuration, it is used. Otherwise, None is returned.

            Args:
                config (ProfileConfig): The configuration of the profile.

            Returns:
                Dict[str, Any]: A dictionary containing the proxy configuration for the profile, or None if no custom proxy configuration is used.
        """
        if self._should_use_custom_proxy(config):
            return asdict(config.proxy)
        return None

    def _build_parameters(self, config: ProfileConfig) -> Dict[str, Any]:
        """
            Builds the parameters for the profile based on the given configuration.

            Args:
                config (ProfileConfig): The configuration of the profile.

            Returns:
                Dict[str, Any]: A dictionary containing the parameters for the profile.
        """
        parameters = {
            'flags': self._build_flags(config),
            'storage': self._build_storage(),
            'fingerprint': self._build_fingerprint(config),
        }

        proxy_data = self._build_proxy(config)
        if proxy_data:
            parameters['proxy'] = proxy_data

        return parameters
    
    def _validate_create_config(self, config: ProfileConfig) -> None:
        """
            Validates the configuration of a profile when creating a new profile.

            Args:
                config (ProfileConfig): The configuration of the profile to create.

            Raises:
                ValueError: If name or folder_id is not set, or if profile_id is set.
        """

        if not config.name or not config.folder_id:
            raise ValueError("Name and folder_id are required to create a profile.")
        
        if config.profile_id:
            raise ValueError("Profile ID should not be set when creating a new profile.")
        
    def _validate_update_config(self, profile_id: str) -> None:
        """
            Validates the configuration of a profile when updating an existing profile.

            Args:
                profile_id (str): The ID of the profile to update.

            Raises:
                ValueError: If profile_id is not set.
        """

        if not profile_id:
            raise ValueError("Profile ID is required for updates")
        
    def _build_common_data(self, config: ProfileConfig) -> Dict[str, Any]:
        """
            Builds the common data required for creating or updating a profile.

            Args:
                config (ProfileConfig): The configuration of the profile to create or update

            Returns:
                Dict[str, Any]: A dictionary containing the common data required for creating or updating a profile
        """
        return {
            'name': config.name,
        }

    def _build_create_data(self, config: ProfileConfig) -> Dict[str, Any]:
        """
            Builds the data required for creating a new profile.

            Args:
                config (ProfileConfig): The configuration of the profile to create

            Returns:
                Dict[str, Any]: A dictionary containing the data required for creating a new profile.
        """
        return {
            'browser_type': config.browser_type,
            'folder_id': config.folder_id,
            'os_type': config.os_type,
            'auto_update_core': config.auto_update_core,
            'times': config.times,
            'notes': config.notes
        }
    
    def _build_update_data(self, config: ProfileConfig) -> Dict[str, Any]:
        """
            Builds the data required for updating a profile.

            Args:
                config (ProfileConfig): The configuration of the profile.

            Returns:
                Dict[str, Any]: The data required for updating a profile.
        """
        return {
            'profile_id': config.profile_id
        }

    def _build_profile_data(self, config: ProfileConfig, is_update: bool = False) -> Dict[str, Any]:
        """
            Build the data required for creating or updating a profile.

            Args:
                config (ProfileConfig): The configuration of the profile.
                is_update (bool): Whether the profile is being updated or created. Defaults to False.

            Returns:
                Dict[str, Any]: The data required for creating or updating a profile.
        """
        data = self._build_common_data(config)
        
        if is_update:
            if not config.profile_id:
                raise ValueError("Profile ID is required for updates")
            data.update(self._build_update_data(config))

        else:
            if config.profile_id:
                raise ValueError("Profile ID should not be set when creating a new profile")
            data.update(self._build_create_data(config))

        data['parameters'] = self._build_parameters(config)
        return data
    
    def create_profile(self, config: ProfileConfig) -> Dict[str, Any]:        
        """
            Create a new profile

            Args:
                config (ProfileConfig): The configuration of the profile to create

            Returns:
                dict: The response from the server
        """
        
        self._validate_create_config(config)
        json = self._build_profile_data(config)
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
    
    def update_profile(self, profile_id: str, config: ProfileConfig) -> Dict[str, Any]:
        """
            Update a profile

            Args:
                profile_id (str): The ID of the profile to update
                config (ProfileConfig): The configuration of the profile to update

            Returns:
                Dict[str, Any]: The response from the server
        """

        self._validate_update_config(profile_id)
        config.profile_id = profile_id
        json = self._build_profile_data(config, is_update=True)
        return self.request('POST', 'profile/update', include_auth=True, json=json)

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

