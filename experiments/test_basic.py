#!/usr/bin/env python3
"""
Basic test for Report Compiler module - no database required
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_imports():
    """Test that all modules can be imported"""
    print("Testing imports...")
    try:
        from report_compiler import ReportCompiler
        print("✓ report_compiler imported successfully")

        from database import Database
        print("✓ database imported successfully")

        from config import Config
        print("✓ config imported successfully")

        from utils import t9n, builtin_value
        print("✓ utils imported successfully")

        return True
    except Exception as e:
        print(f"✗ Import error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_constants():
    """Test that all constants are defined"""
    print("\nTesting constants...")
    try:
        from config import Config

        required_constants = [
            'REPORT', 'REP_COLS', 'REP_JOIN', 'REP_COL_FORMAT',
            'REP_COL_FUNC', 'REP_COL_TOTAL', 'REP_COL_NAME',
            'REP_COL_FORMULA', 'REP_COL_FROM', 'REP_COL_TO',
            'REP_COL_HAV_FR', 'REP_COL_HAV_TO', 'REP_COL_HIDE',
            'REP_COL_SORT', 'REP_ALIAS', 'REP_JOIN_ON'
        ]

        missing = []
        for const in required_constants:
            if not hasattr(Config, const):
                missing.append(const)
            else:
                val = getattr(Config, const)
                print(f"  {const} = {val}")

        if missing:
            print(f"✗ Missing constants: {', '.join(missing)}")
            return False

        print("✓ All report constants defined")
        return True

    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def test_report_compiler_class():
    """Test ReportCompiler class structure"""
    print("\nTesting ReportCompiler class...")
    try:
        from report_compiler import ReportCompiler

        # Check class attributes
        print(f"  AGGR_FUNCS: {ReportCompiler.AGGR_FUNCS}")
        print(f"  TAILED_TYPES: {ReportCompiler.TAILED_TYPES}")

        # Check methods exist
        required_methods = [
            'compile_report', '_build_sql_query', '_process_dynamic_select',
            '_process_custom_totals', '_process_filter_conditions',
            '_build_formula_field', '_build_field_name', '_get_field_expression',
            '_build_join_clause', '_add_field_to_select', '_build_group_by',
            '_build_having', '_build_order_by', '_build_limit',
            'construct_where'
        ]

        missing = []
        for method in required_methods:
            if not hasattr(ReportCompiler, method):
                missing.append(method)

        if missing:
            print(f"✗ Missing methods: {', '.join(missing)}")
            return False

        print(f"✓ All {len(required_methods)} required methods present")
        return True

    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_aggregate_functions():
    """Test aggregate function list"""
    print("\nTesting aggregate functions...")
    try:
        from report_compiler import ReportCompiler

        expected_funcs = ['AVG', 'COUNT', 'MAX', 'MIN', 'SUM']
        if ReportCompiler.AGGR_FUNCS == expected_funcs:
            print(f"✓ Correct aggregate functions: {expected_funcs}")
            return True
        else:
            print(f"✗ Unexpected functions: {ReportCompiler.AGGR_FUNCS}")
            return False

    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def main():
    """Run all basic tests"""
    print("\n" + "=" * 60)
    print("BASIC REPORT COMPILER TESTS (No Database Required)")
    print("=" * 60 + "\n")

    tests = [
        ("Module Imports", test_imports),
        ("Configuration Constants", test_constants),
        ("ReportCompiler Class Structure", test_report_compiler_class),
        ("Aggregate Functions", test_aggregate_functions),
    ]

    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n✗ Test '{name}' crashed: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {name}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All basic tests passed!")
        print("\nThe Report Compiler module is correctly structured.")
        print("Database tests can be run with test_report_compiler.py")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        return 1


if __name__ == '__main__':
    sys.exit(main())
