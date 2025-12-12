"""
Report Compiler - Python port of PHP Compile_Report function

This module provides comprehensive report compilation functionality including:
- Complex SQL query building with JOINs
- Aggregate functions (SUM, AVG, COUNT, MIN, MAX)
- Dynamic WHERE/HAVING clauses
- GROUP BY with totals
- Formulas and calculated fields
"""

import re
from typing import Dict, List, Optional, Any, Tuple
from database import Database
from config import Config
from utils import t9n, builtin_value, write_log


class ReportCompiler:
    """
    Compiles and executes database reports with advanced features
    """

    # Aggregate function names
    AGGR_FUNCS = ['AVG', 'COUNT', 'MAX', 'MIN', 'SUM']

    # Field types that require tail fetching
    TAILED_TYPES = ['CHARS', 'MEMO', 'FILE', 'HTML']

    def __init__(self, db: Database, db_name: str):
        """
        Initialize the report compiler

        Args:
            db: Database connection instance
            db_name: Name of the database
        """
        self.db = db
        self.db_name = db_name
        self.stored_reps = {}
        self.rev_bt = {}  # Reverse basic types mapping
        self.conds = {}  # Filter conditions

    def compile_report(self, report_id: int, execute: bool = True,
                      check_grant: bool = False, request_params: Dict = None) -> Dict:
        """
        Main compilation function - ports PHP Compile_Report function

        Args:
            report_id: ID of the report to compile
            execute: Whether to execute the report or just compile
            check_grant: Whether to check user grants
            request_params: HTTP request parameters (filters, sorting, etc.)

        Returns:
            Dictionary containing compiled report data and SQL
        """
        request_params = request_params or {}

        # Initialize report storage
        if report_id not in self.stored_reps:
            self.stored_reps[report_id] = {
                'params': {},
                'head': {},
                'types': {},
                'columns': {},
                'columns_flip': {},
                'base_in': {},
                'base_out': {},
                'references': {},
                'ref_typ': {},
                'arrays': {},
                'aggrs': {},
                'abn_': {}
            }

        report = self.stored_reps[report_id]

        # Get report header
        header_row = self.db.execute_one(
            f"SELECT val FROM `{self.db_name}` WHERE id = %s",
            (report_id,)
        )

        if not header_row:
            raise ValueError(f"Report #{report_id} was not found")

        report['header'] = header_row['val']

        # Check grants if required
        if check_grant:
            self._check_val_granted(Config.REPORT, header_row['val'])

        # Initialize variables for query building
        tables = {}
        conds = {}
        field_names = {}
        joined_on = {}
        joined = {}
        joined_from = {}
        joined_clause = {}
        joined_join = {}

        # Variable naming based on execution mode
        if execute:
            p = 'a'
            pi = 'i'
            pr = 'r'
            pv = 'v'
            pu = 'u'
        else:
            p = f'a{report_id}_'
            pi = f'i{report_id}_'
            pr = f'r{report_id}_'
            pv = f'v{report_id}_'
            pu = f'u{report_id}_'

        # Get report parameters and columns
        params_query = f"""
            SELECT rep.id up, rep.ord, col_def.up par, col_def.id typ,
                   def_typ.id refr, COALESCE(def_typ.t, def.t, col_def.t) base,
                   CASE WHEN cols.t=0 THEN rep.t
                        ELSE COALESCE(col_typ.t, cols.t, rep.t) END col,
                   CASE WHEN rep.t={Config.REP_COLS} THEN cols.id ELSE '' END id,
                   CASE WHEN cols.t=0 THEN
                        (CASE WHEN cols.ord=0 THEN CONCAT(rep.val, cols.val)
                              ELSE cols.val END)
                        ELSE COALESCE(col_typ.val, cols.val, rep.val) END val,
                   CASE WHEN cols.t IS NULL AND col_def.id IS NULL THEN NULL
                        WHEN col_def.val IS NULL THEN rep.ord
                        WHEN req_def.val IS NULL THEN col_def.val
                        WHEN def_typ.id=def_typ.t THEN CONCAT(req_def.val, ' -> ', def.val)
                        ELSE req_def.val END name,
                   CASE WHEN def_typ.id!=def_typ.t THEN col_def.val END mask,
                   def_typ.val ref_name,
                   rep.t jn, COALESCE(cols.val,'') jnon
            FROM `{self.db_name}` rep
            LEFT JOIN `{self.db_name}` cols ON cols.up=rep.id
            LEFT JOIN `{self.db_name}` col_typ ON col_typ.id=cols.t
                AND rep.t={Config.REP_COLS} AND col_typ.up!={Config.REP_COLS}
            LEFT JOIN `{self.db_name}` col_def ON col_def.id=rep.val
                AND (rep.t={Config.REP_COLS} OR rep.t={Config.REP_JOIN})
            LEFT JOIN `{self.db_name}` req_def ON col_def.up!=0 AND req_def.id=col_def.up
            LEFT JOIN `{self.db_name}` def ON col_def.up!=0 AND def.id=col_def.t
            LEFT JOIN `{self.db_name}` def_typ ON def.id!=def.t AND def_typ.id=def.t
            WHERE rep.up={report_id}
            ORDER BY rep.ord
        """

        data_set = self.db.execute(params_query)

        # Process report parameters and columns
        for row in data_set:
            if row['jn'] == Config.REP_JOIN:
                # Handle JOIN definitions
                key = row['par'] if row['par'] > 0 else (row['typ'] if row['typ'] > 0 else row['up'])
                if Config.REP_JOIN not in report:
                    report[Config.REP_JOIN] = {}
                if key not in report[Config.REP_JOIN]:
                    report[Config.REP_JOIN][key] = {}

                jnon_val = self._get_tail(row['id'], row['jnon']) if len(row['jnon']) >= Config.VAL_LIM else row['jnon']
                report[Config.REP_JOIN][key][row['col']] = jnon_val

            elif row['base'] or row['id']:
                # Handle column definitions
                ord_key = row['ord']

                # Set column header
                if row.get('mask'):
                    alias = self._fetch_alias(row['mask'], row['ref_name'])
                    if alias == row['ref_name']:
                        report['head'][ord_key] = f"{row['name']} -> {alias}"
                    else:
                        report['head'][ord_key] = f"{row['name']} -> {alias} ({row['ref_name']})"
                else:
                    report['head'][ord_key] = row['name']

                report['types'][ord_key] = row['typ'] if row.get('typ') else ''
                report['columns'][ord_key] = row['up']

                if row['par']:
                    if 'parents' not in self.stored_reps:
                        self.stored_reps['parents'] = {}
                    self.stored_reps['parents'][row['typ']] = row['par']

                if row['refr']:
                    if 'refs' not in report:
                        report['refs'] = {}
                    report['refs'][ord_key] = row['refr']

                # Store column value
                val = self._get_tail(row['id'], row['val']) if len(row['val']) >= Config.VAL_LIM else row['val'].strip()
                report[row['col']][ord_key] = val

                # Update reverse basic types mapping
                if row['typ'] and row['typ'] not in self.rev_bt:
                    self.rev_bt[row['typ']] = Config.BASIC_TYPES.get(row['base'], 'SHORT')

            else:
                # Handle report parameters
                param_key = row['col']
                if param_key in report['params']:
                    report['params'][param_key] += row['val']
                else:
                    report['params'][param_key] = row['val']

        # Create columns flip index for quick lookup
        report['columns_flip'] = {v: k for k, v in report['columns'].items()}

        # Validate that report has columns
        if not isinstance(report.get('types'), dict) or len(report['types']) == 0:
            raise ValueError(f"{t9n('[RU]Пустой отчет[EN]Empty report')} {report['header']}")

        # Process dynamic SELECT fields from request
        self._process_dynamic_select(report, request_params, execute)

        # Process custom TOTALS from request
        self._process_custom_totals(report, request_params)

        # Set column names and formats
        for key, typ in report['types'].items():
            if Config.REP_COL_NAME in report and key in report[Config.REP_COL_NAME]:
                report['head'][key] = report[Config.REP_COL_NAME][key]

            if Config.REP_COL_FORMAT in report and key in report[Config.REP_COL_FORMAT]:
                if report[Config.REP_COL_FORMAT][key]:
                    report['base_out'][key] = report['base_in'][key] = report[Config.REP_COL_FORMAT][key]

            if key not in report['base_out']:
                report['base_out'][key] = report['base_in'][key] = self.rev_bt.get(typ, 'SHORT')

        # Build the SQL query
        sql_result = self._build_sql_query(
            report_id, report, tables, conds, field_names, joined_on,
            joined, joined_from, joined_clause, joined_join,
            p, pi, pr, pv, pu, request_params, execute
        )

        # Store compiled SQL
        report['sql'] = sql_result['sql']

        # Execute if required
        if execute and sql_result['sql']:
            results = self.db.execute(sql_result['sql'])
            report['results'] = results

        return report

    def _build_sql_query(self, report_id: int, report: Dict, tables: Dict,
                         conds: Dict, field_names: Dict, joined_on: Dict,
                         joined: Dict, joined_from: Dict, joined_clause: Dict,
                         joined_join: Dict, p: str, pi: str, pr: str,
                         pv: str, pu: str, request_params: Dict, execute: bool) -> Dict:
        """
        Build the complete SQL query for the report

        This is the core query building logic ported from PHP
        """
        # Get references and arrays for JOINs
        refs_query = f"""
            SELECT DISTINCT
                CASE WHEN col_def.up=0 THEN col_def.id ELSE col_def.up END typ,
                reqs.id req, req_refs.t refr, arr_vals.up arr
            FROM `{self.db_name}` rep
            LEFT JOIN `{self.db_name}` col_def ON col_def.id=rep.val
            LEFT JOIN `{self.db_name}` reqs ON reqs.up=
                CASE WHEN col_def.up=0 THEN col_def.id ELSE col_def.up END
            LEFT JOIN `{self.db_name}` req_refs ON req_refs.id=reqs.t
                AND LENGTH(req_refs.val)=0
            LEFT JOIN `{self.db_name}` arr_vals ON arr_vals.up=reqs.t
                AND arr_vals.ord=1
            WHERE rep.up={report_id} AND rep.t={Config.REP_COLS}
                AND (req_refs.id IS NOT NULL OR arr_vals.id IS NOT NULL)
            ORDER BY rep.ord
        """

        refs_data = self.db.execute(refs_query)

        for row in refs_data:
            if row['refr']:
                if 'references' not in report:
                    report['references'] = {}
                if row['typ'] not in report['references']:
                    report['references'][row['typ']] = {}
                report['references'][row['typ']][row['refr']] = row['req']
                report['ref_typ'][row['req']] = row['refr']
            else:
                if 'arrays' not in report:
                    report['arrays'] = {}
                if row['typ'] not in report['arrays']:
                    report['arrays'][row['typ']] = {}
                report['arrays'][row['typ']][row['arr']] = row['req']

        # Process filter conditions from request parameters
        self._process_filter_conditions(report, request_params)

        # Initialize query building variables
        fields = {}
        names = {}
        fields_orig = {}
        display_val = {}
        display_name = {}
        filters = {}
        master_filters = {}
        sort_by_arr = {}
        master = None
        distinct = ""

        # Build JOINs and field lists iteratively
        not_all_joined = True
        max_iterations = 100  # Safety limit
        iteration = 0

        while not_all_joined and iteration < max_iterations:
            not_all_joined = False
            no_progress = True
            iteration += 1

            for key, typ in report['types'].items():
                if not typ:
                    # Handle calculated/formula fields
                    no_progress = False
                    field = self._build_formula_field(report, key, p)
                    name = self._build_field_name(report, key, pv)

                    fields[key] = field
                    names[key] = name

                    if Config.REP_COL_HIDE not in report or key not in report[Config.REP_COL_HIDE]:
                        field_names[key] = f"{field} {name}"
                        display_val[key] = field
                        display_name[key] = name

                        # Handle aggregate functions for formulas
                        if Config.REP_COL_FUNC in report and key in report[Config.REP_COL_FUNC]:
                            if report[Config.REP_COL_FUNC][key] in self.AGGR_FUNCS:
                                func = report[Config.REP_COL_FUNC][key]
                                field_names[key] = f"{func}({field}) {name}"
                                fields[key] = f"{func}({field})"
                                display_val[key] = f"{func}({field})"
                                report['aggrs'][key] = ''
                    continue

                # Handle regular typed fields
                par = self.stored_reps.get('parents', {}).get(typ, typ)
                par_alias = par
                alias = typ

                # Determine field expression
                field = self._get_field_expression(report, key, typ, alias, p)

                # Initialize master table
                if master is None:
                    master = par_alias
                    tables[master] = f"`{self.db_name}` {p}{master}"
                    conds[master] = f"{p}{master}.up!=0 AND LENGTH({p}{master}.val)!=0 AND {p}{master}.t={par}"

                # Build JOINs for this field's type
                if alias not in tables:
                    if par_alias not in tables:
                        # Parent not yet joined - try next iteration
                        not_all_joined = True
                        continue

                    # Build JOIN clause
                    join_result = self._build_join_clause(
                        report_id, report, typ, par, alias, par_alias, master,
                        tables, joined, joined_from, joined_clause, joined_on,
                        p, pr, key
                    )

                    if not join_result['success']:
                        not_all_joined = True
                        continue

                    tables.update(join_result['tables'])
                    joined.update(join_result['joined'])

                no_progress = False

                # Build field name and display expressions
                if key in fields:
                    continue

                name = self._build_field_name(report, key, pv, par)
                fields_orig[key] = field.replace('.', '_') if master != par_alias else field

                # Handle formulas with [THIS] placeholder
                if Config.REP_COL_FORMULA in report and key in report[Config.REP_COL_FORMULA]:
                    formula = report[Config.REP_COL_FORMULA][key]
                    if '[THIS]' in formula:
                        field = formula.replace('[THIS]', field)

                fields[key] = field
                names[key] = name

                # Add to field list if not hidden
                if Config.REP_COL_HIDE not in report or key not in report[Config.REP_COL_HIDE]:
                    self._add_field_to_select(
                        report, key, field, name, fields_orig, field_names,
                        display_val, display_name, joined, master, par_alias,
                        alias, p, pi
                    )

            if not_all_joined and no_progress:
                # No progress made - cannot resolve all JOINs
                raise ValueError(f"Unable to resolve all JOINs for report {report_id}")

        # Build WHERE clause
        where_parts = []
        for key, cond in conds.items():
            where_parts.append(cond)

        # Add filters
        for key, filter_expr in filters.items():
            where_parts.append(filter_expr)

        where_clause = ' AND '.join(where_parts) if where_parts else '1=1'

        # Build SELECT clause
        select_fields = ', '.join(field_names.values()) if field_names else '*'

        # Build FROM clause
        from_clause = ', '.join(tables.values())

        # Build GROUP BY clause
        group_by = self._build_group_by(report, fields)

        # Build HAVING clause
        having = self._build_having(report, fields)

        # Build ORDER BY clause
        order_by = self._build_order_by(report, sort_by_arr, fields)

        # Build LIMIT clause
        limit = self._build_limit(report, request_params)

        # Assemble final SQL
        sql = f"SELECT {distinct} {select_fields} FROM {from_clause}"
        if where_clause and where_clause != '1=1':
            sql += f" WHERE {where_clause}"
        if group_by:
            sql += f" GROUP BY {group_by}"
        if having:
            sql += f" HAVING {having}"
        if order_by:
            sql += f" ORDER BY {order_by}"
        if limit:
            sql += f" LIMIT {limit}"

        return {
            'sql': sql,
            'fields': fields,
            'display_val': display_val,
            'display_name': display_name
        }

    def _process_dynamic_select(self, report: Dict, request_params: Dict, execute: bool):
        """Process dynamic SELECT fields from request"""
        if 'SELECT' not in request_params or not execute:
            return

        i = len(report['columns'])
        select_parts = request_params['SELECT'].replace('\\,', '%2c').split(',')

        for k, v in enumerate(select_parts):
            f = v.replace('\\:', '%3a').split(':')
            if f[0] not in report['columns_flip']:
                i += 1
                field_expr = f[0].replace('%2c', ',').replace('%3a', ':') if f[0] else "''"

                report['types'][i] = ''
                report['columns'][i] = field_expr
                report['head'][i] = field_expr
                report[Config.REP_COL_FORMULA][i] = field_expr
                report['columns_flip'][field_expr] = i

                # Check for filter
                if f'FR_{k}' in request_params:
                    report[Config.REP_COL_FROM][i] = request_params[f'FR_{k}']

    def _process_custom_totals(self, report: Dict, request_params: Dict):
        """Process custom TOTALS from request"""
        if 'TOTALS' not in request_params:
            return

        select_parts = request_params['TOTALS'].split(',')
        tmp = {}

        for v in select_parts:
            f = v.split(':')
            if len(f) == 2 and f[0] in report['columns_flip'] and f[1] in self.AGGR_FUNCS:
                tmp[report['columns_flip'][f[0]]] = f[1]

        if tmp:
            report[Config.REP_COL_TOTAL] = tmp

    def _process_filter_conditions(self, report: Dict, request_params: Dict):
        """Process filter conditions from request parameters"""
        for key, typ in report['types'].items():
            # Check for named filters
            if Config.REP_COL_NAME in report and key in report[Config.REP_COL_NAME]:
                str_key = report[Config.REP_COL_NAME][key].replace(' ', '_')
                if f'FR_{str_key}' in request_params and request_params[f'FR_{str_key}']:
                    if key not in self.conds:
                        self.conds[key] = {}
                    self.conds[key]['FR'] = request_params[f'FR_{str_key}']
                if f'TO_{str_key}' in request_params and request_params[f'TO_{str_key}']:
                    if key not in self.conds:
                        self.conds[key] = {}
                    self.conds[key]['TO'] = request_params[f'TO_{str_key}']

            # Use default filters from report definition
            if key not in self.conds or 'FR' not in self.conds[key]:
                if Config.REP_COL_FROM in report and key in report[Config.REP_COL_FROM]:
                    if key not in self.conds:
                        self.conds[key] = {}
                    self.conds[key]['FR'] = report[Config.REP_COL_FROM][key]

            if key not in self.conds or 'TO' not in self.conds[key]:
                if Config.REP_COL_TO in report and key in report[Config.REP_COL_TO]:
                    if key not in self.conds:
                        self.conds[key] = {}
                    self.conds[key]['TO'] = report[Config.REP_COL_TO][key]

    def _build_formula_field(self, report: Dict, key: int, p: str) -> str:
        """Build field expression for formula/calculated fields"""
        if Config.REP_COL_FORMULA in report and key in report[Config.REP_COL_FORMULA]:
            field = report[Config.REP_COL_FORMULA][key]
            if Config.REP_COL_FUNC in report and key in report[Config.REP_COL_FUNC]:
                if report[Config.REP_COL_FUNC][key] == 'abn_URL':
                    field = f"'abn_URL({key})'"
        elif Config.REP_COL_FUNC in report and key in report[Config.REP_COL_FUNC]:
            field = f"'{report[Config.REP_COL_FUNC][key]} {key}'"
        else:
            field = t9n(f"[RU]'Пустая или неверная формула в вычисляемой колонке (№{key})'[EN]'Empty or incorrect formula in column #{key}'")

        return field

    def _build_field_name(self, report: Dict, key: int, pv: str, par: int = None) -> str:
        """Build field name/alias"""
        if Config.REP_COL_NAME in report and key in report[Config.REP_COL_NAME]:
            escaped_name = report[Config.REP_COL_NAME][key].replace("'", "\\'")
            return f"'{escaped_name}'"
        elif par:
            return f"{pv}{key}_{par}"
        else:
            return f"{pv}{key}"

    def _get_field_expression(self, report: Dict, key: int, typ: int, alias: int, p: str) -> str:
        """Get the SQL field expression for a column"""
        # Check for abnormal functions
        if Config.REP_COL_FUNC in report and key in report[Config.REP_COL_FUNC]:
            func = report[Config.REP_COL_FUNC][key]
            if func.startswith('abn_'):
                if func == 'abn_ID':
                    return f"{p}{alias}.id"
                elif func == 'abn_UP':
                    return f"{p}{alias}.up"
                elif func == 'abn_TYP':
                    return f"{p}{alias}.t"
                elif func == 'abn_ORD':
                    return f"{p}{alias}.ord"
                elif func == 'abn_REQ':
                    return f"{alias}"
                elif func == 'abn_BT':
                    return str(self.rev_bt.get(typ, 0))

                if func in ['abn_ID', 'abn_UP', 'abn_TYP', 'abn_ORD']:
                    report['base_in'][key] = 'NUMBER'
                    if Config.REP_COL_FUNC in report and key in report[Config.REP_COL_FUNC]:
                        del report[Config.REP_COL_FUNC][key]
                    report['abn_'][key] = ''

        return f"{p}{alias}.val"

    def _build_join_clause(self, report_id: int, report: Dict, typ: int, par: int,
                          alias: int, par_alias: int, master: int, tables: Dict,
                          joined: Dict, joined_from: Dict, joined_clause: Dict,
                          joined_on: Dict, p: str, pr: str, key: int) -> Dict:
        """Build JOIN clause for a type"""
        result = {
            'success': False,
            'tables': {},
            'joined': {}
        }

        # Check for custom JOIN definition
        if Config.REP_JOIN in report and par_alias in report[Config.REP_JOIN]:
            rf = report[Config.REP_JOIN][par_alias]
            join_expr = rf.get(Config.REP_JOIN_ON, '')

            # Check if all required types are already joined
            matches = re.findall(r':(\d+):', join_expr)
            for j in matches:
                j = int(j)
                if j != par_alias and j not in tables:
                    # Required type not yet joined
                    return result

            custom_alias = rf.get(Config.REP_ALIAS, par_alias)
            tables[custom_alias] = f"LEFT JOIN `{self.db_name}` {p}{custom_alias} ON {p}{custom_alias}.t={par_alias} AND {join_expr}"

            result['success'] = True
            result['tables'] = tables
            return result

        # Standard JOIN logic - try to find relationship
        for t, j in tables.items():
            if t == master:
                continue

            # Check for reference relationship
            if 'references' in report and par in report.get('references', {}).get(t, {}):
                # Found reference link
                req_id = report['references'][t][par]
                tables[par_alias] = f"LEFT JOIN (`{self.db_name}` {pr}{par_alias} CROSS JOIN `{self.db_name}` {p}{par_alias}) ON {pr}{par_alias}.val='{req_id}' AND {pr}{par_alias}.up={p}{t}.id AND {p}{par_alias}.id={pr}{par_alias}.t AND {p}{par_alias}.t={par}"

                result['success'] = True
                result['tables'] = tables
                return result

            # Check for array relationship
            if 'arrays' in report and par in report.get('arrays', {}).get(t, {}):
                tables[par_alias] = f"LEFT JOIN `{self.db_name}` {p}{par_alias} ON {p}{par_alias}.up={p}{t}.id AND {p}{par_alias}.t={par}"

                result['success'] = True
                result['tables'] = tables
                return result

        return result

    def _add_field_to_select(self, report: Dict, key: int, field: str, name: str,
                            fields_orig: Dict, field_names: Dict, display_val: Dict,
                            display_name: Dict, joined: Dict, master: int,
                            par_alias: int, alias: int, p: str, pi: str):
        """Add a field to the SELECT clause"""
        display_name[key] = name

        # Handle aggregate functions
        if Config.REP_COL_FUNC in report and key in report[Config.REP_COL_FUNC]:
            func = report[Config.REP_COL_FUNC][key]
            if func in self.AGGR_FUNCS:
                base_type = report['base_in'].get(key, 'SHORT')
                if base_type in ['NUMBER', 'DATETIME']:
                    field_names[key] = f"{func}(CAST({field} AS SIGNED)) {name}"
                    display_val[key] = f"{func}(CAST({fields_orig[key]} AS SIGNED))"
                elif base_type == 'SIGNED':
                    field_names[key] = f"{func}(CAST({field} AS DOUBLE)) {name}"
                    display_val[key] = f"{func}(CAST({fields_orig[key]} AS DOUBLE))"
                else:
                    field_names[key] = f"{func}({field}) {name}"
                    display_val[key] = f"{func}({fields_orig[key]})"

                report['aggrs'][key] = ''
                return

        # Standard field
        field_names[key] = f"{field} {name}"
        display_val[key] = field if master == par_alias else fields_orig[key]

    def _build_group_by(self, report: Dict, fields: Dict) -> str:
        """Build GROUP BY clause"""
        if 'aggrs' not in report or not report['aggrs']:
            return ''

        group_fields = []
        for key, field in fields.items():
            if key not in report['aggrs']:
                if Config.REP_COL_HIDE not in report or key not in report[Config.REP_COL_HIDE]:
                    group_fields.append(field)

        return ', '.join(group_fields) if group_fields else ''

    def _build_having(self, report: Dict, fields: Dict) -> str:
        """Build HAVING clause for aggregate filtering"""
        having_parts = []

        for key in report.get('types', {}).keys():
            if Config.REP_COL_HAV_FR in report and key in report[Config.REP_COL_HAV_FR]:
                if key in fields:
                    having_parts.append(f"{fields[key]} >= {report[Config.REP_COL_HAV_FR][key]}")

            if Config.REP_COL_HAV_TO in report and key in report[Config.REP_COL_HAV_TO]:
                if key in fields:
                    having_parts.append(f"{fields[key]} <= {report[Config.REP_COL_HAV_TO][key]}")

        return ' AND '.join(having_parts) if having_parts else ''

    def _build_order_by(self, report: Dict, sort_by_arr: Dict, fields: Dict) -> str:
        """Build ORDER BY clause"""
        if not sort_by_arr and Config.REP_COL_SORT in report:
            # Build from report sort definitions
            for key, sort_val in report[Config.REP_COL_SORT].items():
                if key in fields:
                    base_type = report['base_out'].get(key, 'SHORT')
                    field_expr = fields[key]

                    if base_type in ['NUMBER', 'SIGNED']:
                        field_expr = f"CAST({field_expr} AS SIGNED)"

                    if sort_val < 0:
                        sort_by_arr[abs(sort_val)] = f"{field_expr} DESC"
                    else:
                        sort_by_arr[sort_val] = field_expr

        if sort_by_arr:
            # Sort by key to maintain order
            sorted_items = sorted(sort_by_arr.items())
            return ', '.join([v for k, v in sorted_items])

        return ''

    def _build_limit(self, report: Dict, request_params: Dict) -> str:
        """Build LIMIT clause"""
        if Config.REP_LIMIT in report['params']:
            return str(report['params'][Config.REP_LIMIT])

        if 'LIMIT' in request_params:
            return str(request_params['LIMIT'])

        return ''

    def _get_tail(self, obj_id: int, value: str) -> str:
        """Get tail value for long text fields"""
        if not obj_id:
            return value

        tail_row = self.db.execute_one(
            f"SELECT val FROM `{self.db_name}` WHERE up = %s AND t = 0 AND ord = 0",
            (obj_id,)
        )

        if tail_row:
            return value + tail_row['val']

        return value

    def _fetch_alias(self, mask: str, orig: str) -> str:
        """Fetch alias from mask pattern"""
        match = re.search(Config.ALIAS_MASK, mask)
        if match:
            return match.group(1)
        return orig

    def _check_val_granted(self, typ: int, val: str):
        """Check if user has grants for this value"""
        # Placeholder for grant checking logic
        # In full implementation, would check user permissions
        pass

    def construct_where(self, key: int, filter_dict: Dict, cur_typ: int,
                       join_req: int = 0, ignore_tailed: bool = False) -> str:
        """
        Construct WHERE clause conditions

        Port of PHP Construct_WHERE function
        """
        where_parts = []

        if 'FR' in filter_dict:
            fr_val = builtin_value(filter_dict['FR'])
            if cur_typ in self.rev_bt:
                base_type = self.rev_bt[cur_typ]
                if base_type in ['NUMBER', 'SIGNED', 'DATETIME']:
                    where_parts.append(f"a{key}.val >= '{fr_val}'")
                else:
                    where_parts.append(f"a{key}.val >= '{fr_val}'")
            else:
                where_parts.append(f"a{key}.val >= '{fr_val}'")

        if 'TO' in filter_dict:
            to_val = builtin_value(filter_dict['TO'])
            if cur_typ in self.rev_bt:
                base_type = self.rev_bt[cur_typ]
                if base_type in ['NUMBER', 'SIGNED', 'DATETIME']:
                    where_parts.append(f"a{key}.val <= '{to_val}'")
                else:
                    where_parts.append(f"a{key}.val <= '{to_val}'")
            else:
                where_parts.append(f"a{key}.val <= '{to_val}'")

        return ' AND '.join(where_parts) if where_parts else ''
