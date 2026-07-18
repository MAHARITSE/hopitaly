"""
JSON Database Backend for Django.
Stores data in a single JSON file instead of SQLite.
"""
import os
import json
from django.db import DatabaseError
from django.db.backends import BaseDatabaseWrapper, BaseDatabaseIntrospection, BaseDatabaseOperations, BaseDatabaseClient, BaseDatabaseValidation, BaseDatabaseFeatures
from django.db.backends.creation import BaseDatabaseCreation
from django.db.utils import IntegrityError


class DatabaseFeatures(BaseDatabaseFeatures):
    allows_group_by_pk = False
    allows_auto_pk_0 = False
    supports_foreign_keys = False
    can_introspect_foreign_keys = False
    supports_timezones = False
    can_return_id_from_insert = True
    requires_explicit_null_ordering_when_grouping = True
    supports_long_model_names = False
    supports_long_variable_names = False
    supports_subqueries_in_group_by = False
    supports_microsecond_precision = False
    supports_deleting_related = False
    supports_select_for_update = False
    supports_select_related = False
    supports_left_outer_joins = False
    supports_right_outer_joins = False


class DatabaseOperations(BaseDatabaseOperations):
    compiler_module = "json_database.compiler"
    def quote_name(self, name):
        return '"%s"' % name

    def last_insert_id(self, cursor, table_name, pk_name):
        # For JSON backend, return max id
        data = self.connection.data_store.get(table_name, [])
        if not data:
            return 1
        return max([row.get('id', 0) for row in data]) + 1

    def sql_flush(self, style, tables, sequences, allow_cascade=False):
        sql = []
        for table in tables:
            sql.append('DELETE FROM %s' % self.quote_name(table))
        return sql

    def no_limit_value(self):
        return None


class DatabaseClient(BaseDatabaseClient):
    runshell = False


class DatabaseCreation(BaseDatabaseCreation):
    data_types = {
        'AutoField': 'integer',
        'BigIntegerField': 'integer',
        'BinaryField': 'text',
        'BooleanField': 'integer',
        'CharField': 'varchar(255)',
        'CommaSeparatedIntegerField': 'varchar(255)',
        'DateField': 'date',
        'DateTimeField': 'datetime',
        'DecimalField': 'numeric',
        'EmailField': 'varchar(255)',
        'FileField': 'varchar(100)',
        'FilePathField': 'varchar(100)',
        'FloatField': 'real',
        'ImageField': 'varchar(100)',
        'IntegerField': 'integer',
        'IPAddressField': 'varchar(15)',
        'GenericIPAddressField': 'varchar(39)',
        'NullBooleanField': 'integer',
        'OneToOneField': 'integer',
        'PositiveIntegerField': 'integer',
        'PositiveSmallIntegerField': 'integer',
        'SlugField': 'varchar(50)',
        'SmallIntegerField': 'integer',
        'TextField': 'text',
        'TimeField': 'time',
        'URLField': 'varchar(200)',
    }

    def sql_create_model(self, model, style, known_safe_exists=False):
        # JSON backend doesn't need SQL DDL
        return []

    def sql_destroy_model(self, model, references_to_delete, style):
        return []

    def sql_indexes_for_model(self, model, style):
        return []


class DatabaseIntrospection(BaseDatabaseIntrospection):
    def get_table_list(self, cursor):
        # Read from JSON storage
        connection = cursor.connection
        if not hasattr(connection, 'data_store'):
            return []
        return connection.data_store.keys()

    def get_table_description(self, cursor, table_name):
        connection = cursor.connection
        if not hasattr(connection, 'data_store') or table_name not in connection.data_store:
            return []
        data = connection.data_store.get(table_name, [])
        if not data:
            return []
        # Build column descriptions from first row
        first_row = data[0]
        columns = []
        for key, value in first_row.items():
            column_type = self.data_types_reverse.get(type(value).__name__, 'varchar(255)')
            columns.append((key, column_type))
        return columns


