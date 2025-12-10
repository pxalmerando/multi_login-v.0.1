from typing import Optional
import logging
import random

from app.multilogin.services.base_manager import BaseManagerApi

logger = logging.getLogger(__name__)


class FolderManager(BaseManagerApi):
    """
        A class used to interact with the API endpoints related to folders.

        Attributes:
            api_url (str): The URL of the API.
            api_token (str): The authentication token for the API.
    """

    def __init__(self, api_url: str, api_token: str):
        """
            Initialize the FolderManager.

            Args:
                api_url (str): The URL of the API.
                api_token (str): The authentication token for the API.
        """
        super().__init__(api_url, api_token)
        self._folder_id_cache: Optional[str] = None

    async def get_or_create_default_folder(self, folder_name: Optional[str] = None) -> str:
        """
        Get existing folder or create a new one.
        Results are cached to avoid repeated API calls.
        
        Args:
            folder_name (str, optional): Name for new folder if creation is needed.
                                        Defaults to a random folder name.
        
        Returns:
            str: The folder ID
            
        Raises:
            ValueError: If folder creation fails or returns invalid data
        """
        
        if self._folder_id_cache is not None:
            logger.debug(f"[FolderManager] Using cached folder ID: {self._folder_id_cache}")
            return self._folder_id_cache
        
        try:
            
            folder_ids = await self.get_folder_ids()
            if folder_ids:
                self._folder_id_cache = folder_ids[0]
                logger.info(f"[FolderManager] Using existing folder: {self._folder_id_cache}")
                return self._folder_id_cache
            
            
            folder_name = folder_name or f"Folder {random.randint(1, 100)}"
            new_folder = await self.create_folder(folder_name)
            
            data = new_folder.get('data', {})
            folder_id = data.get('id')
            
            if not folder_id:
                raise ValueError(f"[FolderManager] Failed to get folder ID from create response")
            
            self._folder_id_cache = folder_id
            logger.info(f"[FolderManager] Created new folder '{folder_name}': {folder_id}")
            return folder_id
            
        except Exception as e:
            logger.exception(f"[FolderManager] Failed to get or create folder: {e}")
            raise
    
    def clear_cache(self) -> None:
        """Clear the cached folder ID"""
        self._folder_id_cache = None
        logger.debug(f"[FolderManager] Folder ID cache cleared")

    async def create_folder(self, folder_name: str, comment: str = None):
        """
            Create a new folder in the workspace.

            Args:
                folder_name (str): The name of the new folder.
                comment (str): The comment for the new folder. Defaults to None.

            Returns:
                dict: The response from the server.
        """
        json = {
            'name': folder_name,
            'comment': comment
        }
        return await self.request('POST', 'workspace/folder_create', include_auth=True, json=json)
    
    async def list_folders(self):
        """
            List all folders in the workspace.

            Returns:
                dict: The response from the server.
        """
        return await self.request('GET', 'workspace/folders', include_auth=True)
    
    async def get_folder_name(self) -> list:
        try:
            list_response = await self.list_folders()
            folders = [folder.get('name') for folder in list_response.get('data', {}).get('folders', [])]
            return folders
        except ValueError as e:
            logger.exception(f"[FolderManager] Error retrieving folder names: {e}")
            return []
    
    async def get_folder_ids(self) -> list:
        try:
            list_response = await self.list_folders()
            folders = [folder.get('folder_id') for folder in list_response.get('data', {}).get('folders', [])]
            return folders
        except ValueError as e:
            logger.exception(f"[FolderManager] Error retrieving folder IDs: {e}")
            return []
    async def update_folder(self, folder_id: str, new_folder_name: str, comment: str = None):
        """
            Update the name and comment of a folder.

            Args:
                folder_id (str): The ID of the folder to update.
                new_folder_name (str): The new name of the folder.
                comment (str): The new comment for the folder. Defaults to None.

            Returns:
                dict: The response from the server.
        """
        json = {
            'folder_id': folder_id,
            'name': new_folder_name,
            'comment': comment
        }
        return await self.request('POST', 'workspace/folder_update', include_auth=True, json=json)
    
    async def delete_folder(self, folder_id: str):
        """
            Delete a folder in the workspace.

            Args:
                folder_id (str): The ID of the folder to delete.

            Returns:
                dict: The response from the server.
        """
        json = {
            'ids': [folder_id]
        }
        return await self.request('POST', 'workspace/folders_remove', include_auth=True, json=json)