"""
Filtering system for database queries
Implements the Construct_WHERE functionality from PHP version
"""
from typing import Dict, List, Tuple, Optional, Any
from config import Config
from utils import builtin_value


class FilterBuilder:
    """
    Build WHERE clauses and JOIN statements for filtering database records.

    This class replicates the functionality of the PHP Construct_WHERE() function,
    supporting:
    - Complex WHERE clause construction
    - Range filtering (FROM/TO)
    - Text search with LIKE
    - Reference filtering
    - Multi-criteria filters
    - NOT operations (negation)
    - NULL checks
    - IN clause support
    """

    def __init__(self, table_name: str):
        """
        Initialize the FilterBuilder

        Args:
            table_name: Name of the database table
        """
        self.table_name = table_name
        self.where_clauses = []
        self.join_clauses = []
        self.params = []
        self.distinct = False

    def construct_where(
        self,
        key: int,
        filters: Dict[str, Any],
        cur_typ: int,
        join_req: int = 0,
        ignore_tailed: bool = False,
        field_types: Optional[Dict[int, str]] = None,
        ref_types: Optional[Dict[int, int]] = None
    ) -> Tuple[str, str, List[Any], bool]:
        """
        Construct WHERE clause and JOIN statements based on filters.

        This is the main entry point, equivalent to PHP's Construct_WHERE() function.

        Args:
            key: Field type identifier
            filters: Dictionary of filter conditions (e.g., {"F": "value", "FR": "0", "TO": "100"})
            cur_typ: Current object type
            join_req: Join requirement flag
            ignore_tailed: Whether to ignore tailed values
            field_types: Dictionary mapping type IDs to field type names
            ref_types: Dictionary mapping reference type IDs to their target types

        Returns:
            Tuple of (where_clause, join_clause, params, distinct_flag)
        """
        if field_types is None:
            field_types = {}
        if ref_types is None:
            ref_types = {}

        join = join_req != 0

        for filter_key, value in filters.items():
            # Handle NOT operator
            not_flag = False
            not_str = ""
            not_eq = ""

            if isinstance(value, str) and value.startswith("!"):
                not_flag = True
                not_str = "NOT"
                not_eq = "!"
                value = value[1:]

            # Process built-in values
            value = builtin_value(value)

            # Handle NULL checks
            if value == "%":
                search_val = f"IS {'' if not_flag else 'NOT'} NULL"
            # Handle IN clause
            elif isinstance(value, str) and value.strip().upper().startswith("IN(") and value.strip().endswith(")"):
                in_values = value.strip()[3:-1]
                search_val = f"{not_str} IN({in_values})"
            else:
                # Regular value matching
                if isinstance(value, str) and "%" in value:
                    # LIKE search
                    search_val = f"{not_str} LIKE %s"
                    self.params.append(value)
                else:
                    # Exact match
                    search_val = f"{not_eq}=%s"
                    self.params.append(value)

            # Handle reference by ID (@ prefix)
            if isinstance(value, str) and value.startswith("@"):
                value_id = int(value[1:].replace(" ", ""))
                self._handle_reference_filter(
                    key, value_id, cur_typ, join, join_req,
                    not_flag, field_types, ref_types
                )
                continue

            # Get field type for this key
            field_type = field_types.get(key, "")

            # Handle different field types
            if key in ref_types:
                # Reference type
                self._handle_reference_type_filter(
                    key, search_val, join, join_req, not_flag, ref_types
                )
            elif field_type in ("CHARS", "FILE", "MEMO", "HTML"):
                # Text fields
                self._handle_text_filter(
                    key, value, search_val, cur_typ, join, not_flag, ignore_tailed
                )
            elif field_type == "ARRAY":
                # Array fields (with range support)
                self._handle_array_filter(
                    key, value, filter_key, filters, search_val, join, not_flag
                )
            elif field_type in ("DATE", "DATETIME"):
                # Date/datetime fields
                is_date = field_type == "DATE"
                self._handle_datetime_filter(
                    key, value, filter_key, filters, search_val, cur_typ, join, not_flag, is_date
                )
            elif field_type in ("NUMBER", "SIGNED"):
                # Numeric fields
                self._handle_numeric_filter(
                    key, value, filter_key, filters, search_val, cur_typ, join, not_flag
                )
            else:
                # Default field type
                self._handle_default_filter(
                    key, value, search_val, cur_typ, join, not_flag
                )

        # Build final WHERE and JOIN clauses
        where_clause = " AND ".join(self.where_clauses) if self.where_clauses else ""
        join_clause = " ".join(self.join_clauses) if self.join_clauses else ""

        return where_clause, join_clause, self.params, self.distinct

    def _handle_reference_filter(
        self,
        key: int,
        value_id: int,
        cur_typ: int,
        join: bool,
        join_req: int,
        not_flag: bool,
        field_types: Dict[int, str],
        ref_types: Dict[int, int]
    ):
        """Handle filtering by reference ID (@ prefix)"""
        z = self.table_name

        if key == cur_typ:
            # Direct ID filter on current type
            op = "!=" if not_flag else "="
            self.where_clauses.append(f"vals.id{op}%s")
            self.params.append(value_id)
        else:
            if field_types.get(key) == "ARRAY":
                self.distinct = True

            if not_flag:
                # NOT filter
                if key in ref_types:
                    # Reference type with NOT
                    if join:
                        self.join_clauses.append(
                            f"LEFT JOIN ({z} r{key} CROSS JOIN {z} a{key}) "
                            f"ON r{key}.up=vals.id AND a{key}.t=%s "
                            f"AND r{key}.t=a{key}.id AND r{key}.val=%s"
                        )
                        self.params.extend([ref_types[key], join_req])
                    self.where_clauses.append(f"(a{key}.id!=%s OR a{key}.id IS NULL)")
                    self.params.append(value_id)
                else:
                    if join:
                        self.join_clauses.append(
                            f"LEFT JOIN {z} a{key} ON a{key}.up=vals.id AND a{key}.t=%s"
                        )
                        self.params.append(key)
                    self.where_clauses.append(f"(a{key}.id!=%s OR a{key}.id IS NULL)")
                    self.params.append(value_id)
            else:
                # Positive filter
                if key in ref_types:
                    if join:
                        self.join_clauses.append(
                            f"JOIN ({z} r{key} CROSS JOIN {z} a{key}) "
                            f"ON r{key}.up=vals.id AND r{key}.t=a{key}.id "
                            f"AND r{key}.val=%s AND r{key}.t=%s"
                        )
                        self.params.extend([join_req, value_id])
                    self.where_clauses.append(f"a{key}.id=%s")
                    self.params.append(value_id)
                else:
                    if join:
                        self.join_clauses.append(
                            f"JOIN {z} a{key} ON a{key}.up=vals.id AND a{key}.id=%s"
                        )
                        self.params.append(value_id)
                    self.where_clauses.append(f"a{key}.id=%s")
                    self.params.append(value_id)

    def _handle_reference_type_filter(
        self,
        key: int,
        search_val: str,
        join: bool,
        join_req: int,
        not_flag: bool,
        ref_types: Dict[int, int]
    ):
        """Handle reference type fields"""
        z = self.table_name

        if join:
            self.join_clauses.append(
                f"LEFT JOIN ({z} r{key} CROSS JOIN {z} a{key}) "
                f"ON r{key}.up=vals.id AND r{key}.t=a{key}.id "
                f"AND r{key}.val=%s AND a{key}.t=%s"
            )
            self.params.extend([join_req, ref_types[key]])

        if not_flag:
            self.where_clauses.append(f"(a{key}.val {search_val} OR a{key}.val IS NULL)")
        else:
            self.where_clauses.append(f"a{key}.val {search_val}")

    def _handle_text_filter(
        self,
        key: int,
        value: str,
        search_val: str,
        cur_typ: int,
        join: bool,
        not_flag: bool,
        ignore_tailed: bool
    ):
        """Handle text field filtering (CHARS, FILE, MEMO, HTML)"""
        z = self.table_name
        val_lim = Config.VAL_LIM

        if value == "%":
            # NULL check
            if join:
                join_type = "LEFT" if not_flag else ""
                self.join_clauses.append(
                    f"{join_type} JOIN {z} a{key} ON a{key}.up=vals.id AND a{key}.t=%s"
                )
                self.params.append(key)
            self.where_clauses.append(f"a{key}.val {search_val}")
        elif (len(value) <= val_lim and "%" not in value) or ignore_tailed:
            # Short value or ignore_tailed mode
            if key == cur_typ:
                self.where_clauses.append(f"vals.val {search_val}")
            else:
                if join:
                    self.join_clauses.append(
                        f"LEFT JOIN {z} a{key} ON a{key}.up=vals.id AND a{key}.t=%s"
                    )
                    self.params.append(key)

                if not_flag:
                    self.where_clauses.append(f"(a{key}.val {search_val} OR a{key}.val IS NULL)")
                else:
                    self.where_clauses.append(f"a{key}.val {search_val}")
        else:
            # Long value with potential tailing
            self._handle_tailed_text_filter(key, value, search_val, cur_typ, join, not_flag)

    def _handle_tailed_text_filter(
        self,
        key: int,
        value: str,
        search_val: str,
        cur_typ: int,
        join: bool,
        not_flag: bool
    ):
        """Handle text fields that may have tailed (split) values"""
        z = self.table_name
        val_lim = Config.VAL_LIM
        self.distinct = True

        # Create short search value for initial match
        if "%" not in value:
            short_val = value[:val_lim]
            short_search_val = f"=%s"
            self.params.append(short_val)
        else:
            percent_pos = value.find('%')
            short_val = value[:min(percent_pos, val_lim)] + "%"
            short_search_val = f"LIKE %s"
            self.params.append(short_val)

        if key == cur_typ:
            if join:
                self.join_clauses.append(
                    f"LEFT JOIN {z} t{key} ON t{key}.up=vals.id AND t{key}.t=0 "
                    f"LEFT JOIN {z} tp{key} ON tp{key}.up=t{key}.up "
                    f"AND tp{key}.t=0 AND tp{key}.ord=t{key}.ord+1"
                )

            concat_clause = (
                f"CONCAT(CASE WHEN t{key}.ord!=0 THEN '' ELSE vals.val END, "
                f"COALESCE(t{key}.val, ''), COALESCE(tp{key}.val,''))"
            )
            self.where_clauses.append(f"vals.val {short_search_val}")
            self.where_clauses.append(f"{concat_clause} {search_val}")
        else:
            if join:
                self.join_clauses.append(
                    f"LEFT JOIN {z} a{key} ON a{key}.up=vals.id AND a{key}.t=%s "
                    f"LEFT JOIN {z} t{key} ON t{key}.up=a{key}.id AND t{key}.t=0 "
                    f"LEFT JOIN {z} tp{key} ON tp{key}.up=t{key}.up "
                    f"AND tp{key}.t=0 AND tp{key}.ord=t{key}.ord+1"
                )
                self.params.append(key)

            concat_clause = (
                f"CONCAT(CASE WHEN t{key}.ord!=0 THEN '' ELSE a{key}.val END, "
                f"COALESCE(t{key}.val, ''), COALESCE(tp{key}.val,''))"
            )

            if not_flag:
                self.where_clauses.append(
                    f"((a{key}.val {short_search_val} AND {concat_clause} {search_val}) "
                    f"OR a{key}.val IS NULL)"
                )
            else:
                self.where_clauses.append(f"a{key}.val {short_search_val}")
                if not (isinstance(value, str) and value.endswith("%")):
                    self.where_clauses.append(f"{concat_clause} {search_val}")

    def _handle_array_filter(
        self,
        key: int,
        value: Any,
        filter_key: str,
        filters: Dict[str, Any],
        search_val: str,
        join: bool,
        not_flag: bool
    ):
        """Handle array field filtering with range support"""
        z = self.table_name
        self.distinct = True

        if filter_key == "F":
            # Simple filter
            if join:
                self.join_clauses.append(
                    f"LEFT JOIN {z} a{key} ON a{key}.up=vals.id AND a{key}.t=%s"
                )
                self.params.append(key)

            if not_flag:
                self.where_clauses.append(f"(a{key}.val {search_val} OR a{key}.val IS NULL)")
            else:
                self.where_clauses.append(f"a{key}.val {search_val}")
        elif "TO" not in filters or "FR" not in filters:
            # Single value without range
            if join:
                self.join_clauses.append(
                    f"LEFT JOIN {z} a{key} ON a{key}.up=vals.id AND a{key}.t=%s"
                )
                self.params.append(key)

            if value != "%":
                if not_flag:
                    self.where_clauses.append(f"(a{key}.val!=%s OR a{key}.val IS NULL)")
                    self.params.append(value)
                else:
                    self.where_clauses.append(f"a{key}.val=%s")
                    self.params.append(value)
            else:
                self.where_clauses.append(f"a{key}.val {search_val}")
        else:
            # Range filter (FROM/TO)
            if filter_key == "FR":
                if join:
                    self.join_clauses.append(
                        f"JOIN {z} a{key} ON a{key}.up=vals.id AND a{key}.t=%s"
                    )
                    self.params.append(key)

                numeric_val = float(value) if value != 0 else value
                self.where_clauses.append(f"a{key}.val>=%s")
                self.params.append(numeric_val)
            elif filter_key == "TO":
                numeric_val = float(value) if value != 0 else value
                self.where_clauses.append(f"a{key}.val<=%s")
                self.params.append(numeric_val)

    def _handle_datetime_filter(
        self,
        key: int,
        value: Any,
        filter_key: str,
        filters: Dict[str, Any],
        search_val: str,
        cur_typ: int,
        join: bool,
        not_flag: bool,
        is_date: bool
    ):
        """Handle date and datetime field filtering"""
        z = self.table_name

        # Format date value if needed
        if value != "%":
            value = self._format_date_value(value, is_date)

        # Check for range filtering
        if "TO" not in filters or "FR" not in filters:
            # Single value filter
            if key == cur_typ:
                if "%" in str(value):
                    self.where_clauses.append(f"vals.val LIKE %s")
                    self.params.append(value)
                else:
                    self.where_clauses.append(f"vals.val=%s")
                    self.params.append(value)
            else:
                if join:
                    self.join_clauses.append(
                        f"LEFT JOIN {z} a{key} ON a{key}.up=vals.id AND a{key}.t=%s"
                    )
                    self.params.append(key)

                if value == "%":
                    self.where_clauses.append(f"a{key}.val {search_val}")
                elif "%" not in str(value):
                    if not_flag:
                        self.where_clauses.append(f"(a{key}.val!=%s OR a{key}.val IS NULL)")
                        self.params.append(value)
                    else:
                        self.where_clauses.append(f"a{key}.val=%s")
                        self.params.append(value)
                else:
                    if not_flag:
                        self.where_clauses.append(f"(a{key}.val NOT LIKE %s OR a{key}.val IS NULL)")
                        self.params.append(value)
                    else:
                        self.where_clauses.append(f"a{key}.val LIKE %s")
                        self.params.append(value)
        else:
            # Range filter (FROM/TO)
            self._handle_range_filter(key, value, filter_key, cur_typ, join, is_date)

    def _handle_numeric_filter(
        self,
        key: int,
        value: Any,
        filter_key: str,
        filters: Dict[str, Any],
        search_val: str,
        cur_typ: int,
        join: bool,
        not_flag: bool
    ):
        """Handle numeric field filtering"""
        z = self.table_name

        # Check if this is an IN clause (already handled in search_val)
        is_in_clause = "IN(" in search_val

        # Convert to numeric if not zero and not an IN clause
        if not is_in_clause:
            if isinstance(value, str):
                value = value.replace(" ", "")
            if value != 0 and value != "0":
                try:
                    value = float(value) if "." in str(value) else int(value)
                except (ValueError, TypeError):
                    pass

        # Check for range filtering
        if "TO" not in filters or "FR" not in filters:
            # Single value filter
            if key == cur_typ:
                if is_in_clause:
                    self.where_clauses.append(f"vals.val {search_val}")
                elif "%" in str(value):
                    self.where_clauses.append(f"vals.val LIKE %s")
                    self.params.append(value)
                else:
                    self.where_clauses.append(f"vals.val=%s")
                    self.params.append(value)
            else:
                if join:
                    self.join_clauses.append(
                        f"LEFT JOIN {z} a{key} ON a{key}.up=vals.id AND a{key}.t=%s"
                    )
                    self.params.append(key)

                if value == "%":
                    self.where_clauses.append(f"a{key}.val {search_val}")
                elif is_in_clause:
                    if not_flag:
                        self.where_clauses.append(f"(a{key}.val {search_val} OR a{key}.val IS NULL)")
                    else:
                        self.where_clauses.append(f"a{key}.val {search_val}")
                elif "%" not in str(value):
                    if not_flag:
                        self.where_clauses.append(f"(a{key}.val!=%s OR a{key}.val IS NULL)")
                        self.params.append(value)
                    else:
                        self.where_clauses.append(f"a{key}.val=%s")
                        self.params.append(value)
                else:
                    if not_flag:
                        self.where_clauses.append(f"(a{key}.val NOT LIKE %s OR a{key}.val IS NULL)")
                        self.params.append(value)
                    else:
                        self.where_clauses.append(f"a{key}.val LIKE %s")
                        self.params.append(value)
        else:
            # Range filter (FROM/TO)
            self._handle_range_filter(key, value, filter_key, cur_typ, join, False)

    def _handle_range_filter(
        self,
        key: int,
        value: Any,
        filter_key: str,
        cur_typ: int,
        join: bool,
        is_date: bool
    ):
        """Handle range filtering (FROM/TO) for numeric and date fields"""
        z = self.table_name

        if filter_key == "FR":
            if key == cur_typ:
                self.where_clauses.append(f"vals.val>=%s")
                self.params.append(value)
            else:
                if join:
                    self.join_clauses.append(
                        f"JOIN {z} a{key} ON a{key}.up=vals.id AND a{key}.t=%s"
                    )
                    self.params.append(key)
                self.where_clauses.append(f"a{key}.val>=%s")
                self.params.append(value)
        elif filter_key == "TO":
            if key == cur_typ:
                self.where_clauses.append(f"vals.val<=%s")
                self.params.append(value)
            else:
                self.where_clauses.append(f"a{key}.val<=%s")
                self.params.append(value)

    def _handle_default_filter(
        self,
        key: int,
        value: Any,
        search_val: str,
        cur_typ: int,
        join: bool,
        not_flag: bool
    ):
        """Handle default field type filtering"""
        z = self.table_name

        if key == cur_typ:
            self.where_clauses.append(f"vals.val {search_val}")
        else:
            if join:
                self.join_clauses.append(
                    f"LEFT JOIN {z} a{key} ON a{key}.up=vals.id AND a{key}.t=%s"
                )
                self.params.append(key)

            if not_flag:
                self.where_clauses.append(f"(a{key}.val {search_val} OR a{key}.val IS NULL)")
            else:
                self.where_clauses.append(f"a{key}.val {search_val}")

    def _format_date_value(self, value: Any, is_date: bool) -> str:
        """Format date/datetime value"""
        # This would include date formatting logic
        # For now, return as-is
        return str(value)

    def reset(self):
        """Reset the builder state"""
        self.where_clauses = []
        self.join_clauses = []
        self.params = []
        self.distinct = False


