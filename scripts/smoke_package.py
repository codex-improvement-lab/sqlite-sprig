"""Install a built wheel in a fresh environment and exercise its real CLI."""
from contextlib import closing
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import venv

ROOT = Path(__file__).resolve().parents[1]


def main():
    wheel = Path(sys.argv[1]).resolve()
    assert wheel.is_file()
    env = os.environ.copy()
    env.pop('PYTHONPATH', None)
    with tempfile.TemporaryDirectory(prefix='sprig-package-') as directory:
        work = Path(directory).resolve()
        assert work.parent == Path(tempfile.gettempdir()).resolve() and work.name.startswith('sprig-package-')
        venv.EnvBuilder(with_pip=True).create(work / 'venv')
        python = work / 'venv' / ('Scripts/python.exe' if os.name == 'nt' else 'bin/python')
        cli = work / 'venv' / ('Scripts/sqlite-sprig.exe' if os.name == 'nt' else 'bin/sqlite-sprig')
        subprocess.run([str(python), '-m', 'pip', 'install', '--no-deps', '--no-index', str(wheel)], cwd=work, env=env, check=True)
        source, output = work / 'board.sqlite3', work / 'card.sqlite3'
        with closing(sqlite3.connect(source)) as connection:
            connection.executescript((ROOT / 'examples/board.sql').read_text(encoding='utf-8'))
        source_hash = hashlib.sha256(source.read_bytes()).hexdigest()
        command = [str(cli), str(source), '--root', 'cards', '--where', 'id=103', '--out', str(output)]
        result = subprocess.run(command, cwd=work, env=env, capture_output=True, text=True, check=True)
        payload = json.loads(result.stdout)
        assert payload['totalRows'] == 11 and payload['format'] == 'sqlite-sprig/1'
        with closing(sqlite3.connect(output)) as connection:
            assert connection.execute('PRAGMA foreign_key_check').fetchall() == []
            assert connection.execute('SELECT id,status,comment_count,actual_comments FROM card_summary').fetchall() == [(103, 'open', 2, 2)]
            with closing(sqlite3.connect(':memory:')) as probe:
                connection.backup(probe)
                probe.execute("INSERT INTO cards(id,board_id,creator_id,title) VALUES(104,10,1,'probe')")
                assert probe.execute('SELECT status,comment_count FROM cards WHERE id=104').fetchone() == ('open', 0)
                probe.execute("INSERT INTO comments(id,card_id,author_id,body) VALUES(900,103,2,'probe')")
                assert probe.execute('SELECT status,comment_count FROM cards WHERE id=103').fetchone() == ('review', 3)
                probe.rollback()
        output_hash = hashlib.sha256(output.read_bytes()).hexdigest()
        repeat = subprocess.run(command, cwd=work, env=env, capture_output=True, text=True)
        assert repeat.returncode == 2 and json.loads(repeat.stdout)['status'] == 'error'
        assert hashlib.sha256(output.read_bytes()).hexdigest() == output_hash
        assert hashlib.sha256(source.read_bytes()).hexdigest() == source_hash
        location = subprocess.check_output([str(python), '-c', 'import sqlite_sprig;print(sqlite_sprig.__file__)'], cwd=work, env=env, text=True).strip()
        assert Path(location).resolve().is_relative_to(work / 'venv')
        module = subprocess.run([str(python), '-m', 'sqlite_sprig', '--version'], cwd=work, env=env, capture_output=True, text=True, check=True)
        assert module.stdout.strip() == '0.1.0a1'
    print(json.dumps({'cleanWheel': True, 'consoleScript': True, 'module': True, 'rows': 11, 'sourceUnchanged': True, 'schemaBehavior': True, 'noOverwrite': True}))


if __name__ == '__main__':
    main()
