"""
Examples demonstrating the filtering system

This script shows various use cases of the filtering system implemented
for the IdeaV Local Python version.
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from filters import FilterBuilder, apply_filters


def example_1_simple_text_filter():
    """Example 1: Simple text filtering"""
    print("\n=== Example 1: Simple Text Filter ===")

    builder = FilterBuilder("ideav")
    field_types = {3: "CHARS"}

    # Filter for records where field 3 equals "test"
    filters = {"F": "test"}
    where, join, params, distinct = builder.construct_where(
        3, filters, 1, 0, False, field_types, {}
    )

    print(f"WHERE clause: {where}")
    print(f"JOIN clause: {join}")
    print(f"Parameters: {params}")
    print(f"Distinct: {distinct}")


def example_2_like_search():
    """Example 2: LIKE search with wildcards"""
    print("\n=== Example 2: LIKE Search ===")

    builder = FilterBuilder("ideav")
    field_types = {3: "CHARS"}

    # Filter for records where field 3 starts with "prod"
    filters = {"F": "prod%"}
    where, join, params, distinct = builder.construct_where(
        3, filters, 1, 0, False, field_types, {}
    )

    print(f"WHERE clause: {where}")
    print(f"Parameters: {params}")


def example_3_range_filter():
    """Example 3: Range filtering (FROM/TO)"""
    print("\n=== Example 3: Range Filter ===")

    builder = FilterBuilder("ideav")
    field_types = {13: "NUMBER"}

    # Filter for records where field 13 is between 100 and 500
    filters = {"FR": "100", "TO": "500"}
    where, join, params, distinct = builder.construct_where(
        13, filters, 1, 0, False, field_types, {}
    )

    print(f"WHERE clause: {where}")
    print(f"Parameters: {params}")


def example_4_not_filter():
    """Example 4: NOT filter (negation)"""
    print("\n=== Example 4: NOT Filter ===")

    builder = FilterBuilder("ideav")
    field_types = {3: "CHARS"}

    # Filter for records where field 3 does NOT equal "test"
    filters = {"F": "!test"}
    where, join, params, distinct = builder.construct_where(
        3, filters, 1, 0, False, field_types, {}
    )

    print(f"WHERE clause: {where}")
    print(f"Parameters: {params}")


def example_5_null_check():
    """Example 5: NULL check"""
    print("\n=== Example 5: NULL Check ===")

    builder = FilterBuilder("ideav")
    field_types = {3: "CHARS"}

    # Filter for records where field 3 is NOT NULL
    filters = {"F": "%"}
    where, join, params, distinct = builder.construct_where(
        3, filters, 1, 0, False, field_types, {}
    )

    print(f"WHERE clause: {where}")


def example_6_reference_filter():
    """Example 6: Reference filtering by ID"""
    print("\n=== Example 6: Reference Filter ===")

    builder = FilterBuilder("ideav")
    field_types = {3: "CHARS"}

    # Filter for records where field 3 references ID 123
    filters = {"F": "@123"}
    where, join, params, distinct = builder.construct_where(
        3, filters, 1, 3, False, field_types, {}
    )

    print(f"WHERE clause: {where}")
    print(f"JOIN clause: {join}")
    print(f"Parameters: {params}")


def example_7_in_clause():
    """Example 7: IN clause"""
    print("\n=== Example 7: IN Clause ===")

    builder = FilterBuilder("ideav")
    field_types = {13: "NUMBER"}

    # Filter for records where field 13 is in (1, 2, 3, 4, 5)
    filters = {"F": "IN(1,2,3,4,5)"}
    where, join, params, distinct = builder.construct_where(
        13, filters, 1, 0, False, field_types, {}
    )

    print(f"WHERE clause: {where}")


def example_8_multi_criteria():
    """Example 8: Multi-criteria filtering"""
    print("\n=== Example 8: Multi-Criteria Filter ===")

    field_types = {
        3: "CHARS",    # Product name
        13: "NUMBER",  # Price
        9: "DATE"      # Date
    }

    filters = {
        3: {"F": "product%"},           # Product name starts with "product"
        13: {"FR": "100", "TO": "500"}, # Price between 100 and 500
        9: {"F": "20240101"}            # Date equals 2024-01-01
    }

    where, join, params, distinct = apply_filters(
        "ideav", filters, 1, field_types, {}
    )

    print(f"WHERE clause: {where}")
    print(f"JOIN clause: {join}")
    print(f"Parameters: {params}")
    print(f"Distinct: {distinct}")


def example_9_date_range():
    """Example 9: Date range filtering"""
    print("\n=== Example 9: Date Range Filter ===")

    builder = FilterBuilder("ideav")
    field_types = {9: "DATE"}

    # Filter for dates between 2024-01-01 and 2024-12-31
    filters = {"FR": "20240101", "TO": "20241231"}
    where, join, params, distinct = builder.construct_where(
        9, filters, 1, 0, False, field_types, {}
    )

    print(f"WHERE clause: {where}")
    print(f"Parameters: {params}")


def example_10_combined_not_and_like():
    """Example 10: Combined NOT and LIKE"""
    print("\n=== Example 10: Combined NOT and LIKE ===")

    builder = FilterBuilder("ideav")
    field_types = {3: "CHARS"}

    # Filter for records where field 3 does NOT contain "test"
    filters = {"F": "!%test%"}
    where, join, params, distinct = builder.construct_where(
        3, filters, 1, 0, False, field_types, {}
    )

    print(f"WHERE clause: {where}")
    print(f"Parameters: {params}")


def main():
    """Run all examples"""
    print("=" * 60)
    print("IdeaV Local - Filtering System Examples")
    print("=" * 60)

    example_1_simple_text_filter()
    example_2_like_search()
    example_3_range_filter()
    example_4_not_filter()
    example_5_null_check()
    example_6_reference_filter()
    example_7_in_clause()
    example_8_multi_criteria()
    example_9_date_range()
    example_10_combined_not_and_like()

    print("\n" + "=" * 60)
    print("All examples completed!")
    print("=" * 60)


if __name__ == "__main__":
    main()
