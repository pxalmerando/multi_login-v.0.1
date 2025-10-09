import pytest
from unittest.mock import patch
from src.folder_manager import FolderManager
from src.base_manager import BaseManagerApi


@pytest.fixture
def api_credentials():
    """Fixture providing test API credentials."""
    return {
        'api_url': 'https://api.example.com',
        'api_token': 'test_token_12345'
    }


@pytest.fixture
def folder_manager(api_credentials):
    """Fixture providing a FolderManager instance."""
    return FolderManager(
        api_url=api_credentials['api_url'],
        api_token=api_credentials['api_token']
    )


@pytest.fixture
def mock_request(folder_manager):
    """Fixture providing a mocked request method."""
    with patch.object(folder_manager, 'request') as mock:
        yield mock


class TestFolderManagerInitialization:
    """Test cases for FolderManager initialization."""

    def test_initialization_with_valid_credentials(self, api_credentials):
        """Test that FolderManager initializes correctly with valid credentials."""
        manager = FolderManager(
            api_url=api_credentials['api_url'],
            api_token=api_credentials['api_token']
        )
        assert manager is not None
        assert isinstance(manager, FolderManager)

    def test_inherits_from_base_manager(self, folder_manager):
        """Test that FolderManager properly inherits from BaseManagerApi."""
        assert isinstance(folder_manager, BaseManagerApi)


class TestCreateFolder:
    """Test cases for create_folder method."""

    def test_create_folder_with_name_only(self, folder_manager, mock_request):
        """Test creating a folder with only a name."""
        mock_request.return_value = {'id': '123', 'name': 'Test Folder', 'success': True}
        
        result = folder_manager.create_folder('Test Folder')
        
        mock_request.assert_called_once_with(
            'POST',
            'workspace/folder_create',
            include_auth=True,
            json={'name': 'Test Folder', 'comment': None}
        )
        assert result['success'] is True
        assert result['name'] == 'Test Folder'

    def test_create_folder_with_name_and_comment(self, folder_manager, mock_request):
        """Test creating a folder with both name and comment."""
        mock_request.return_value = {'id': '123', 'success': True}
        
        result = folder_manager.create_folder('Test Folder', 'This is a test comment')
        
        mock_request.assert_called_once_with(
            'POST',
            'workspace/folder_create',
            include_auth=True,
            json={'name': 'Test Folder', 'comment': 'This is a test comment'}
        )
        assert result['success'] is True

    @pytest.mark.parametrize('folder_name,comment', [
        ('Project A', None),
        ('Project B', 'Important project'),
        ('Marketing 2024', 'Q4 campaigns'),
        ('Archive', ''),
    ])
    def test_create_folder_various_inputs(self, folder_manager, mock_request, folder_name, comment):
        """Test creating folders with various name and comment combinations."""
        mock_request.return_value = {'success': True}
        
        folder_manager.create_folder(folder_name, comment)
        
        mock_request.assert_called_once_with(
            'POST',
            'workspace/folder_create',
            include_auth=True,
            json={'name': folder_name, 'comment': comment}
        )

    def test_create_folder_with_special_characters(self, folder_manager, mock_request):
        """Test creating a folder with special characters in name."""
        mock_request.return_value = {'success': True}
        
        folder_manager.create_folder('Test-Folder_2024 (v1)', 'Comment with émojis 🎉')
        
        assert mock_request.called
        call_args = mock_request.call_args
        assert call_args[1]['json']['name'] == 'Test-Folder_2024 (v1)'


class TestListFolders:
    """Test cases for list_folders method."""

    def test_list_folders_success(self, folder_manager, mock_request):
        """Test successfully listing all folders."""
        expected_response = {
            'folders': [
                {'id': '1', 'name': 'Folder 1'},
                {'id': '2', 'name': 'Folder 2'}
            ]
        }
        mock_request.return_value = expected_response
        
        result = folder_manager.list_folders()
        
        mock_request.assert_called_once_with(
            'GET',
            'workspace/folders',
            include_auth=True
        )
        assert result == expected_response
        assert len(result['folders']) == 2

    def test_list_folders_empty(self, folder_manager, mock_request):
        """Test listing folders when workspace is empty."""
        mock_request.return_value = {'folders': []}
        
        result = folder_manager.list_folders()
        
        assert result['folders'] == []

    def test_list_folders_calls_correct_endpoint(self, folder_manager, mock_request):
        """Test that list_folders uses the correct HTTP method and endpoint."""
        mock_request.return_value = {'folders': []}
        
        folder_manager.list_folders()
        
        args, kwargs = mock_request.call_args
        assert args[0] == 'GET'
        assert args[1] == 'workspace/folders'
        assert kwargs['include_auth'] is True


