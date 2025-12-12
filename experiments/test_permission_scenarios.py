"""
Experiment script to test permission system scenarios

This script demonstrates various permission checking scenarios
to verify the implementation matches the PHP version's behavior.
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from permissions import PermissionSystem, PermissionError


def test_scenario_1_admin_access():
    """Scenario 1: Admin user should have full access"""
    print("=" * 60)
    print("Scenario 1: Admin User Access")
    print("=" * 60)

    perm_sys = PermissionSystem("test_db")
    perm_sys.user = "admin"

    # Test type grant
    result = perm_sys.check_types_grant(fatal=False)
    print(f"✓ Admin types grant: {result}")
    assert result == "WRITE", "Admin should have WRITE access to types"

    # Test object grant
    result = perm_sys.check_grant(1, 0, "WRITE", fatal=False)
    print(f"✓ Admin object grant: {result}")
    assert result is True, "Admin should have access to any object"

    print("✓ Scenario 1 PASSED\n")


def test_scenario_2_explicit_type_permission():
    """Scenario 2: User with explicit type permission"""
    print("=" * 60)
    print("Scenario 2: Explicit Type Permission")
    print("=" * 60)

    perm_sys = PermissionSystem("test_db")
    perm_sys.user = "testuser"
    perm_sys.grants = {3: "WRITE", 5: "READ"}

    # User has WRITE on type 3
    result = perm_sys.check_grant(100, 3, "WRITE", fatal=False)
    print(f"✓ WRITE access to type 3: {result}")
    assert result is True, "User should have WRITE access to type 3"

    # User has READ on type 3 (WRITE includes READ)
    result = perm_sys.check_grant(100, 3, "READ", fatal=False)
    print(f"✓ READ access to type 3 (via WRITE): {result}")
    assert result is True, "User with WRITE should also have READ"

    # User has only READ on type 5
    result = perm_sys.check_grant(200, 5, "READ", fatal=False)
    print(f"✓ READ access to type 5: {result}")
    assert result is True, "User should have READ access to type 5"

    # User should not have WRITE on type 5
    result = perm_sys.check_grant(200, 5, "WRITE", fatal=False)
    print(f"✓ WRITE access to type 5 (denied): {result}")
    assert result is False, "User should not have WRITE access to type 5"

    print("✓ Scenario 2 PASSED\n")


def test_scenario_3_explicit_object_permission():
    """Scenario 3: User with explicit object permission"""
    print("=" * 60)
    print("Scenario 3: Explicit Object Permission")
    print("=" * 60)

    perm_sys = PermissionSystem("test_db")
    perm_sys.user = "testuser"
    perm_sys.grants = {100: "WRITE", 200: "READ"}

    # User has WRITE on object 100
    result = perm_sys.check_grant(100, 0, "WRITE", fatal=False)
    print(f"✓ WRITE access to object 100: {result}")
    assert result is True, "User should have WRITE access to object 100"

    # User has only READ on object 200
    result = perm_sys.check_grant(200, 0, "READ", fatal=False)
    print(f"✓ READ access to object 200: {result}")
    assert result is True, "User should have READ access to object 200"

    # User should not have WRITE on object 200
    result = perm_sys.check_grant(200, 0, "WRITE", fatal=False)
    print(f"✓ WRITE access to object 200 (denied): {result}")
    assert result is False, "User should not have WRITE access to object 200"

    print("✓ Scenario 3 PASSED\n")


def test_scenario_4_permission_denied_fatal():
    """Scenario 4: Permission denied with fatal=True"""
    print("=" * 60)
    print("Scenario 4: Permission Denied (Fatal)")
    print("=" * 60)

    perm_sys = PermissionSystem("test_db")
    perm_sys.user = "testuser"
    perm_sys.grants = {}

    # Should raise PermissionError
    try:
        perm_sys.check_grant(100, 3, "WRITE", fatal=True)
        print("✗ Should have raised PermissionError")
        assert False, "Should have raised PermissionError"
    except PermissionError as e:
        print(f"✓ Raised PermissionError: {e}")

    print("✓ Scenario 4 PASSED\n")


def test_scenario_5_metadata_editing():
    """Scenario 5: Metadata editing restrictions"""
    print("=" * 60)
    print("Scenario 5: Metadata Editing Restrictions")
    print("=" * 60)

    perm_sys = PermissionSystem("test_db")
    perm_sys.user = "testuser"

    # Cannot edit metadata (up=0)
    obj = {'up': 0}
    result = perm_sys.can_edit_metadata(obj)
    print(f"✓ Cannot edit metadata (up=0): {not result}")
    assert result is False, "Should not be able to edit metadata"

    # Can edit regular objects
    obj = {'up': 1}
    result = perm_sys.can_edit_metadata(obj)
    print(f"✓ Can edit regular object (up=1): {result}")
    assert result is True, "Should be able to edit regular objects"

    # Cannot delete if parent is metadata
    parent = {'up': 0}
    result = perm_sys.can_delete_metadata(parent)
    print(f"✓ Cannot delete metadata child (parent.up=0): {not result}")
    assert result is False, "Should not be able to delete metadata children"

    # Can delete if parent is not metadata
    parent = {'up': 1}
    result = perm_sys.can_delete_metadata(parent)
    print(f"✓ Can delete regular object (parent.up=1): {result}")
    assert result is True, "Should be able to delete regular objects"

    print("✓ Scenario 5 PASSED\n")


def test_scenario_6_types_grant():
    """Scenario 6: Types grant checking"""
    print("=" * 60)
    print("Scenario 6: Types Grant Checking")
    print("=" * 60)

    # User with READ access to types
    perm_sys = PermissionSystem("test_db")
    perm_sys.user = "testuser"
    perm_sys.grants = {0: "READ"}

    result = perm_sys.check_types_grant(fatal=False)
    print(f"✓ Types grant (READ): {result}")
    assert result == "READ", "Should have READ access to types"

    # User with WRITE access to types
    perm_sys.grants = {0: "WRITE"}
    result = perm_sys.check_types_grant(fatal=False)
    print(f"✓ Types grant (WRITE): {result}")
    assert result == "WRITE", "Should have WRITE access to types"

    # User with no access to types (non-fatal)
    perm_sys.grants = {}
    result = perm_sys.check_types_grant(fatal=False)
    print(f"✓ Types grant (none, non-fatal): {result}")
    assert result == "READ", "Should default to READ when fatal=False"

    # User with no access to types (fatal)
    try:
        perm_sys.check_types_grant(fatal=True)
        print("✗ Should have raised PermissionError")
        assert False, "Should have raised PermissionError"
    except PermissionError as e:
        print(f"✓ Raised PermissionError for types: {e}")

    print("✓ Scenario 6 PASSED\n")


def test_scenario_7_grant_hierarchy():
    """Scenario 7: Grant hierarchy and inheritance"""
    print("=" * 60)
    print("Scenario 7: Grant Hierarchy and Inheritance")
    print("=" * 60)

    perm_sys = PermissionSystem("test_db")
    perm_sys.user = "testuser"

    # Test with grants at different levels
    perm_sys.grants = {
        1: "WRITE",  # Global grant
        3: "READ",   # Type 3 grant
        100: "WRITE" # Object 100 grant
    }

    # Object 100 has explicit grant
    result = perm_sys.check_grant(100, 0, "WRITE", fatal=False)
    print(f"✓ Object 100 explicit grant: {result}")
    assert result is True, "Should have WRITE via explicit object grant"

    # Type 3 has explicit grant
    result = perm_sys.check_grant(50, 3, "READ", fatal=False)
    print(f"✓ Type 3 explicit grant: {result}")
    assert result is True, "Should have READ via explicit type grant"

    print("✓ Scenario 7 PASSED\n")


def run_all_tests():
    """Run all test scenarios"""
    print("\n" + "=" * 60)
    print("PERMISSION SYSTEM TEST SCENARIOS")
    print("=" * 60 + "\n")

    try:
        test_scenario_1_admin_access()
        test_scenario_2_explicit_type_permission()
        test_scenario_3_explicit_object_permission()
        test_scenario_4_permission_denied_fatal()
        test_scenario_5_metadata_editing()
        test_scenario_6_types_grant()
        test_scenario_7_grant_hierarchy()

        print("=" * 60)
        print("ALL SCENARIOS PASSED ✓")
        print("=" * 60)
        return 0

    except AssertionError as e:
        print(f"\n✗ FAILED: {e}")
        return 1
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = run_all_tests()
    sys.exit(exit_code)
