#!/usr/bin/env python3
"""
Test script for batch operations implementation.
This verifies the new batch delete, move up, and export features.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import Database

def test_batch_delete():
    """Test the batch_delete method"""
    print("Testing batch_delete method...")

    # Test that the method exists and is callable
    db = Database.__new__(Database)
    assert hasattr(db, 'batch_delete'), "batch_delete method should exist"
    assert callable(getattr(db, 'batch_delete')), "batch_delete should be callable"

    print("✓ batch_delete method exists and is callable")

def test_permissions():
    """Test the has_delete_grant method"""
    print("\nTesting has_delete_grant method...")

    from permissions import PermissionSystem

    # Test that the method exists
    perm_sys = PermissionSystem.__new__(PermissionSystem)
    assert hasattr(perm_sys, 'has_delete_grant'), "has_delete_grant method should exist"
    assert callable(getattr(perm_sys, 'has_delete_grant')), "has_delete_grant should be callable"

    print("✓ has_delete_grant method exists and is callable")

def test_routes():
    """Test that the new routes exist in app.py"""
    print("\nTesting routes...")

    with open('app.py', 'r') as f:
        content = f.read()

    # Check for batch delete route
    assert 'batch_delete_objects' in content, "batch_delete_objects route should exist"
    assert '_m_del_select' in content, "Should handle _m_del_select parameter"

    # Check for move up route
    assert 'move_up_object' in content, "move_up_object route should exist"
    assert '_m_up' in content, "Should handle _m_up route"

    # Check for export functionality
    assert 'export_objects_csv' in content, "export_objects_csv function should exist"
    assert 'csv' in content, "Should handle CSV export"

    print("✓ All required routes exist")

def test_template():
    """Test that the template has move up button"""
    print("\nTesting template...")

    with open('templates_python/object.html', 'r') as f:
        content = f.read()

    # Check for move up button
    assert '_m_up' in content, "Template should have move up button"
    assert 'Move up' in content, "Template should have Move up title"
    assert '/up.png' in content, "Template should have up icon"

    print("✓ Template includes move up button")

def main():
    """Run all tests"""
    print("=" * 60)
    print("Testing Batch Operations Implementation")
    print("=" * 60)

    try:
        test_batch_delete()
        test_permissions()
        test_routes()
        test_template()

        print("\n" + "=" * 60)
        print("✓ All tests passed!")
        print("=" * 60)
        return 0
    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        return 1
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    sys.exit(main())
