#!/usr/bin/env python3
"""
Test script for Report Compiler

This script tests the report compiler functionality with various scenarios
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import Database
from report_compiler import ReportCompiler
from config import Config


def test_basic_report():
    """Test basic report compilation"""
    print("=" * 60)
    print("Test 1: Basic Report Compilation")
    print("=" * 60)

    try:
        with Database(Config.DB_NAME) as db:
            # Find a report in the database
            reports = db.execute(
                f"SELECT id, val FROM `{Config.DB_NAME}` WHERE t = {Config.REPORT} LIMIT 1"
            )

            if not reports:
                print("No reports found in database. Creating test data is required.")
                return False

            report_id = reports[0]['id']
            report_name = reports[0]['val']

            print(f"Testing report ID {report_id}: {report_name}")

            # Compile the report
            compiler = ReportCompiler(db, Config.DB_NAME)
            result = compiler.compile_report(report_id, execute=False)

            print(f"\n✓ Report compiled successfully")
            print(f"  Header: {result.get('header', 'N/A')}")
            print(f"  Columns: {len(result.get('types', {}))}")
            print(f"  SQL generated: {len(result.get('sql', ''))} characters")

            if result.get('sql'):
                print(f"\nGenerated SQL (first 200 chars):")
                print(result['sql'][:200] + "...")

            return True

    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_aggregates():
    """Test aggregate functions"""
    print("\n" + "=" * 60)
    print("Test 2: Aggregate Functions")
    print("=" * 60)

    try:
        with Database(Config.DB_NAME) as db:
            compiler = ReportCompiler(db, Config.DB_NAME)

            # Test aggregate function support
            print("Supported aggregate functions:")
            for func in compiler.AGGR_FUNCS:
                print(f"  - {func}")

            print("\n✓ Aggregate functions available")
            return True

    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def test_formula_fields():
    """Test formula and calculated fields"""
    print("\n" + "=" * 60)
    print("Test 3: Formula Fields")
    print("=" * 60)

    try:
        with Database(Config.DB_NAME) as db:
            compiler = ReportCompiler(db, Config.DB_NAME)

            # Create test report structure
            test_report = {
                'types': {1: 0},  # Type 0 = calculated field
                'base_in': {1: 'NUMBER'},
                'base_out': {1: 'NUMBER'},
                Config.REP_COL_FORMULA: {1: '1 + 1'},
                Config.REP_COL_NAME: {1: 'Test Formula'}
            }

            # Test formula field building
            field = compiler._build_formula_field(test_report, 1, 'a')
            print(f"Formula field result: {field}")

            name = compiler._build_field_name(test_report, 1, 'v')
            print(f"Field name: {name}")

            print("\n✓ Formula fields working")
            return True

    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_where_construction():
    """Test WHERE clause construction"""
    print("\n" + "=" * 60)
    print("Test 4: WHERE Clause Construction")
    print("=" * 60)

    try:
        with Database(Config.DB_NAME) as db:
            compiler = ReportCompiler(db, Config.DB_NAME)

            # Set up test conditions
            compiler.rev_bt[100] = 'NUMBER'
            filter_dict = {'FR': '10', 'TO': '100'}

            where = compiler.construct_where(100, filter_dict, 100)
            print(f"WHERE clause: {where}")

            print("\n✓ WHERE clause construction working")
            return True

    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_database_connection():
    """Test database connectivity"""
    print("\n" + "=" * 60)
    print("Test 0: Database Connection")
    print("=" * 60)

    try:
        with Database(Config.DB_NAME) as db:
            # Test basic query
            result = db.execute_one(f"SELECT COUNT(*) as cnt FROM `{Config.DB_NAME}`")
            print(f"Database connected successfully")
            print(f"Total records in database: {result['cnt']}")

            # Count reports
            reports = db.execute(
                f"SELECT COUNT(*) as cnt FROM `{Config.DB_NAME}` WHERE t = {Config.REPORT}"
            )
            print(f"Total reports in database: {reports[0]['cnt']}")

            return True

    except Exception as e:
        print(f"✗ Database connection error: {e}")
        print("\nPlease ensure:")
        print("1. MySQL is running")
        print("2. Database is created (run 1_database.sql)")
        print("3. Tables are created (run 2_table.sql)")
        print("4. .env file has correct database credentials")
        return False


def main():
    """Run all tests"""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 58 + "║")
    print("║" + "  REPORT COMPILER TEST SUITE".center(58) + "║")
    print("║" + " " * 58 + "║")
    print("╚" + "=" * 58 + "╝")
    print()

    tests = [
        ("Database Connection", test_database_connection),
        ("Basic Report Compilation", test_basic_report),
        ("Aggregate Functions", test_aggregates),
        ("Formula Fields", test_formula_fields),
        ("WHERE Clause Construction", test_where_construction),
    ]

    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n✗ Test '{name}' crashed: {e}")
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
        print("\n🎉 All tests passed!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        return 1


if __name__ == '__main__':
    sys.exit(main())
