from contextlib import closing
import hashlib
import json
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import unittest


class CliTests(unittest.TestCase):
    def invoke(self, *args):
        return subprocess.run([sys.executable, '-m', 'sqlite_sprig', *map(str, args)],
                              text=True, encoding='utf-8', capture_output=True, timeout=15)

    def test_json_output_and_failed_second_write(self):
        with tempfile.TemporaryDirectory(prefix='sprig-cli-') as directory:
            resolved = Path(directory).resolve()
            self.assertEqual(resolved.parent, Path(tempfile.gettempdir()).resolve())
            self.assertTrue(resolved.name.startswith('sprig-cli-'))
            source, output = Path(directory) / 'in.db', Path(directory) / 'out.db'
            with closing(sqlite3.connect(source)) as connection:
                connection.executescript('CREATE TABLE t(id INTEGER PRIMARY KEY); INSERT INTO t VALUES(1);')
            args = (source, '--root', 't', '--where', 'id=1', '--out', output)
            first = self.invoke(*args)
            self.assertEqual(first.returncode, 0, first.stderr)
            payload = json.loads(first.stdout)
            self.assertEqual(payload['format'], 'sqlite-sprig/1')
            self.assertEqual(payload['totalRows'], 1)
            before = hashlib.sha256(output.read_bytes()).hexdigest()
            second = self.invoke(*args)
            self.assertEqual(second.returncode, 2)
            self.assertEqual(json.loads(second.stdout)['status'], 'error')
            self.assertEqual(hashlib.sha256(output.read_bytes()).hexdigest(), before)

    def test_invalid_arguments_are_machine_readable(self):
        for args in [(), ('--unknown',), ('in.db', '--root', 't', '--where', '1', '--out', 'out.db', '--max-rows', 'no')]:
            with self.subTest(args=args):
                result = self.invoke(*args)
                self.assertEqual(result.returncode, 2)
                self.assertEqual(json.loads(result.stdout)['format'], 'sqlite-sprig/1')
                self.assertEqual(json.loads(result.stdout)['status'], 'error')


if __name__ == '__main__':
    unittest.main()
