"""
Unit tests for the permission system

These tests verify the core functionality of:
- Permission checking (Check_Grant equivalent)
- Type permission checking (Check_Types_Grant equivalent)
- Token validation (Validate_Token equivalent)
"""
import unittest
from unittest.mock import Mock, patch, MagicMock
from permissions import PermissionSystem, PermissionError
from config import Config


class TestPermissionSystem(unittest.TestCase):
    """Test cases for PermissionSystem class"""

    def setUp(self):
        """Set up test fixtures"""
        self.db_name = "test_db"
        self.perm_sys = PermissionSystem(self.db_name)

    def test_init(self):
        """Test PermissionSystem initialization"""
        self.assertEqual(self.perm_sys.db_name, self.db_name)
        self.assertEqual(self.perm_sys.grants, {})
        self.assertIsNone(self.perm_sys.user)
        self.assertIsNone(self.perm_sys.user_id)
        self.assertIsNone(self.perm_sys.role)

    def test_admin_has_full_access(self):
        """Test that admin user has full access"""
        self.perm_sys.user = "admin"

        # Admin should have WRITE access to types
        result = self.perm_sys.check_types_grant(fatal=False)
        self.assertEqual(result, "WRITE")

        # Admin should have access to any object
        result = self.perm_sys.check_grant(1, 0, "WRITE", fatal=False)
        self.assertTrue(result)

    def test_check_types_grant_with_permission(self):
        """Test check_types_grant when user has permission"""
        self.perm_sys.user = "testuser"
        self.perm_sys.grants = {0: "READ"}

        result = self.perm_sys.check_types_grant(fatal=False)
        self.assertEqual(result, "READ")

        self.perm_sys.grants = {0: "WRITE"}
        result = self.perm_sys.check_types_grant(fatal=False)
        self.assertEqual(result, "WRITE")

    def test_check_types_grant_without_permission_fatal(self):
        """Test check_types_grant raises exception when no permission and fatal=True"""
        self.perm_sys.user = "testuser"
        self.perm_sys.grants = {}

        with self.assertRaises(PermissionError) as context:
            self.perm_sys.check_types_grant(fatal=True)

        self.assertIn("metadata", str(context.exception).lower())

    def test_check_types_grant_without_permission_non_fatal(self):
        """Test check_types_grant returns READ when no permission and fatal=False"""
        self.perm_sys.user = "testuser"
        self.perm_sys.grants = {}

        result = self.perm_sys.check_types_grant(fatal=False)
        self.assertEqual(result, "READ")

    def test_check_grant_explicit_type_permission(self):
        """Test check_grant with explicit type permission"""
        self.perm_sys.user = "testuser"
        self.perm_sys.grants = {3: "WRITE"}

        # User has WRITE on type 3
        result = self.perm_sys.check_grant(1, 3, "WRITE", fatal=False)
        self.assertTrue(result)

        # User has READ on type 3 (WRITE includes READ)
        result = self.perm_sys.check_grant(1, 3, "READ", fatal=False)
        self.assertTrue(result)

    def test_check_grant_explicit_object_permission(self):
        """Test check_grant with explicit object permission"""
        self.perm_sys.user = "testuser"
        self.perm_sys.grants = {100: "WRITE"}

        # User has WRITE on object 100
        result = self.perm_sys.check_grant(100, 0, "WRITE", fatal=False)
        self.assertTrue(result)

    def test_check_grant_write_includes_read(self):
        """Test that WRITE permission includes READ permission"""
        self.perm_sys.user = "testuser"
        self.perm_sys.grants = {3: "WRITE"}

        # User has WRITE on type 3, should also have READ
        result = self.perm_sys.check_grant(1, 3, "READ", fatal=False)
        self.assertTrue(result)

    def test_check_grant_read_does_not_include_write(self):
        """Test that READ permission does not include WRITE permission"""
        self.perm_sys.user = "testuser"
        self.perm_sys.grants = {3: "READ"}

        # User has READ on type 3, should not have WRITE
        result = self.perm_sys.check_grant(1, 3, "WRITE", fatal=False)
        self.assertFalse(result)

    def test_check_grant_no_permission_fatal(self):
        """Test check_grant raises exception when no permission and fatal=True"""
        self.perm_sys.user = "testuser"
        self.perm_sys.grants = {}

        with self.assertRaises(PermissionError) as context:
            self.perm_sys.check_grant(100, 3, "WRITE", fatal=True)

        self.assertIn("Access denied", str(context.exception))

    def test_check_grant_no_permission_non_fatal(self):
        """Test check_grant returns False when no permission and fatal=False"""
        self.perm_sys.user = "testuser"
        self.perm_sys.grants = {}

        with patch.object(PermissionSystem, '_query_object_hierarchy') as mock_query:
            mock_query.return_value = False
            result = self.perm_sys.check_grant(100, 3, "WRITE", fatal=False)
            self.assertFalse(result)

    def test_can_edit_metadata(self):
        """Test can_edit_metadata function"""
        # Metadata (up=0) cannot be edited
        obj = {'up': 0}
        result = self.perm_sys.can_edit_metadata(obj)
        self.assertFalse(result)

        # Regular objects can be edited
        obj = {'up': 1}
        result = self.perm_sys.can_edit_metadata(obj)
        self.assertTrue(result)

    def test_can_delete_metadata(self):
        """Test can_delete_metadata function"""
        # Cannot delete if parent is metadata
        parent = {'up': 0}
        result = self.perm_sys.can_delete_metadata(parent)
        self.assertFalse(result)

        # Can delete if parent is not metadata
        parent = {'up': 1}
        result = self.perm_sys.can_delete_metadata(parent)
        self.assertTrue(result)

        # Can delete if parent is None
        result = self.perm_sys.can_delete_metadata(None)
        self.assertTrue(result)

    @patch('permissions.Database')
    def test_validate_token_success(self, mock_db_class):
        """Test successful token validation"""
        # Mock database connection
        mock_db = MagicMock()
        mock_db_class.return_value.__enter__.return_value = mock_db

        # Mock user query result
        mock_db.execute_one.return_value = {
            'id': 1,
            'val': 'testuser',
            'r': 42,
            'role': 'editor',
            'xsrf': 'xsrf_token_value'
        }

        # Mock grants query result
        mock_db.execute.return_value = [
            {'object': '1', 'mask': '', 'level': 'WRITE', 'mass': ''},
            {'object': '3', 'mask': '', 'level': 'READ', 'mass': ''}
        ]

        with patch('permissions.session', {}):
            with patch('permissions.time'):
                result = self.perm_sys.validate_token('test_token')

        self.assertTrue(result)
        self.assertEqual(self.perm_sys.user, 'testuser')
        self.assertEqual(self.perm_sys.user_id, 1)
        self.assertEqual(self.perm_sys.role, 'editor')
        self.assertIn('1', self.perm_sys.grants)
        self.assertIn('3', self.perm_sys.grants)

    @patch('permissions.Database')
    def test_validate_token_no_user(self, mock_db_class):
        """Test token validation when user not found"""
        mock_db = MagicMock()
        mock_db_class.return_value.__enter__.return_value = mock_db
        mock_db.execute_one.return_value = None

        result = self.perm_sys.validate_token('invalid_token')
        self.assertFalse(result)

    @patch('permissions.Database')
    def test_validate_token_no_role(self, mock_db_class):
        """Test token validation when user has no role"""
        mock_db = MagicMock()
        mock_db_class.return_value.__enter__.return_value = mock_db
        mock_db.execute_one.return_value = {
            'id': 1,
            'val': 'testuser',
            'r': None,  # No role assigned
            'role': None,
            'xsrf': None
        }

        with self.assertRaises(PermissionError) as context:
            self.perm_sys.validate_token('test_token')

        self.assertIn("No role assigned", str(context.exception))

    def test_load_grants_simple_level(self):
        """Test loading simple level grants"""
        mock_db = Mock()
        mock_db.execute.return_value = [
            {'object': '1', 'mask': '', 'level': 'WRITE', 'mass': ''},
            {'object': '3', 'mask': '', 'level': 'READ', 'mass': ''}
        ]

        self.perm_sys._load_grants(mock_db, 42)

        self.assertEqual(self.perm_sys.grants['1'], 'WRITE')
        self.assertEqual(self.perm_sys.grants['3'], 'READ')

    def test_load_grants_masklevel(self):
        """Test loading mask-level grants"""
        mock_db = Mock()
        mock_db.execute.return_value = [
            {'object': '100', 'mask': 'filter1', 'level': 'READ', 'mass': ''}
        ]

        self.perm_sys._load_grants(mock_db, 42)

        self.assertIn('masklevel', self.perm_sys.grants)
        self.assertIn('100', self.perm_sys.grants['masklevel'])
        self.assertEqual(self.perm_sys.grants['masklevel']['100']['READ'], 'filter1')

    def test_load_grants_mask_only(self):
        """Test loading mask-only grants"""
        mock_db = Mock()
        mock_db.execute.return_value = [
            {'object': '200', 'mask': 'mask_val', 'level': '', 'mass': ''}
        ]

        self.perm_sys._load_grants(mock_db, 42)

        self.assertIn('mask', self.perm_sys.grants)
        self.assertIn('200', self.perm_sys.grants['mask'])
        self.assertIn('mask_val', self.perm_sys.grants['mask']['200'])


