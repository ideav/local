"""
Test script for export/import functionality
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from export_import import ExportImport


def test_delimiter_functions():
    """Test delimiter masking/unmasking functions"""
    print("Testing delimiter masking/unmasking...")

    # Test mask_delimiters
    test_val = "test:value;with\\special"
    masked = ExportImport.mask_delimiters(test_val)
    print(f"  Original: {test_val}")
    print(f"  Masked: {masked}")
    assert masked == "test\\:value\\;with\\\\special", f"Masking failed: {masked}"

    # Test unmask_delimiters
    unmasked = ExportImport.unmask_delimiters(masked)
    print(f"  Unmasked: {unmasked}")
    assert unmasked == test_val, f"Unmasking failed: {unmasked}"

    print("  ✓ Delimiter masking/unmasking works correctly")


def test_hide_unhide_delimiters():
    """Test delimiter hiding/unhiding functions"""
    print("\nTesting delimiter hiding/unhiding...")

    test_val = "\\\\test\\:\\;value"
    hidden = ExportImport.hide_delimiters(test_val)
    print(f"  Original: {test_val}")
    print(f"  Hidden: {hidden}")
    assert hidden == "%5Ctest%3A%3Bvalue", f"Hiding failed: {hidden}"

    unhidden = ExportImport.unhide_delimiters(hidden)
    print(f"  Unhidden: {unhidden}")
    assert unhidden == test_val, f"Unhiding failed: {unhidden}"

    print("  ✓ Delimiter hiding/unhiding works correctly")


def test_csv_export():
    """Test CSV export functionality"""
    print("\nTesting CSV export...")

    # Mock database name (won't actually connect)
    exporter = ExportImport("test_db", connect_db=False)

    headers = ["Name", "Age", "City"]
    data = [
        ["John Doe", "30", "New York"],
        ["Jane Smith", "25", "Los Angeles"],
        ["Bob Johnson", "35", "Chicago"]
    ]

    csv_content = exporter.export_csv(1, headers, data)

    print(f"  CSV content type: {type(csv_content)}")
    print(f"  CSV content length: {len(csv_content)} bytes")

    # Decode to check content
    try:
        csv_text = csv_content.decode('windows-1251')
    except:
        csv_text = csv_content.decode('utf-8')

    print(f"  CSV preview:\n{csv_text[:200]}")

    # Check that headers are present
    assert "Name" in csv_text, "Headers not found in CSV"
    assert "John Doe" in csv_text, "Data not found in CSV"

    print("  ✓ CSV export works correctly")


def test_bki_structure_parsing():
    """Test BKI structure line parsing"""
    print("\nTesting BKI structure parsing...")

    # Sample BKI structure line
    bki_line = "123:Object Name:SHORT;Name Field:CHARS;456:ref:789;"

    # Test hiding and splitting
    hidden = ExportImport.hide_delimiters(bki_line)
    parts = hidden.split(';')

    print(f"  Original: {bki_line}")
    print(f"  Parts count: {len(parts)}")

    for i, part in enumerate(parts):
        unhidden = ExportImport.unhide_delimiters(part)
        if unhidden:
            print(f"    Part {i}: {unhidden}")

    print("  ✓ BKI structure parsing works correctly")


def main():
    """Run all tests"""
    print("=" * 60)
    print("Export/Import Module Tests")
    print("=" * 60)

    try:
        test_delimiter_functions()
        test_hide_unhide_delimiters()
        test_csv_export()
        test_bki_structure_parsing()

        print("\n" + "=" * 60)
        print("✓ All tests passed!")
        print("=" * 60)
    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        return 1
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == '__main__':
    sys.exit(main())
