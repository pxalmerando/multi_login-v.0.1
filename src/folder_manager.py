from .base_manager import BaseManagerApi
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
    
    def create_folder(self, folder_name: str, comment: str = None):
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
        return self.request('POST', 'workspace/folder_create', include_auth=True, json=json)
    
    def list_folders(self):
        """
            List all folders in the workspace.

            Returns:
                dict: The response from the server.
        """
        return self.request('GET', 'workspace/folders', include_auth=True)
    
    def get_folder_name(self) -> list:
        try:
            list_response = self.list_folders()
            folders = [folder.get('name') for folder in list_response.get('data', {}).get('folders', [])]
            return folders
        except ValueError as e:
            print(f"Error retrieving folder names: {e}")
            return []
    
    def get_folder_id(self) -> list:
        try:
            list_response = self.list_folders()
            folders = [folder.get('folder_id') for folder in list_response.get('data', {}).get('folders', [])]
            return folders
        except ValueError as e:
            print(f"Error retrieving folder IDs: {e}")
            return []
    def update_folder(self, folder_id: str, new_folder_name: str, comment: str = None):
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
        return self.request('POST', 'workspace/folder_update', include_auth=True, json=json)
    
    def delete_folder(self, folder_id: str):
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
        return self.request('POST', 'workspace/folders_remove', include_auth=True, json=json)
