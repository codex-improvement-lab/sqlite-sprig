import hashlib
from contextlib import closing
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

import sqlite_sprig


class SliceTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(prefix='sqlite_sprig-unit-')
        self.root = Path(self.directory.name)
        self.source = self.root / 'input.sqlite3'
        self.output = self.root / 'result.sqlite3'

    def tearDown(self):
        resolved = self.root.resolve()
        self.assertEqual(resolved.parent, Path(tempfile.gettempdir()).resolve())
        self.assertTrue(resolved.name.startswith("sqlite_sprig-unit-"))
        self.directory.cleanup()

    def make(self, script):
        with closing(sqlite3.connect(self.source)) as connection:
            connection.executescript(script)
        self.source_hash = hashlib.sha256(self.source.read_bytes()).hexdigest()

    def check_source(self):
        self.assertEqual(hashlib.sha256(self.source.read_bytes()).hexdigest(), self.source_hash)

    def run_slice(self, root, where='id=1', **kwargs):
        result = sqlite_sprig.extract(self.source, self.output, root, where, **kwargs)
        self.check_source()
        with closing(sqlite3.connect(self.output)) as connection:
            self.assertEqual(connection.execute('PRAGMA foreign_key_check').fetchall(), [])
        return result

    def test_branch_scope_and_application_behavior(self):
        self.make('''
        CREATE TABLE customers(id INTEGER PRIMARY KEY);
        CREATE TABLE orders(id INTEGER PRIMARY KEY, customer INTEGER REFERENCES customers, status TEXT NOT NULL DEFAULT 'ready');
        CREATE TABLE products(id INTEGER PRIMARY KEY, stock INTEGER NOT NULL);
        CREATE TABLE items(id INTEGER PRIMARY KEY, ord INTEGER REFERENCES orders, product INTEGER REFERENCES products, qty INTEGER);
        INSERT INTO customers VALUES(1),(2);
        INSERT INTO orders(id,customer) VALUES(1,1),(2,1),(3,2);
        INSERT INTO products VALUES(1,2),(2,9);
        INSERT INTO items VALUES(1,1,1,7),(2,2,1,1),(3,3,2,1);
        CREATE INDEX orders_status ON orders(status);
        CREATE VIEW shortages AS SELECT items.id,qty-stock AS shortfall FROM items JOIN products ON product=products.id WHERE qty>stock;
        CREATE TRIGGER changed AFTER INSERT ON items BEGIN UPDATE orders SET status='changed' WHERE id=NEW.ord; END;
        ''')
        result = self.run_slice('orders')
        self.assertEqual(result['totalRows'], 4)
        with closing(sqlite3.connect(self.output)) as connection:
            self.assertEqual(connection.execute('SELECT id FROM orders').fetchall(), [(1,)])
            self.assertEqual(connection.execute('SELECT * FROM shortages').fetchall(), [(1, 5)])
            connection.execute('INSERT INTO orders(id,customer) VALUES(4,1)')
            self.assertEqual(connection.execute('SELECT status FROM orders WHERE id=4').fetchone(), ('ready',))
            connection.execute('INSERT INTO items VALUES(4,1,1,1)')
            self.assertEqual(connection.execute('SELECT status FROM orders WHERE id=1').fetchone(), ('changed',))
            self.assertIsNotNone(connection.execute("SELECT name FROM sqlite_schema WHERE name='orders_status'").fetchone())

    def test_parent_cycles_terminate_without_adding_sibling_children(self):
        self.make('''
        CREATE TABLE people(id INTEGER PRIMARY KEY, manager INTEGER REFERENCES people);
        CREATE TABLE tickets(id INTEGER PRIMARY KEY, owner INTEGER REFERENCES people);
        INSERT INTO people VALUES(1,2),(2,1),(3,2),(4,NULL);
        INSERT INTO tickets VALUES(1,1),(2,4);
        ''')
        result = self.run_slice('tickets')
        self.assertEqual(result['rows']['people'], 2)
        self.assertEqual(result['rows']['tickets'], 1)

    def test_composite_implicit_parent_key_and_parent_collation(self):
        self.make('''
        CREATE TABLE parent(tenant TEXT COLLATE NOCASE, code INTEGER, PRIMARY KEY(tenant,code)) WITHOUT ROWID;
        CREATE TABLE child(id INTEGER PRIMARY KEY, tenant TEXT, code INTEGER, FOREIGN KEY(tenant,code) REFERENCES parent);
        INSERT INTO parent VALUES('ACME',7),('OTHER',8);
        INSERT INTO child VALUES(1,'acme',7),(2,'other',8);
        ''')
        result = self.run_slice('PARENT', "tenant='acme'")
        self.assertEqual(result['totalRows'], 2)
        with closing(sqlite3.connect(self.output)) as connection:
            self.assertEqual(connection.execute('SELECT * FROM parent').fetchall(), [('ACME', 7)])
            self.assertEqual(connection.execute('SELECT tenant FROM child').fetchall(), [('acme',)])

    def test_foreign_key_to_unique_column_and_partial_null(self):
        self.make('''
        CREATE TABLE lookup(id INTEGER PRIMARY KEY, code TEXT UNIQUE COLLATE NOCASE);
        CREATE TABLE item(id INTEGER PRIMARY KEY, code TEXT REFERENCES lookup(code));
        INSERT INTO lookup VALUES(1,'sku'),(2,'unused');
        INSERT INTO item VALUES(1,'SKU'),(2,NULL);
        ''')
        result = self.run_slice('item', '1')
        self.assertEqual(result['rows']['lookup'], 1)
        self.assertEqual(result['rows']['item'], 2)

    def test_parent_text_affinity_controls_child_and_parent_selection(self):
        self.make('''
        CREATE TABLE parent(code TEXT PRIMARY KEY);
        CREATE TABLE child(id INTEGER PRIMARY KEY, code NUMERIC REFERENCES parent(code));
        INSERT INTO parent VALUES('01'),('1');
        INSERT INTO child VALUES(1,1);
        ''')
        self.assertEqual(self.run_slice('parent', "code='01'")['totalRows'], 1)
        with closing(sqlite3.connect(self.output)) as connection:
            self.assertEqual(connection.execute('SELECT * FROM child').fetchall(), [])
        second = self.root / 'child.sqlite3'
        result = sqlite_sprig.extract(self.source, second, 'child', 'id=1')
        self.assertEqual(result['totalRows'], 2)
        with closing(sqlite3.connect(second)) as connection:
            self.assertEqual(connection.execute('SELECT code FROM parent').fetchall(), [('1',)])
        self.check_source()

    def test_broken_reference_refused_without_published_output(self):
        self.make('''
        CREATE TABLE parent(id INTEGER PRIMARY KEY);
        CREATE TABLE child(id INTEGER PRIMARY KEY, pid INTEGER REFERENCES parent);
        INSERT INTO child VALUES(1,9);
        ''')
        with self.assertRaisesRegex(sqlite_sprig.SliceError, 'foreign-key violations'):
            self.run_slice('child')
        self.assertFalse(self.output.exists())
        self.assertEqual(list(self.root.glob('.result.sqlite3-*')), [])
        self.check_source()

    def test_generated_columns_recompute_after_export(self):
        self.make('''
        CREATE TABLE item(id INTEGER PRIMARY KEY, qty INTEGER DEFAULT 2, price INTEGER, total INTEGER GENERATED ALWAYS AS(qty*price) STORED);
        INSERT INTO item(id,price) VALUES(1,7),(2,11);
        ''')
        self.run_slice('item')
        with closing(sqlite3.connect(self.output)) as connection:
            self.assertEqual(connection.execute('SELECT total FROM item').fetchone(), (14,))
            connection.execute('UPDATE item SET qty=3 WHERE id=1')
            self.assertEqual(connection.execute('SELECT total FROM item').fetchone(), (21,))

    def test_shadowed_rowid_quoted_names_and_blob(self):
        self.make('''
        CREATE TABLE "odd table"(rowid TEXT, payload BLOB);
        INSERT INTO "odd table"(_rowid_,rowid,payload) VALUES(17,'visible rowid',X'00FF');
        INSERT INTO "odd table"(_rowid_,rowid,payload) VALUES(25,'other',X'0203');
        ''')
        self.run_slice('odd table', "hex(payload)='00FF'")
        with closing(sqlite3.connect(self.output)) as connection:
            self.assertEqual(connection.execute('SELECT _rowid_,rowid,payload FROM "odd table"').fetchall(), [(17,'visible rowid',b'\x00\xff')])

    def test_sequences_and_application_pragmas(self):
        self.make('''
        PRAGMA user_version=17;
        PRAGMA application_id=1128877132;
        CREATE TABLE item(id INTEGER PRIMARY KEY AUTOINCREMENT);
        INSERT INTO item VALUES(1),(100);
        DELETE FROM item WHERE id=100;
        ''')
        self.run_slice('item')
        with closing(sqlite3.connect(self.output)) as connection:
            self.assertEqual(connection.execute('PRAGMA user_version').fetchone(), (17,))
            self.assertEqual(connection.execute('PRAGMA application_id').fetchone(), (1128877132,))
            connection.execute('INSERT INTO item DEFAULT VALUES')
            self.assertEqual(connection.execute('SELECT max(id) FROM item').fetchone(), (101,))

    def test_parent_only_mode(self):
        self.make('''CREATE TABLE p(id INTEGER PRIMARY KEY);CREATE TABLE c(id INTEGER PRIMARY KEY,pid INTEGER REFERENCES p);INSERT INTO p VALUES(1);INSERT INTO c VALUES(1,1);''')
        result = self.run_slice('p', children=False)
        self.assertEqual(result['totalRows'], 1)
        self.assertEqual(result['rows']['c'], 0)

    def test_limits_missing_rows_and_existing_output(self):
        self.make('CREATE TABLE item(id INTEGER PRIMARY KEY);INSERT INTO item VALUES(1),(2);')
        for where,options in [('1',{'max_rows':1}),('id=7',{}),('id=1',{'timeout':float('nan')}),('id=1',{'max_rows':True})]:
            with self.assertRaises(sqlite_sprig.SliceError):
                sqlite_sprig.extract(self.source,self.output,'item',where,**options)
            self.assertFalse(self.output.exists())
            self.check_source()
        self.output.write_bytes(b'keep')
        with self.assertRaises(sqlite_sprig.SliceError):self.run_slice('item')
        self.assertEqual(self.output.read_bytes(),b'keep')

    def test_publication_race_does_not_overwrite_other_file(self):
        self.make('CREATE TABLE item(id INTEGER PRIMARY KEY);INSERT INTO item VALUES(1);')
        real_link = sqlite_sprig.os.link
        def race(source,destination):
            Path(destination).write_bytes(b'other process')
            return real_link(source,destination)
        with patch.object(sqlite_sprig.os,'link',side_effect=race),self.assertRaises(FileExistsError):
            self.run_slice('item')
        self.assertEqual(self.output.read_bytes(),b'other process')
        self.assertEqual(list(self.root.glob('.result.sqlite3-*')),[])
        self.check_source()

    def test_query_timeout_leaves_no_output(self):
        self.make('CREATE TABLE item(id INTEGER PRIMARY KEY);INSERT INTO item VALUES(1);')
        where='id=(WITH RECURSIVE n(x) AS (SELECT 1 UNION ALL SELECT x+1 FROM n WHERE x<500000000) SELECT sum(x) FROM n)'
        with self.assertRaises((sqlite3.OperationalError,sqlite_sprig.SliceError)):
            sqlite_sprig.extract(self.source,self.output,'item',where,timeout=0.005)
        self.assertFalse(self.output.exists())
        self.check_source()

    def test_virtual_table_refused(self):
        try:self.make('CREATE VIRTUAL TABLE notes USING fts5(body);')
        except sqlite3.OperationalError:self.skipTest('This SQLite build has no FTS5 module.')
        with self.assertRaisesRegex(sqlite_sprig.SliceError,'Virtual tables'):
            self.run_slice('notes','1')
        self.assertFalse(self.output.exists())


if __name__=='__main__':unittest.main(verbosity=2)
