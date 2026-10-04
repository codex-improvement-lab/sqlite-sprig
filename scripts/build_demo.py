"""Build the authored example, actual subsets and public display data."""
from contextlib import closing
import hashlib
import json
from pathlib import Path
import sqlite3
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from sqlite_sprig import extract

TABLES = ['spaces', 'boards', 'users', 'cards', 'comments', 'card_labels', 'labels']


def rows(connection):
    result = {}
    for table in TABLES:
        cursor = connection.execute(f'SELECT * FROM "{table}"')
        names = [column[0] for column in cursor.description]
        result[table] = [dict(zip(names, row)) for row in cursor]
    return result


def build():
    target = ROOT / 'docs/data'
    target.mkdir(parents=True, exist_ok=True)
    assert target.resolve().is_relative_to(ROOT.resolve())
    with tempfile.TemporaryDirectory(prefix='sprig-demo-') as directory:
        scratch = Path(directory).resolve()
        assert scratch.parent == Path(tempfile.gettempdir()).resolve() and scratch.name.startswith('sprig-demo-')
        source = scratch / 'board.sqlite3'
        with closing(sqlite3.connect(source)) as connection:
            connection.executescript((ROOT / 'examples/board.sql').read_text(encoding='utf-8'))
            source_rows = rows(connection)
        source_hash = hashlib.sha256(source.read_bytes()).hexdigest()
        data = {'authoredExample': True, 'source': source_rows, 'sourceRows': sum(map(len, source_rows.values())), 'cases': {}}
        for card_id, expected_count in [(103, 11), (101, 9), (102, 8)]:
            output = scratch / f'card-{card_id}.sqlite3'
            summary = extract(source, output, 'cards', f'id={card_id}')
            assert summary['totalRows'] == expected_count
            with closing(sqlite3.connect(output)) as result:
                case_rows = rows(result)
                assert result.execute('SELECT status,comment_count FROM cards').fetchall() == [('open', 2)]
                assert result.execute('PRAGMA foreign_key_check').fetchall() == []
            data['cases'][str(card_id)] = {
                'totalRows': summary['totalRows'], 'rows': case_rows,
                'filename': output.name, 'sha256': hashlib.sha256(output.read_bytes()).hexdigest(),
            }
            (target / output.name).write_bytes(output.read_bytes())
        assert hashlib.sha256(source.read_bytes()).hexdigest() == source_hash
        (target / source.name).write_bytes(source.read_bytes())
        data['sourceSha256'] = source_hash
        data['sourceFilename'] = source.name
        encoded = json.dumps(data, indent=2, ensure_ascii=True)
        (target / 'demo.json').write_text(encoded + '\n', encoding='utf-8')
        (target / 'demo-data.js').write_text('window.SPRIG_DEMO = ' + encoded + ';\n', encoding='utf-8')
    print(json.dumps({'sourceRows': data['sourceRows'], 'retainedRows': {key: value['totalRows'] for key, value in data['cases'].items()}}))


if __name__ == '__main__':
    build()
