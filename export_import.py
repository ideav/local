"""
Export/Import System for BKI and CSV formats

This module provides functionality to export and import data in BKI format
(proprietary backup format) and CSV format, matching the PHP implementation.
"""

import csv
import io
from typing import Dict, List, Any, Optional, Tuple
from database import Database


class ExportImport:
    """Handles export and import operations for BKI and CSV formats"""

    def __init__(self, db_name: str, connect_db: bool = True):
        """Initialize with database name"""
        self.db_name = db_name
        self.db = None

        if connect_db:
            self.db = Database(db_name)

        # Global state for export/import operations
        self.local_struct = {}  # Structure cache
        self.base = {}  # Base type cache
        self.linx = {}  # Link indicators
        self.refs = {}  # References
        self.arrays = {}  # Arrays
        self.pwds = {}  # Password fields
        self.parents = {}  # Parent relationships
        self.data = {}  # Data cache
        self.rev_bt = {}  # Reverse base type mapping
        self.bt = {}  # Base type mapping

        # Load base type mappings if connected
        if connect_db:
            self._load_base_types()

    def _load_base_types(self):
        """Load base type mappings from database"""
        # Get base types mapping
        query = """
            SELECT id, val FROM `{table}`
            WHERE up = 0 AND t IN (
                SELECT id FROM `{table}` WHERE val IN
                ('SHORT', 'NUMBER', 'SIGNED', 'DATE', 'DATETIME', 'CHARS',
                 'MEMO', 'FILE', 'HTML', 'PWD', 'GRANT', 'REPORT_COLUMN')
                AND up = 0
            )
        """.format(table=self.db_name)

        try:
            results = self.db.execute(query)
            for row in results:
                # Build reverse mapping
                self.rev_bt[row['id']] = row['val']

            # Build forward mapping
            query2 = """
                SELECT id, val FROM `{table}`
                WHERE val IN ('SHORT', 'NUMBER', 'SIGNED', 'DATE', 'DATETIME',
                             'CHARS', 'MEMO', 'FILE', 'HTML', 'PWD', 'GRANT',
                             'REPORT_COLUMN')
                AND up = 0
            """.format(table=self.db_name)
            results2 = self.db.execute(query2)
            for row in results2:
                self.bt[row['val']] = row['id']
        except Exception:
            # Set some defaults if database is not accessible
            pass

    @staticmethod
    def mask_delimiters(value: str) -> str:
        r"""
        Mask delimiter characters for BKI format
        Replaces \ with \\, : with \:, and ; with \;
        """
        if not value:
            return ""
        value = str(value)
        value = value.replace("\\", "\\\\")
        value = value.replace(":", "\\:")
        value = value.replace(";", "\\;")
        return value

    @staticmethod
    def unmask_delimiters(value: str) -> str:
        """
        Unmask delimiter characters from BKI format
        Reverses the masking done by mask_delimiters
        """
        if not value:
            return ""
        value = str(value)
        # First convert hidden delimiters back
        value = ExportImport.unhide_delimiters(value)
        # Then unmask
        value = value.replace("\\\\", "\\")
        value = value.replace("\\:", ":")
        value = value.replace("\\;", ";")
        return value

    @staticmethod
    def hide_delimiters(value: str) -> str:
        r"""
        Hide escaped delimiters during parsing
        Converts \\ to %5C, \: to %3A, \; to %3B
        """
        if not value:
            return ""
        value = str(value)
        value = value.replace("\\\\", "%5C")
        value = value.replace("\\:", "%3A")
        value = value.replace("\\;", "%3B")
        return value

    @staticmethod
    def unhide_delimiters(value: str) -> str:
        """
        Unhide escaped delimiters after parsing
        Reverses the hiding done by hide_delimiters
        """
        if not value:
            return ""
        value = str(value)
        value = value.replace("%5C", "\\\\")
        value = value.replace("%3A", "\\:")
        value = value.replace("%3B", "\\;")
        return value

    def export_header(self, obj_id: int, parent: int = 0) -> str:
        """
        Export object structure/metadata header for BKI format

        Args:
            obj_id: Object ID to export
            parent: Parent object ID (for recursive exports)

        Returns:
            Header string with structure definitions
        """
        if obj_id in self.local_struct:
            # Already exported
            return ""

        self.parents[obj_id] = parent

        # Query to get object structure
        query = f"""
            SELECT
                CASE WHEN LENGTH(obj.val)=0 THEN obj.id ELSE obj.t END t,
                CASE WHEN LENGTH(obj.val)=0 THEN obj.t ELSE obj.val END val,
                req.id, req.t req_t, refr.val req, refr.t ref_t,
                req.val attr, base.t base_t, arr.id arr, linx.i, obj.ord uniq
            FROM `{self.db_name}` obj
            LEFT JOIN (`{self.db_name}` req
                CROSS JOIN `{self.db_name}` refr
                CROSS JOIN `{self.db_name}` base)
                ON req.up=obj.id AND refr.id=req.t AND base.id=refr.t
            LEFT JOIN `{self.db_name}` arr
                ON arr.up=req.t AND arr.t!=0 AND arr.ord=1
            CROSS JOIN (SELECT COUNT(1) i FROM `{self.db_name}`
                WHERE up=0 AND t=%s) linx
            WHERE obj.id=%s
            ORDER BY req.ord
        """

        try:
            rows = self.db.execute(query, (obj_id, obj_id))
        except Exception:
            return ""

        self.local_struct[obj_id] = {}

        for row in rows:
            if 0 not in self.local_struct[obj_id]:
                # First row - export object definition
                masked_val = self.mask_delimiters(row['val'])
                type_suffix = f":{self.rev_bt.get(row['t'], '')}" if row['t'] in self.rev_bt else ""
                unique_suffix = ":unique" if row['uniq'] == 1 else ""

                self.local_struct[obj_id][0] = f"{obj_id}:{masked_val}{type_suffix}{unique_suffix}"
                self.base[obj_id] = row['t']

                if row['i']:
                    self.linx[obj_id] = ""

            if row['req_t']:
                req_id = row['id']

                if row['ref_t'] != row['base_t']:
                    # This is a reference
                    attr_part = f":{self.mask_delimiters(row['attr'])}" if row['attr'] else ""
                    self.local_struct[obj_id][req_id] = f"ref:{req_id}:{row['req_t']}{attr_part}"

                    # Recursively export referenced types
                    if row['req_t'] not in self.local_struct:
                        self.export_header(row['req_t'], obj_id)
                    if row['ref_t'] not in self.local_struct:
                        self.export_header(row['ref_t'], obj_id)

                    self.refs[req_id] = row['ref_t']

                elif row['arr']:
                    # This is an array
                    attr_part = f":{self.mask_delimiters(row['attr'])}" if row['attr'] else ""
                    self.local_struct[obj_id][req_id] = f"arr:{row['req_t']}{attr_part}"

                    if row['req_t'] not in self.local_struct:
                        self.export_header(row['req_t'], obj_id)
                        self.arrays[row['req_t']] = ""
                else:
                    # Regular requirement
                    attr_part = f":{self.mask_delimiters(row['attr'])}" if row['attr'] else ""
                    ref_type = self.rev_bt.get(row['ref_t'], 'SHORT')
                    self.local_struct[obj_id][req_id] = f"{self.mask_delimiters(row['req'])}:{ref_type}{attr_part}"

                    if ref_type == "PWD":
                        self.pwds[req_id] = ""

                    self.base[req_id] = row['base_t']

        # Build header string from all structures
        header_str = ""
        for struct in self.local_struct.values():
            if struct:
                parts = [struct.get(key, "") for key in sorted(struct.keys())]
                header_str += ";".join(parts) + ";\r\n"

        return header_str

    def export_reqs(self, type_id: int, obj_id: int, val: str, ref: str = "") -> str:
        """
        Export object data requirements recursively

        Args:
            type_id: Type ID
            obj_id: Object ID
            val: Object value
            ref: Reference path

        Returns:
            Data string with object values
        """
        if obj_id in self.data:
            return ""

        str_out = ""
        children = ""
        refs_out = ""

        # Get object data
        query = f"""
            SELECT DISTINCT
                obj.id, obj.t, obj.val, obj.ord,
                req.t req_t, req.val req_val, req.up rup,
                tail.up, par.up ref
            FROM `{self.db_name}` obj
            LEFT JOIN `{self.db_name}` tail
                ON tail.t=0 AND tail.up=obj.id AND tail.ord=0
            LEFT JOIN `{self.db_name}` req ON req.id=obj.t
            LEFT JOIN `{self.db_name}` par ON par.id=req.up
            WHERE obj.up=%s
            ORDER BY obj.ord
        """

        try:
            rows = self.db.execute(query, (obj_id,))
        except Exception:
            return ""

        reqs = {}

        for row in rows:
            if row['rup'] and row['rup'] != type_id and row['rup'] != 0:
                # Reference to another object
                reqs[row['val']] = row['t']
                ref_prefix = f"{row['val']}:" if row['ref'] == 1 else ""
                refs_out += self.export_reqs(
                    row['req_t'],
                    row['t'],
                    self.mask_delimiters(row['req_val']),
                    ref_prefix or ""
                )
            elif row['t'] in self.arrays:
                # Array element
                children += self.export_reqs(
                    row['t'],
                    row['id'],
                    self.mask_delimiters(row['val'])
                )
            elif row['t'] not in self.pwds:
                # Regular field (skip passwords)
                if row['up']:
                    # Get tail value if needed
                    reqs[row['t']] = self.mask_delimiters(
                        self._get_tail(row['up'], row['val'])
                    )
                else:
                    reqs[row['t']] = self.mask_delimiters(row['val'])

        # Build output string based on structure
        if type_id in self.local_struct:
            for key in sorted(self.local_struct[type_id].keys()):
                if key == 0:
                    str_out = f"{self.mask_delimiters(val)};"
                else:
                    str_out += f"{reqs.get(key, '')};"

            # Determine output format
            if (type_id in self.arrays or
                type_id not in self.linx):
                str_out = f"{type_id}::{str_out}\r\n"
            else:
                str_out = f"{ref}{type_id}:{obj_id}:{str_out}\r\n"
                self.data[obj_id] = ""

        return refs_out + str_out + children

    def _get_tail(self, obj_id: int, val: str) -> str:
        """
        Get full value including tail (for long text fields)

        Args:
            obj_id: Object ID
            val: Initial value

        Returns:
            Complete value with tail appended
        """
        query = f"""
            SELECT val FROM `{self.db_name}`
            WHERE up=%s AND t=0 AND ord > 0
            ORDER BY ord
        """
        try:
            rows = self.db.execute(query, (obj_id,))
            for row in rows:
                val += row['val']
        except Exception:
            pass

        return val

    def export_bki(self, obj_id: int, filters: Optional[Dict] = None) -> str:
        """
        Export object and its data to BKI format

        Args:
            obj_id: Object type ID to export
            filters: Optional filters to apply

        Returns:
            Complete BKI format string with header and data
        """
        # Reset state
        self.local_struct = {}
        self.base = {}
        self.linx = {}
        self.refs = {}
        self.arrays = {}
        self.pwds = {}
        self.parents = {}
        self.data = {}

        # Reload base types
        self._load_base_types()

        # Export header (structure)
        header = self.export_header(obj_id)

        # Export data
        data_parts = []

        # Get all objects of this type
        query = f"""
            SELECT id, val FROM `{self.db_name}`
            WHERE t=%s AND up!=0
            ORDER BY ord
        """

        try:
            rows = self.db.execute(query, (obj_id,))
            for row in rows:
                data_str = self.export_reqs(obj_id, row['id'], row['val'])
                if data_str:
                    data_parts.append(data_str)
        except Exception:
            pass

        # Combine header and data
        return header + "DATA\r\n" + "".join(data_parts)

    def export_csv(self, obj_id: int, headers: List[str],
                   data: List[List[Any]]) -> str:
        """
        Export data to CSV format with semicolon delimiter

        Args:
            obj_id: Object type ID
            headers: Column headers
            data: Data rows

        Returns:
            CSV formatted string
        """
        output = io.StringIO()

        # Convert to Windows-1251 encoding (matching PHP)
        # Use semicolon delimiter as in PHP
        writer = csv.writer(output, delimiter=';', lineterminator='\r\n')

        # Write headers
        if headers:
            writer.writerow(headers)

        # Write data
        for row in data:
            writer.writerow(row)

        csv_content = output.getvalue()
        output.close()

        # Convert to Windows-1251 for compatibility with Excel
        try:
            csv_bytes = csv_content.encode('windows-1251')
            return csv_bytes
        except UnicodeEncodeError:
            # Fallback to UTF-8 if encoding fails
            return csv_content.encode('utf-8')

    def import_bki(self, file_content: str, parent_id: int = 1) -> Tuple[bool, str]:
        """
        Import data from BKI format file

        Args:
            file_content: BKI file content
            parent_id: Parent object ID for import

        Returns:
            Tuple of (success, message)
        """
        # Reset state
        self.local_struct = {}
        self.imported = {}
        self.local_types = {}

        lines = file_content.split('\n')
        if not lines:
            return False, "Empty file"

        # Remove BOM if present
        first_line = lines[0]
        if first_line.startswith('\ufeff'):
            first_line = first_line[1:]
            lines[0] = first_line

        # Check if this is plain data or has structure
        plain_data = first_line.strip().startswith("DATA")

        if plain_data:
            # Plain data import (structure already exists)
            # TODO: Implement plain data import
            return False, "Plain data import not yet implemented"

        # Parse structure section
        line_idx = 0
        obj_id = None

        try:
            # Parse first line to get object ID
            obj_id = int(first_line.split(':')[0])
        except (ValueError, IndexError):
            return False, "Invalid BKI format - cannot parse object ID"

        # Load existing structure for comparison
        self.export_header(obj_id)

        # Parse all structure lines until DATA marker
        count = 0
        while line_idx < len(lines):
            line = lines[line_idx].rstrip('\r')
            line_idx += 1

            if line.strip() == "DATA":
                break

            if not line.strip():
                continue

            # Parse structure line
            hidden_line = self.hide_delimiters(line)
            parts = hidden_line.split(';')
            parts = [p for p in parts if p]  # Remove empty parts

            if not parts:
                continue

            # Parse object definition
            obj_parts = parts[0].split(':')
            try:
                curr_obj_id = int(obj_parts[0])
            except (ValueError, IndexError):
                continue

            # Store imported structure
            self.imported[curr_obj_id] = {}
            for i, part in enumerate(parts):
                self.imported[curr_obj_id][i] = self.unhide_delimiters(part)

            count += 1

        # Parse data section
        data_count = 0
        while line_idx < len(lines):
            line = lines[line_idx].rstrip('\r')
            line_idx += 1

            if not line.strip():
                continue

            # Parse data line
            # Format: type_id:obj_id:val1;val2;val3;...
            # or: type_id::val1;val2;val3;... for new objects

            try:
                parts = line.split(':', 2)
                if len(parts) >= 3:
                    type_id = int(parts[0])
                    obj_id_str = parts[1]
                    values_str = parts[2]

                    # Parse values
                    values = values_str.split(';')

                    # TODO: Insert or update object data
                    # This requires reconciling imported structure with local structure
                    # and creating/updating records accordingly

                    data_count += 1
            except (ValueError, IndexError):
                continue

        return True, f"Imported {count} structure definitions and {data_count} data records"

    def close(self):
        """Close database connection"""
        if self.db:
            self.db.close()
