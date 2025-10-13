from typing import Dict, Any, List, Optional
from .base_manager import BaseManagerApi


class ProfileManager(BaseManagerApi):
    """Manager for creating, listing, updating and deleting profiles.

    This class wraps profile-related API calls and provides helper methods to
    build request payloads and extract useful data from responses.

    Args:
        api_url: Base URL for the API endpoints (e.g. "https://api.example.com/").
        api_token: API token used for authenticated requests.
    """

    BROWSER_TYPE = 'mimic'
    OS_TYPE = 'windows'
    DEFAULT_LIMIT = 100
    DEFAULT_OFFSET = 0
    DEFAULT_SEARCH_TEXT = ''
    DEFAULT_SORT = 'asc'
    DEFAULT_ORDER_BY = 'created_at'
    DEFAULT_STORAGE_TYPE = 'all'


    def __init__(self, api_url: str, api_token: str) -> None:
        """Initialize the ProfileManager.

        Simply forwards parameters to the BaseManagerApi constructor.

        Args:
            api_url: Base URL for the API endpoints.
            api_token: API token used for authenticated requests.
        """
        super().__init__(api_url, api_token)
    def _get_profile_field(self, folder_id: str, field_name: str):
        """Helper to get a specific field from a profile by id.

        Args:
            profile_id: ID of the profile to query.
            field: The field name to extract from the profile data.

        Returns:
            The value of the requested field, or None if not found.
        """

        if not folder_id:
            raise ValueError("folder_id must be provided")
        if not field_name:
            raise ValueError("field_name must be provided")
        try:
            response = self.list_profiles(folder_id=folder_id)
            profiles = response.get('data', {}).get('profiles', [])
            return [profile.get(field_name, '') for profile in profiles]
        except Exception as e:
            print(f"Failed to get field '{field_name}' for profile {folder_id}: {e}")
            return []
    def _build_profile_payload(
        self,
        name: str,
        folder_id: str,
        browser_type: str,
        os_type: str,
        proxy: Optional[Dict[str, Any]],
        profile_id: Optional[str] = None,
        include_full_parameters: bool = False
    ) -> Dict[str, Any]:
        """Build the JSON payload used when creating or updating a profile.

        This helper centralizes payload construction so create/update behave
        consistently. It will include default parameter flags when
        ``include_full_parameters`` is True, attach proxy settings when
        provided, and optionally include an existing ``profile_id`` for
        updates.

        Args:
            name: Human-readable profile name.
            folder_id: ID of the folder to which the profile belongs.
            browser_type: Browser engine type (e.g. "mimic").
            os_type: Operating system type (e.g. "windows").
            proxy: Optional proxy configuration dictionary to attach to the
                profile parameters.
            profile_id: Optional existing profile id for update operations.
            include_full_parameters: Whether to populate the full default
                parameters block (flags, fingerprint, storage).

        Returns:
            A dictionary ready to be sent as JSON in an API request.
        """
        payload = {
            'name': name,
            'folder_id': folder_id,
            'browser_type': browser_type,
            'os_type': os_type,
        }
        if profile_id:
            payload['profile_id'] = profile_id
        if include_full_parameters:
            proxy_masking = "disabled" if not proxy else "custom"
            payload['parameters'] = {
                'flags': {
                    'proxy_masking': proxy_masking,
                    'audio_masking': 'natural',
                    'fonts_masking': 'natural',
                    'geolocation_masking': 'mask',
                    'geolocation_popup': 'prompt',
                    'graphics_masking': 'natural',
                    'graphics_noise': 'natural',
                    'localization_masking': 'natural',
                    'media_devices_masking': 'natural',
                    'navigator_masking': 'natural',
                    'ports_masking': 'natural',
                    'screen_masking': 'natural',
                    'timezone_masking': 'natural',
                    'webrtc_masking': 'natural',
                },
                'fingerprint': {},
                'storage': {'is_local': True},
            }
        elif proxy:
            payload['parameters'] = {
                'flags': {'proxy_masking': 'custom'}
            }
        if proxy:
            if 'parameters' not in payload:
                payload['parameters'] = {}
            payload['parameters']['proxy'] = proxy
        return payload
    def create_profile(
        self, 
        folder_id: str,
        name: str, 
        browser_type: str = BROWSER_TYPE, 
        os_type: str = OS_TYPE, 
        proxy: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create a new profile.

        Constructs the profile payload using sensible defaults and sends a
        POST request to the profile creation endpoint.

        Args:
            folder_id: ID of the folder to create the profile in.
            name: Name for the new profile.
            browser_type: Browser engine type. Defaults to "mimic".
            os_type: Operating system type. Defaults to "windows".
            proxy: Optional proxy configuration to attach to the profile.
                Example of proxy configuration:
                "proxy": {
                    "type": "http",
                    "host": "hellos.com",
                    "username": "angelou",
                    "password": "pass",
                    "save_traffic": "true"
                }

        Returns:
            The parsed JSON response from the API as a dictionary.
        """
        payload = self._build_profile_payload(
            name=name,
            folder_id=folder_id,
            browser_type=browser_type,
            os_type=os_type,
            proxy=proxy,
            include_full_parameters=True,
        )
        return self.request('POST', 'profile/create', include_auth=True, json=payload)
    def list_profiles(
        self, 
        folder_id: str, 
        is_removed: bool = False, 
        limit: int = DEFAULT_LIMIT, 
        offset: int = DEFAULT_OFFSET, 
        search_text: str = DEFAULT_SEARCH_TEXT, 
        storage_type: str = DEFAULT_STORAGE_TYPE, 
        order_by: str = DEFAULT_ORDER_BY, 
        sort: str = DEFAULT_SORT
    ) -> Dict[str, Any]:
        """Return a list of profiles for a given folder.

        This method wraps the profile search endpoint. The returned structure
        is the API response dict and may contain pagination metadata under the
        'data' key depending on the server implementation.

        Args:
            folder_id: Folder id to list profiles from.
            is_removed: Whether to include removed profiles. Defaults to False.
            limit: Maximum number of profiles to return. Defaults to 100.
            offset: Pagination offset. Defaults to 0.
            search_text: Optional text to filter profile names.
            storage_type: Storage filter (e.g. 'all').
            order_by: Field to order by. Defaults to 'created_at'.
            sort: Sort direction ('asc' or 'desc'). Defaults to 'asc'.

        Returns:
            API response as a dictionary.
        """
        payload = {
            'is_removed': is_removed,
            'limit': limit,
            'offset': offset,
            'search_text': search_text,
            'folder_id': folder_id,
            'storage_type': storage_type,
            'order_by': order_by,
            'sort': sort,
        }
        return self.request('POST', 'profile/search', include_auth=True, json=payload)
    
    def get_profile_names(self, folder_id: str) -> List[str]:
        """Return a list of profile names for the given folder.

        Args:
            folder_id: ID of the folder to query.

        Returns:
            A list of profile name strings. If an error occurs an empty list is
            returned. Raises ValueError if folder_id is falsy.
        """
        return self._get_profile_field(folder_id, 'name')
    def get_profile_ids(self, folder_id: str) -> List[str]:
        """Return a list of profile IDs for the given folder.

        Args:
            folder_id: ID of the folder to query.

        Returns:
            A list of profile id strings. If an error occurs an empty list is
            returned. Raises ValueError if folder_id is falsy.
        """
        return self._get_profile_field(folder_id, 'id')
    def update_profile(
        self,
        profile_id: str,
        folder_id: str,
        name: str,
        browser_type: str = BROWSER_TYPE,
        os_type: str = OS_TYPE,
        proxy: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Update an existing profile.

        Builds an update payload that includes full parameters and the
        provided proxy configuration (if any), then sends it to the profile
        update endpoint.

        Args:
            profile_id: ID of the profile to update.
            folder_id: ID of the folder containing the profile.
            name: New name for the profile.
            browser_type: Browser engine type. Defaults to "mimic".
            os_type: Operating system type. Defaults to "windows".
            proxy: Optional proxy configuration to attach to the profile.

        Returns:
            The parsed JSON response from the API as a dictionary.
        """
        payload = self._build_profile_payload(
            name=name,
            folder_id=folder_id,
            browser_type=browser_type,
            os_type=os_type,
            proxy=proxy,
            profile_id=profile_id,
            include_full_parameters=True,
        )
        return self.request("POST", "profile/update", include_auth=True, json=payload)
    def delete_profile(
        self, 
        profile_id: str, 
        is_permanent: bool = True
    ) -> Dict[str, Any]:
        """Delete (or soft-delete) a profile by id.

        Args:
            profile_id: ID of the profile to remove.
            is_permanent: If True the profile will be permanently deleted,
                otherwise it will be marked as removed/soft-deleted.

        Returns:
            The parsed JSON response from the API as a dictionary. On
            unexpected failure an empty dict is returned.
        """
        try:
            payload = {
                'ids': [profile_id],
                'permanently': is_permanent
            }
            return self.request('POST', 'profile/remove', include_auth=True, json=payload)
        except Exception as e:
            print(f"Failed to delete profile {profile_id}: {e}")
            return {}