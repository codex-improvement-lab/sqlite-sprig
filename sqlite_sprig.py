"""SQLite Sprig: a selected branch, with the schema and parents it needs."""
from __future__ import annotations

import argparse
from collections import defaultdict, deque
from dataclasses import dataclass
import json
import math
import os
from pathlib import Path
import sqlite3
import tempfile
import time


__version__ = "0.1.0a1"


class SliceError(Exception):
    pass


def quote(value: str) -> str:
    return '"' + value.replace('"', '""') + '"'


def name_key(value: str) -> str:
    # SQLite identifier folding is ASCII-only, not Unicode casefolding.
    return value.translate(str.maketrans('ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'))


@dataclass
class Table:
    name: str
    columns: tuple[str, ...]
    primary_key: tuple[str, ...]
    identity: tuple[str, ...]
    rowid_alias: str | None
    sql: str


@dataclass
class ForeignKey:
    child: str
    parent: str
    child_columns: tuple[str, ...]
    parent_columns: tuple[str, ...]


class Snapshot:
    def __init__(self, connection: sqlite3.Connection, max_rows: int, deadline: float):
        self.connection = connection
        self.max_rows = max_rows
        self.deadline = deadline
        self.tables: dict[str, Table] = {}
        self.names: dict[str, str] = {}
        self.parents: dict[str, list[ForeignKey]] = defaultdict(list)
        self.children: dict[str, list[ForeignKey]] = defaultdict(list)
        self.selected: dict[str, dict[tuple, None]] = {}
        self.row_count = 0
        self._read_schema()

    def check_time(self) -> None:
        if time.monotonic() > self.deadline:
            raise SliceError('The extraction timed out.')

    def _read_schema(self) -> None:
        if sqlite3.sqlite_version_info < (3, 37):
            raise SliceError('SQLite Sprig requires SQLite 3.37 or newer.')
        metadata = self.connection.execute('PRAGMA main.table_list').fetchall()
        definitions = dict(self.connection.execute("SELECT name,sql FROM sqlite_schema WHERE type='table' AND sql IS NOT NULL"))
        for _, name, kind, _, without_rowid, _ in metadata:
            if name.startswith('sqlite_'):
                continue
            if kind in {'virtual', 'shadow'}:
                raise SliceError('Virtual tables are not supported by SQLite Sprig.')
            if kind != 'table':
                continue
            fields = self.connection.execute('PRAGMA table_xinfo(' + quote(name) + ')').fetchall()
            columns = tuple(field[1] for field in fields if field[6] == 0)
            pk = tuple(field[1] for field in sorted(fields, key=lambda field: field[5]) if field[5])
            alias = None
            if without_rowid:
                identity = pk
            else:
                occupied = {name_key(field[1]) for field in fields}
                alias = next((candidate for candidate in ['_rowid_', 'rowid', 'oid'] if candidate not in occupied), None)
                if alias is None:
                    raise SliceError(f'{name}: all hidden rowid aliases are shadowed.')
                identity = (alias,)
            self.tables[name] = Table(name, columns, pk, identity, alias, definitions[name])
            self.names[name_key(name)] = name
            self.selected[name] = {}
        for name in self.tables:
            groups: dict[int, list[tuple]] = defaultdict(list)
            for row in self.connection.execute('PRAGMA foreign_key_list(' + quote(name) + ')'):
                groups[row[0]].append(row)
            for group in groups.values():
                group.sort(key=lambda row: row[1])
                parent = self.names.get(name_key(group[0][2]))
                if parent is None:
                    raise SliceError(f'{name}: foreign-key parent table is missing.')
                parent_cols = tuple(row[4] for row in group)
                if any(column is None for column in parent_cols):
                    parent_cols = self.tables[parent].primary_key
                if len(parent_cols) != len(group):
                    raise SliceError(f'{name}: foreign-key columns cannot be resolved.')
                fk = ForeignKey(name, parent, tuple(row[3] for row in group), parent_cols)
                self.parents[name].append(fk)
                self.children[parent].append(fk)

    def add(self, table: str, key: tuple) -> bool:
        self.check_time()
        if key in self.selected[table]:
            return False
        if self.row_count >= self.max_rows:
            raise SliceError(f'Selection exceeds the {self.max_rows} row limit.')
        self.selected[table][key] = None
        self.row_count += 1
        return True

    def related(self, fk: ForeignKey, key: tuple, to_parent: bool):
        self.check_time()
        parent, child = self.tables[fk.parent], self.tables[fk.child]
        target, target_alias = (parent, 'p') if to_parent else (child, 'c')
        origin, origin_alias = (child, 'c') if to_parent else (parent, 'p')
        projection = ','.join(target_alias + '.' + quote(column) for column in target.identity)
        # The FK comparison uses the parent's collation and affinity. Unary +
        # strips the child's column affinity, otherwise a NUMERIC child can
        # make a TEXT parent '01' compare equal to a different parent '1'.
        join = ' AND '.join('p.' + quote(p) + '=+c.' + quote(c)
                            for p, c in zip(fk.parent_columns, fk.child_columns))
        where = ' AND '.join(origin_alias + '.' + quote(column) + ' IS ?' for column in origin.identity)
        sql = (f'SELECT {projection} FROM {quote(parent.name)} p JOIN {quote(child.name)} c ON {join}'
               f' WHERE {where} ORDER BY {projection}')
        for result in self.connection.execute(sql, key):
            self.check_time()
            yield result

    def collect(self, root: str, where: str, include_children: bool) -> tuple[str, int]:
        root_name = self.names.get(name_key(root))
        if root_name is None:
            raise SliceError(f'Unknown root table: {root}')
        table = self.tables[root_name]
        projection = ','.join(quote(column) for column in table.identity)
        seeds = []
        for key in self.connection.execute(f'SELECT {projection} FROM {quote(root_name)} WHERE ({where}) ORDER BY {projection}'):
            if self.add(root_name, key):
                seeds.append((root_name, key))
        if not seeds:
            raise SliceError('The root condition matched no rows.')
        if include_children:
            queue = deque(seeds)
            while queue:
                name, key = queue.popleft()
                for fk in self.children[name]:
                    for child_key in self.related(fk, key, False):
                        if self.add(fk.child, child_key):
                            queue.append((fk.child, child_key))
        queue = deque((name, key) for name, keys in self.selected.items() for key in keys)
        while queue:
            name, key = queue.popleft()
            for fk in self.parents[name]:
                for parent_key in self.related(fk, key, True):
                    if self.add(fk.parent, parent_key):
                        queue.append((fk.parent, parent_key))
        return root_name, len(seeds)

    def write(self, connection: sqlite3.Connection) -> None:
        connection.execute('BEGIN')
        for table in self.tables.values():
            self.check_time()
            connection.execute(table.sql)
        for name, keys in self.selected.items():
            table = self.tables[name]
            fields = ((table.rowid_alias,) if table.rowid_alias else ()) + table.columns
            columns = ','.join(quote(column) for column in fields)
            where = ' AND '.join(quote(column) + ' IS ?' for column in table.identity)
            insert = f'INSERT INTO {quote(name)} ({columns}) VALUES ({",".join("?" for _ in fields)})'
            for key in keys:
                self.check_time()
                row = self.connection.execute(f'SELECT {columns} FROM {quote(name)} WHERE {where}', key).fetchone()
                if row is None:
                    raise SliceError('A selected row disappeared from the source snapshot.')
                connection.execute(insert, row)
        if self.connection.execute("SELECT 1 FROM sqlite_schema WHERE name='sqlite_sequence'").fetchone():
            connection.execute('DELETE FROM sqlite_sequence')
            connection.executemany('INSERT INTO sqlite_sequence(name,seq) VALUES(?,?)',
                                   self.connection.execute('SELECT name,seq FROM sqlite_sequence'))
        for kind in ['index', 'view', 'trigger']:
            objects = self.connection.execute('SELECT sql FROM sqlite_schema WHERE type=? AND sql IS NOT NULL ORDER BY name', (kind,))
            for (sql,) in objects:
                connection.execute(sql)
        for pragma in ['user_version', 'application_id']:
            value = int(self.connection.execute('PRAGMA ' + pragma).fetchone()[0])
            connection.execute(f'PRAGMA {pragma}={value}')
        violations = connection.execute('PRAGMA foreign_key_check').fetchall()
        if violations:
            raise SliceError(f'The selected rows leave {len(violations)} foreign-key violations.')
        if connection.execute('PRAGMA integrity_check').fetchall() != [('ok',)]:
            raise SliceError('The output did not pass SQLite integrity_check.')
        connection.commit()