def apply_filters(
    db_name: str,
    filters: Dict[int, Dict[str, Any]],
    cur_typ: int,
    field_types: Optional[Dict[int, str]] = None,
    ref_types: Optional[Dict[int, int]] = None
) -> Tuple[str, str, List[Any], bool]:
    """
    Apply multiple filters and return combined WHERE and JOIN clauses.

    Args:
        db_name: Database/table name
        filters: Dictionary mapping field IDs to their filter conditions
        cur_typ: Current object type
        field_types: Dictionary mapping type IDs to field type names
        ref_types: Dictionary mapping reference type IDs to their target types

    Returns:
        Tuple of (where_clause, join_clause, params, distinct_flag)
    """
    builder = FilterBuilder(db_name)
    all_where = []
    all_joins = []
    all_params = []
    distinct = False

    for key, filter_dict in filters.items():
        if key == "U" or key == 0:
            continue

        # Special handling for ID filter
        if key == "I" and filter_dict.get("F", 0) != 0:
            all_where.append(f"vals.id=%s")
            all_params.append(int(filter_dict["F"]))
            continue

        builder.reset()
        where, join, params, is_distinct = builder.construct_where(
            key, filter_dict, cur_typ, key, False, field_types, ref_types
        )

        if where:
            all_where.append(where)
        if join:
            all_joins.append(join)
        all_params.extend(params)
        if is_distinct:
            distinct = True

    final_where = " AND ".join(all_where) if all_where else ""
    final_join = " ".join(all_joins) if all_joins else ""

    return final_where, final_join, all_params, distinct
