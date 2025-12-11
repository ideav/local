"""
Database connection and operations
"""
import pymysql
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

    def close(self):
        """Close database connection"""
        if self.connection and self.connection.open:
            self.connection.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