def extract(source: Path, output: Path, root: str, where: str, *, children: bool = True,
            max_rows: int = 10000, timeout: float = 30) -> dict:
    source, output = Path(source).resolve(), Path(output).absolute()
    if not source.is_file():
        raise SliceError('The source must be an existing SQLite file.')
    if os.path.lexists(output):
        raise SliceError('The output already exists; choose an unused path.')
    if type(max_rows) is not int or max_rows < 1 or isinstance(timeout, bool) or not isinstance(timeout, (int, float)) or not math.isfinite(timeout) or timeout <= 0:
        raise SliceError('Row limit and timeout must be positive.')
    if not output.parent.is_dir():
        raise SliceError('The output directory must already exist.')
    started = time.monotonic()
    temporary = None
    connection = None
    try:
        connection = sqlite3.connect(source.as_uri() + '?mode=ro', uri=True, timeout=timeout)
        connection.execute('PRAGMA query_only=ON')
        connection.set_progress_handler(lambda: int(time.monotonic() - started > timeout), 10000)
        connection.execute('BEGIN')
        snapshot = Snapshot(connection, max_rows, started + timeout)
        root_name, seed_count = snapshot.collect(root, where, children)
        descriptor, temporary_name = tempfile.mkstemp(prefix='.' + output.name + '-', suffix='.sqlite3', dir=output.parent)
        os.close(descriptor)
        temporary = Path(temporary_name)
        destination = sqlite3.connect(temporary, timeout=timeout)
        destination.set_progress_handler(lambda: int(time.monotonic() - started > timeout), 10000)
        try:
            snapshot.write(destination)
        finally:
            destination.close()
        # Same-directory hard-link publication refuses a destination created
        # by another process during extraction, without overwriting it.
        os.link(temporary, output)
        return {'format': 'sqlite-sprig/1', 'version': __version__, 'status': 'created', 'output': str(output), 'root': root_name,
                'seedRows': seed_count, 'includeChildren': children,
                'rows': {name: len(keys) for name, keys in snapshot.selected.items()},
                'totalRows': snapshot.row_count, 'bytes': output.stat().st_size,
                'schema': 'ordinary tables, indexes, views, triggers and SQLite defaults retained',
                'sourceReadOnly': True, 'masked': False,
                'processSeconds': time.monotonic() - started}
    finally:
        if connection is not None:
            connection.close()
        if temporary is not None:
            temporary.unlink(missing_ok=True)


class JsonArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        print(json.dumps({'format': 'sqlite-sprig/1', 'status': 'error', 'message': message}))
        raise SystemExit(2)


def main() -> int:
    parser = JsonArgumentParser(description='Extract a SQLite branch with its ordinary schema and required parents.')
    parser.add_argument('--version', action='version', version=__version__)
    parser.add_argument('source', type=Path)
    parser.add_argument('--root', required=True)
    parser.add_argument('--where', required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--parents-only', action='store_true')
    parser.add_argument('--max-rows', type=int, default=10000)
    parser.add_argument('--timeout', type=float, default=30)
    args = parser.parse_args()
    try:
        result = extract(args.source, args.out, args.root, args.where, children=not args.parents_only,
                         max_rows=args.max_rows, timeout=args.timeout)
    except (SliceError, sqlite3.Error, OSError) as error:
        print(json.dumps({'format': 'sqlite-sprig/1', 'status': 'error', 'message': str(error)}))
        return 2
    print(json.dumps(result))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