class TestPermissionHelpers(unittest.TestCase):
    """Test helper functions for permission system"""

    @patch('permissions.session', {})
    @patch('permissions.request')
    @patch('permissions.PermissionSystem')
    def test_get_permission_system_new(self, mock_perm_class, mock_request):
        """Test creating new permission system"""
        from permissions import get_permission_system

        mock_request.cookies.get.return_value = 'test_token'
        mock_perm = Mock()
        mock_perm.validate_token.return_value = True
        mock_perm_class.return_value = mock_perm

        result = get_permission_system('test_db')

        mock_perm_class.assert_called_once_with('test_db')
        mock_perm.validate_token.assert_called_once_with('test_token')
        self.assertEqual(result, mock_perm)

    @patch('permissions.session', {})
    @patch('permissions.request')
    @patch('permissions.PermissionSystem')
    def test_get_permission_system_invalid_token(self, mock_perm_class, mock_request):
        """Test get_permission_system with invalid token"""
        from permissions import get_permission_system

        mock_request.cookies.get.return_value = 'invalid_token'
        mock_perm = Mock()
        mock_perm.validate_token.return_value = False
        mock_perm_class.return_value = mock_perm

        result = get_permission_system('test_db')

        self.assertIsNone(result)


if __name__ == '__main__':
    unittest.main()
