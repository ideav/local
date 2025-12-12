"""
Database connection and operations
"""
import pymysql
from typing import Dict, Any, Optional, List
from config import Config


class Database:
    """Database connection handler"""

    def __init__(self, db_name=None):
        self.db_name = db_name or Config.DB_NAME
        self.connection = None
        self.connect()

    def connect(self):
        """Establish database connection"""
        try:
            self.connection = pymysql.connect(
                host=Config.DB_HOST,
                user=Config.DB_USER,
                password=Config.DB_PASSWORD,
                database=self.db_name,
                charset='utf8mb4',
                cursorclass=pymysql.cursors.DictCursor,
                autocommit=False
            )
        except pymysql.Error as e:
            raise Exception(f"Could not connect to database: {e}")

    def execute(self, query, params=None, commit=False):
        """Execute a query and return results"""
        if not self.connection or not self.connection.open:
            self.connect()

        try:
            with self.connection.cursor() as cursor:
                cursor.execute(query, params or ())
                if commit:
                    self.connection.commit()
                if query.strip().upper().startswith('SELECT'):
                    return cursor.fetchall()
                return cursor.lastrowid
        except pymysql.Error as e:
            self.connection.rollback()
            raise Exception(f"Query error: {e}, Query: {query}")

    def execute_one(self, query, params=None):
        """Execute a query and return one result"""
        if not self.connection or not self.connection.open:
            self.connect()

        try:
            with self.connection.cursor() as cursor:
                cursor.execute(query, params or ())
                return cursor.fetchone()
        except pymysql.Error as e:
            raise Exception(f"Query error: {e}, Query: {query}")

    def insert(self, table, up, ord_val, t, val, comment=""):
        """Insert a new record into the database"""
        query = f"INSERT INTO `{table}` (up, ord, t, val) VALUES (%s, %s, %s, %s)"
        return self.execute(query, (up, ord_val, t, val), commit=True)

    def update_val(self, table, record_id, val):
        """Update a record's value"""
        query = f"UPDATE `{table}` SET val = %s WHERE id = %s"
        self.execute(query, (val, record_id), commit=True)

    def delete(self, table, record_id):
        """Delete a record and its children"""
        query = f"DELETE FROM `{table}` WHERE id = %s OR up = %s"
        self.execute(query, (record_id, record_id), commit=True)

    def get_record(self, table, record_id):
        """Get a single record by ID"""
        query = f"SELECT * FROM `{table}` WHERE id = %s"
        return self.execute_one(query, (record_id,))

    def get_records(self, table, conditions=None, limit=None, offset=None):
        """Get multiple records with optional conditions"""
        query = f"SELECT * FROM `{table}`"

        if conditions:
            where_clauses = []
            params = []
            for key, value in conditions.items():
                where_clauses.append(f"{key} = %s")
                params.append(value)
            query += " WHERE " + " AND ".join(where_clauses)
        else:
            params = []

        if limit:
            query += f" LIMIT {int(limit)}"
            if offset:
                query += f" OFFSET {int(offset)}"

        return self.execute(query, tuple(params))

    def get_records_filtered(
        self,
        table: str,
        filters: Optional[Dict[int, Dict[str, Any]]] = None,
        cur_typ: int = 1,
        field_types: Optional[Dict[int, str]] = None,
        ref_types: Optional[Dict[int, int]] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        order_by: Optional[str] = None
    ) -> List[Dict]:
        """
        Get multiple records with advanced filtering support.

        This method implements the filtering system from the PHP version,
        supporting complex WHERE clauses, range filters, text search, etc.

        Args:
            table: Table name
            filters: Dictionary mapping field IDs to their filter conditions
                    Example: {3: {"F": "test"}, 13: {"FR": "0", "TO": "100"}}
            cur_typ: Current object type ID
            field_types: Dictionary mapping type IDs to field type names
            ref_types: Dictionary mapping reference type IDs to their target types
            limit: Maximum number of records to return
            offset: Number of records to skip
            order_by: ORDER BY clause (e.g., "vals.val ASC")

        Returns:
            List of record dictionaries
        """
        from filters import apply_filters

        # Build base query
        distinct = ""
        join_clause = ""
        where_clause = ""
        params = []

        # Apply filters if provided
        if filters:
            where_clause, join_clause, params, is_distinct = apply_filters(
                table, filters, cur_typ, field_types, ref_types
            )
            if is_distinct:
                distinct = "DISTINCT"

        # Construct query
        query = f"SELECT {distinct} vals.* FROM `{table}` vals"

        if join_clause:
            query += f" {join_clause}"

        if where_clause:
            query += f" WHERE {where_clause}"

        if order_by:
            query += f" ORDER BY {order_by}"

        if limit:
            query += f" LIMIT {int(limit)}"
            if offset:
                query += f" OFFSET {int(offset)}"

        return self.execute(query, tuple(params))

    def close(self):
        """Close database connection"""
        if self.connection and self.connection.open:
            self.connection.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
