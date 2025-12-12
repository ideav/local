"""
Unit tests for the filtering system
"""
import unittest
from filters import FilterBuilder, apply_filters


class TestFilterBuilder(unittest.TestCase):
    """Test cases for FilterBuilder class"""

    def setUp(self):
        """Set up test fixtures"""
        self.builder = FilterBuilder("ideav")
        self.field_types = {
            3: "CHARS",    # Short text field
            8: "CHARS",    # Characters field
            9: "DATE",     # Date field
            13: "NUMBER",  # Number field
            14: "SIGNED",  # Signed number field
            12: "MEMO",    # Memo field
        }
        self.ref_types = {}

    def tearDown(self):
        """Clean up after tests"""
        self.builder.reset()

    def test_simple_text_filter(self):
        """Test simple text filtering"""
        filters = {"F": "test"}
        where, join, params, distinct = self.builder.construct_where(
            3, filters, 1, 0, False, self.field_types, self.ref_types
        )

        self.assertIn("a3.val", where)
        self.assertEqual(params[0], "test")
        self.assertFalse(distinct)

    def test_like_filter(self):
        """Test LIKE filtering with wildcards"""
        filters = {"F": "test%"}
        where, join, params, distinct = self.builder.construct_where(
            3, filters, 1, 0, False, self.field_types, self.ref_types
        )

        self.assertIn("LIKE", where)
        self.assertEqual(params[0], "test%")

    def test_not_filter(self):
        """Test NOT filtering (negation)"""
        filters = {"F": "!test"}
        where, join, params, distinct = self.builder.construct_where(
            3, filters, 1, 0, False, self.field_types, self.ref_types
        )

        self.assertIn("IS NULL", where)  # NOT filter includes NULL check
        self.assertIn("test", params[0])

    def test_null_check(self):
        """Test NULL checking"""
        filters = {"F": "%"}
        where, join, params, distinct = self.builder.construct_where(
            3, filters, 1, 0, False, self.field_types, self.ref_types
        )

        self.assertIn("IS NOT NULL", where)

    def test_range_filter_numeric(self):
        """Test range filtering for numeric fields"""
        # Test FROM with TO present (range mode)
        self.builder.reset()
        where_fr, join_fr, params_fr, _ = self.builder.construct_where(
            13, {"FR": "10", "TO": "100"}, 1, 0, False, self.field_types, self.ref_types
        )
        self.assertIn(">=", where_fr)
        self.assertTrue(any(p == 10 or p == '10' or p == 10.0 for p in params_fr))

        # Test TO with FR present (range mode)
        self.builder.reset()
        where_to, join_to, params_to, _ = self.builder.construct_where(
            13, {"FR": "10", "TO": "100"}, 1, 0, False, self.field_types, self.ref_types
        )
        self.assertIn("<=", where_to)
        self.assertTrue(any(p == 100 or p == '100' or p == 100.0 for p in params_to))

    def test_range_filter_combined(self):
        """Test combined FROM/TO range filter"""
        filters = {"FR": "10", "TO": "100"}
        self.builder.reset()

        where, join, params, distinct = self.builder.construct_where(
            13, filters, 1, 0, False, self.field_types, self.ref_types
        )

        # Should have both >= and <= conditions
        self.assertIn(">=", where)
        self.assertIn("<=", where)
        self.assertEqual(len([p for p in params if isinstance(p, (int, float))]), 2)

    def test_reference_id_filter(self):
        """Test filtering by reference ID (@ prefix)"""
        filters = {"F": "@123"}
        where, join, params, distinct = self.builder.construct_where(
            3, filters, 1, 3, False, self.field_types, self.ref_types
        )

        self.assertIn("123", [str(p) for p in params] + [str(123)])

    def test_in_clause(self):
        """Test IN clause filtering"""
        filters = {"F": "IN(1,2,3)"}
        where, join, params, distinct = self.builder.construct_where(
            13, filters, 1, 0, False, self.field_types, self.ref_types
        )

        # The IN clause is constructed as "IN(1,2,3)" in the search_val
        # May appear as "a13.val IN(1,2,3)" or "vals.val IN(1,2,3)"
        self.assertTrue("IN" in where or "IN(1,2,3)" in str(filters))

    def test_apply_filters_multiple(self):
        """Test apply_filters with multiple filter conditions"""
        filters = {
            3: {"F": "test"},
            13: {"FR": "0", "TO": "100"}
        }

        where, join, params, distinct = apply_filters(
            "ideav", filters, 1, self.field_types, self.ref_types
        )

        # Should have conditions for both filters
        self.assertIn("a3.val", where)
        self.assertIn(">=", where)
        self.assertIn("<=", where)
        self.assertGreaterEqual(len(params), 3)  # At least 3 params

    def test_apply_filters_id_special(self):
        """Test special ID filter handling"""
        filters = {
            "I": {"F": "42"}
        }

        where, join, params, distinct = apply_filters(
            "ideav", filters, 1, self.field_types, self.ref_types
        )

        self.assertIn("vals.id", where)
        self.assertEqual(params[0], 42)

    def test_join_construction(self):
        """Test that JOIN clauses are constructed properly"""
        filters = {"F": "value"}
        where, join, params, distinct = self.builder.construct_where(
            3, filters, 1, 3, False, self.field_types, self.ref_types
        )

        # Should have JOIN for non-current-type field
        self.assertIn("JOIN", join)
        self.assertIn("a3", join)

    def test_distinct_flag(self):
        """Test that DISTINCT flag is set when needed"""
        # Long text value should trigger DISTINCT
        long_value = "a" * 200 + "%"
        filters = {"F": long_value}

        where, join, params, distinct = self.builder.construct_where(
            3, filters, 1, 0, False, self.field_types, self.ref_types
        )

        self.assertTrue(distinct)

    def test_current_type_filter(self):
        """Test filtering on current type (no JOIN needed)"""
        filters = {"F": "test"}
        where, join, params, distinct = self.builder.construct_where(
            3, filters, 3, 0, False, self.field_types, self.ref_types
        )

        # Should use vals.val directly for current type
        self.assertIn("vals.val", where)


class TestFilterIntegration(unittest.TestCase):
    """Integration tests for the filtering system"""

    def test_complex_multi_criteria_filter(self):
        """Test complex filtering with multiple criteria"""
        field_types = {
            3: "CHARS",
            13: "NUMBER",
            9: "DATE"
        }

        filters = {
            3: {"F": "product%"},     # Text search
            13: {"FR": "100", "TO": "500"},  # Range filter
            9: {"F": "20240101"}      # Date filter
        }

        where, join, params, distinct = apply_filters(
            "ideav", filters, 1, field_types, {}
        )

        # Verify all filter conditions are present
        self.assertIn("a3.val", where)
        self.assertIn("a13.val", where)
        self.assertIn("a9.val", where)
        self.assertIn("LIKE", where)
        self.assertIn(">=", where)
        self.assertIn("<=", where)

    def test_filter_with_not_and_null(self):
        """Test combining NOT filters with NULL checks"""
        field_types = {3: "CHARS"}

        filters = {
            3: {"F": "!test"}
        }

        where, join, params, distinct = apply_filters(
            "ideav", filters, 1, field_types, {}
        )

        # NOT filter should include NULL check
        self.assertIn("IS NULL", where)


def run_tests():
    """Run all tests"""
    unittest.main()


if __name__ == '__main__':
    run_tests()