class DatabaseWrapper(BaseDatabaseWrapper):
    operators = {
        'exact': '= %s',
        'iexact': 'ILIKE %s',
        'contains': 'LIKE %s',
        'icontains': 'ILIKE %s',
        'gt': '> %s',
        'gte': '>= %s',
        'lt': '< %s',
        'lte': '<= %s',
        'startswith': 'LIKE %s',
        'istartswith': 'ILIKE %s',
        'endswith': 'LIKE %s',
        'iendswith': 'ILIKE %s',
        'isnull': 'IS NULL',
    }

    data_types = DatabaseCreation.data_types
    data_types_reverse = {v: k for k, v in data_types.items()}

    def __init__(self, *args, **kwargs):
        super(DatabaseWrapper, self).__init__(*args, **kwargs)
        self.features = DatabaseFeatures(self)
        self.ops = DatabaseOperations(self)
        self.client = DatabaseClient(self)
        self.creation = DatabaseCreation(self)
        self.introspection = DatabaseIntrospection(self)
        self.validation = BaseDatabaseValidation(self)
        self.data_store_path = kwargs.get('NAME', 'db.json')
        if not os.path.isabs(self.data_store_path):
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            # Try to resolve relative to project base
            self.data_store_path = os.path.join(base_dir, self.data_store_path)
        self.data_store = self._load_store()

    def _load_store(self):
        if os.path.exists(self.data_store_path):
            try:
                with open(self.data_store_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (ValueError, IOError):
                return {}
        return {}

    def _save_store(self):
        with open(self.data_store_path, 'w', encoding='utf-8') as f:
            json.dump(self.data_store, f, indent=2, default=str, ensure_ascii=False)

    def close(self):
        self._save_store()
        super(DatabaseWrapper, self).close()

    def _cursor(self):
        cursor = JSONCursor(self)
        return cursor


class JSONCursor(object):
    def __init__(self, connection):
        self.connection = connection
        self.results = []
        self.rowcount = 0

    def execute(self, sql, params=None):
        # Very basic SQL parser for JSON backend
        sql = sql.strip()
        # Handle SELECT
        if sql.upper().startswith('SELECT '):
            # Extract table name roughly
            table = self._extract_table(sql)
            data = self.connection.data_store.get(table, [])
            # Apply basic WHERE filtering if params provided
            if params:
                data = [row for row in data if self._matches(row, sql, params)]
            self.results = data
            self.rowcount = len(data)
        elif sql.upper().startswith('INSERT '):
            table, values = self._parse_insert(sql, params)
            if table not in self.connection.data_store:
                self.connection.data_store[table] = []
            # Auto-assign id if not provided
            row = dict(values) if isinstance(values, dict) else values
            if isinstance(row, dict) and 'id' not in row:
                max_id = max([r.get('id', 0) for r in self.connection.data_store[table]], default=0)
                row['id'] = max_id + 1
            self.connection.data_store[table].append(row)
            self.rowcount = 1
            self.results = [row]
        elif sql.upper().startswith('UPDATE '):
            table, updates, conditions = self._parse_update(sql, params)
            data = self.connection.data_store.get(table, [])
            for row in data:
                if self._matches(row, sql, params):
                    row.update(updates)
            self.connection.data_store[table] = data
            self.rowcount = len(data)
        elif sql.upper().startswith('DELETE '):
            table = self._extract_table_from_delete(sql)
            data = self.connection.data_store.get(table, [])
            if params:
                new_data = [row for row in data if not self._matches(row, sql, params)]
            else:
                new_data = []
            self.connection.data_store[table] = new_data
            self.rowcount = len(data) - len(new_data)
        else:
            # Ignore other SQL (like CREATE, etc.)
            self.results = []
            self.rowcount = 0
        return self

    def _extract_table(self, sql):
        # Simple extraction: FROM table_name
        parts = sql.split()
        for i, part in enumerate(parts):
            if part.upper() == 'FROM' and i + 1 < len(parts):
                return parts[i + 1].strip('";')
        return 'unknown'

    def _extract_table_from_delete(self, sql):
        parts = sql.split()
        for i, part in enumerate(parts):
            if part.upper() == 'FROM' and i + 1 < len(parts):
                return parts[i + 1].strip('";')
        return 'unknown'

    def _parse_insert(self, sql, params):
        # Very rough parser for INSERT INTO table (cols) VALUES (...)
        table = 'unknown'
        values = {}
        # Try to extract table
        upper = sql.upper()
        if 'INTO' in upper:
            after_into = sql.split('INTO', 1)[1].strip()
            table = after_into.split()[0].strip('";')
        # If params provided as tuple, attempt basic mapping
        if params and isinstance(params, (tuple, list)):
            # Try to get column names from SQL
            cols = []
            if '(' in sql:
                start = sql.find('(')
                end = sql.find(')', start)
                if start != -1 and end != -1:
                    col_str = sql[start+1:end]
                    cols = [c.strip().strip('"') for c in col_str.split(',')]
            values = {}
            for i, val in enumerate(params):
                if i < len(cols):
                    values[cols[i]] = val
                else:
                    values['col_%d' % i] = val
            # If no column names parsed but params is a dict
            if not values and isinstance(params, dict):
                return table, params
            return table, values
        if isinstance(params, dict):
            return table, params
        # Fallback
        return table, params

    def _parse_update(self, sql, params):
        table = 'unknown'
        updates = {}
        # Extract table
        upper = sql.upper()
        if 'UPDATE' in upper:
            after_update = sql.split('UPDATE', 1)[1].strip()
            table = after_update.split()[0].strip('";')
        # Extract SET clauses
        if 'SET' in upper:
            set_part = sql.split('SET', 1)[1]
            # Find WHERE
            where_idx = set_part.upper().find('WHERE')
            if where_idx != -1:
                set_str = set_part[:where_idx]
            else:
                set_str = set_part
            clauses = set_str.split(',')
            for clause in clauses:
                if '=' in clause:
                    col, val = clause.split('=', 1)
                    col = col.strip().strip('"')
                    # We don't evaluate val expressions; rely on params if any
                    updates[col] = val.strip()
        # Try to apply params for updates
        if isinstance(params, dict):
            updates.update(params)
        return table, updates, params

    def _matches(self, row, sql, params):
        # Very basic filtering for JSON backend
        # Check for equality conditions in WHERE clause
        upper_sql = sql.upper()
        if 'WHERE' not in upper_sql:
            return True
        # Try to match each param condition roughly
        # This is a simplified approach: assume params map to conditions
        if isinstance(params, dict):
            for k, v in params.items():
                if k in row:
                    if row[k] != v:
                        return False
            return True
        if isinstance(params, (tuple, list)) and len(params) > 0:
            # Basic: assume first param is id for equality
            if 'id' in row and row['id'] == params[0]:
                return True
            # Try to find a column referenced in SQL
            # Simplified: assume params correspond to conditions in order
            # Just return True for basic compatibility
            return True
        return True

    def executemany(self, sql, param_list):
        for params in param_list:
            self.execute(sql, params)

    def fetchone(self):
        if self.results:
            row = self.results[0]
            self.results = self.results[1:]
            return row
        return None

    def fetchall(self):
        result = self.results
        self.results = []
        return result

    def fetchmany(self, size=None):
        if size is None:
            size = 1
        result = self.results[:size]
        self.results = self.results[size:]
        return result

    def close(self):
        pass