class TestUpdateFolder:
    """Test cases for update_folder method."""

    def test_update_folder_name_only(self, folder_manager, mock_request):
        """Test updating only the folder name."""
        mock_request.return_value = {'success': True}
        
        result = folder_manager.update_folder('folder_123', 'New Folder Name')
        
        mock_request.assert_called_once_with(
            'POST',
            'workspace/folder_update',
            include_auth=True,
            json={
                'folder_id': 'folder_123',
                'name': 'New Folder Name',
                'comment': None
            }
        )
        assert result['success'] is True

    def test_update_folder_name_and_comment(self, folder_manager, mock_request):
        """Test updating both folder name and comment."""
        mock_request.return_value = {'success': True}
        
        result = folder_manager.update_folder(
            'folder_456',
            'Updated Folder',
            'Updated comment'
        )
        
        mock_request.assert_called_once_with(
            'POST',
            'workspace/folder_update',
            include_auth=True,
            json={
                'folder_id': 'folder_456',
                'name': 'Updated Folder',
                'comment': 'Updated comment'
            }
        )

    @pytest.mark.parametrize('folder_id,new_name,comment', [
        ('id_1', 'Name 1', None),
        ('id_2', 'Name 2', 'Comment 2'),
        ('id_3', 'Name 3', ''),
        ('uuid-1234-5678', 'Complex Name!', 'Complex comment with 特殊字符'),
    ])
    def test_update_folder_various_inputs(self, folder_manager, mock_request, folder_id, new_name, comment):
        """Test updating folders with various input combinations."""
        mock_request.return_value = {'success': True}
        
        folder_manager.update_folder(folder_id, new_name, comment)
        
        call_json = mock_request.call_args[1]['json']
        assert call_json['folder_id'] == folder_id
        assert call_json['name'] == new_name
        assert call_json['comment'] == comment


class TestDeleteFolder:
    """Test cases for delete_folder method."""

    def test_delete_folder_success(self, folder_manager, mock_request):
        """Test successfully deleting a folder."""
        mock_request.return_value = {'success': True, 'deleted': 1}
        
        result = folder_manager.delete_folder('folder_123')
        
        mock_request.assert_called_once_with(
            'POST',
            'workspace/folders_remove',
            include_auth=True,
            json={'ids': ['folder_123']}
        )
        assert result['success'] is True

    def test_delete_folder_wraps_id_in_list(self, folder_manager, mock_request):
        """Test that delete_folder properly wraps the folder_id in a list."""
        mock_request.return_value = {'success': True}
        
        folder_manager.delete_folder('single_id')
        
        call_json = mock_request.call_args[1]['json']
        assert isinstance(call_json['ids'], list)
        assert call_json['ids'] == ['single_id']

    @pytest.mark.parametrize('folder_id', [
        'folder_1',
        'uuid-abcd-1234',
        '12345',
        'folder_with_underscores',
    ])
    def test_delete_folder_various_ids(self, folder_manager, mock_request, folder_id):
        """Test deleting folders with various ID formats."""
        mock_request.return_value = {'success': True}
        
        folder_manager.delete_folder(folder_id)
        
        call_json = mock_request.call_args[1]['json']
        assert folder_id in call_json['ids']


class TestErrorHandling:
    """Test cases for error handling across all methods."""

    def test_create_folder_api_error(self, folder_manager, mock_request):
        """Test handling of API errors when creating a folder."""
        mock_request.return_value = {'success': False, 'error': 'Invalid folder name'}
        
        result = folder_manager.create_folder('Invalid/Name')
        
        assert result['success'] is False
        assert 'error' in result

    def test_list_folders_api_error(self, folder_manager, mock_request):
        """Test handling of API errors when listing folders."""
        mock_request.side_effect = Exception('Network error')
        
        with pytest.raises(Exception) as exc_info:
            folder_manager.list_folders()
        
        assert 'Network error' in str(exc_info.value)

    def test_update_folder_nonexistent_id(self, folder_manager, mock_request):
        """Test updating a folder that doesn't exist."""
        mock_request.return_value = {'success': False, 'error': 'Folder not found'}
        
        result = folder_manager.update_folder('nonexistent_id', 'New Name')
        
        assert result['success'] is False

    def test_delete_folder_nonexistent_id(self, folder_manager, mock_request):
        """Test deleting a folder that doesn't exist."""
        mock_request.return_value = {'success': False, 'error': 'Folder not found'}
        
        result = folder_manager.delete_folder('nonexistent_id')
        
        assert result['success'] is False


class TestAuthenticationHandling:
    """Test cases verifying authentication is properly included."""

    def test_all_methods_include_auth(self, folder_manager, mock_request):
        """Test that all methods include authentication."""
        mock_request.return_value = {'success': True}
        
        # Test each method
        folder_manager.create_folder('Test')
        assert mock_request.call_args[1]['include_auth'] is True
        
        folder_manager.list_folders()
        assert mock_request.call_args[1]['include_auth'] is True
        
        folder_manager.update_folder('id', 'Name')
        assert mock_request.call_args[1]['include_auth'] is True
        
        folder_manager.delete_folder('id')
        assert mock_request.call_args[1]['include_auth'] is True    