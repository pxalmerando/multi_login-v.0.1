from base_manager import BaseManagerApi
class FolderManager(BaseManagerApi):
    def __init__(self, api_url: str, api_token: str):
        super().__init__(api_url, api_token)

        
    def create_folder(self, folder_name: str, comment: str = None):
        json = {
            'name': folder_name,
            'comment': comment
        }
        return self.request('POST', 'workspace/folder_create', include_auth=True, json=json)
    
    def list_folders(self):
        return self.request('GET', 'workspace/folders', include_auth=True)
    
    def update_folder(self, folder_id: str, new_folder_name: str, comment: str = None):
        json = {
            'folder_id': folder_id,
            'name': new_folder_name,
            'comment': comment
        }
        return self.request('POST', 'workspace/folder_update', include_auth=True, json=json)
    
    def delete_folder(self, folder_id: str):
        json = {
            'ids': [folder_id]
        }
        return self.request('POST', 'workspace/folders_remove', include_auth=True, json=json)