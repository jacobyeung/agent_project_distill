"""Ordered selection parity on real tables and the native composed-store view."""
import json
import os
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch
from student_pilot.p3_provenance import file_pin
from student_pilot.s1_exclusions import _database


class Rule:
    def __init__(self):self.events=[]
    def counts(self, source):self.events.append(('counts', source))
    def expect(self, source, rows, population):self.events.append(('expect', source, list(rows), population))
    def keep(self, row, source):self.events.append(('keep', source, row));return row['qid']%3 != 0


class SelectSQL(unittest.TestCase):
    def database(self, view=False):
        root = Path(tempfile.mkdtemp(prefix='modep_sql_', dir=os.environ['TMPDIR']))
        p = root/'rows.sqlite'
        with sqlite3.connect(p) as db:
            db.execute('CREATE TABLE payloads(i INTEGER PRIMARY KEY,row TEXT,target TEXT)')
            db.executemany('INSERT INTO payloads VALUES(?,?,?)',
                          ((i,json.dumps(dict(qid=i,ground_record={'x':i},routing={})), '{}') for i in range(1100)))
            if view:
                db.execute("CREATE VIEW rows AS SELECT i,json_set(row,'$.routing.ground_record',json_extract(row,'$.ground_record')) AS row,target FROM payloads")
            else:db.execute('ALTER TABLE payloads RENAME TO rows')
        return p

    def test_sparse_dense_unsorted_empty_and_chunk_boundaries(self):
        for view in (False, True):
            path = self.database(view)
            pin = file_pin(path)
            for indices in ([], [1099,1,400,2], list(range(1100)), list(range(1099,-1,-2))):
                outputs=[]
                for flag in ('0','1'):
                    rule=Rule()
                    with patch.dict(os.environ, S1_PREP_SELECT_SQL=flag):
                        result=_database(pin,indices,rule,'source')
                    outputs.append((result,rule.events))
                self.assertEqual(outputs[0],outputs[1])
                self.assertEqual(file_pin(path),pin)

    def test_missing_invalid_and_changed_inputs_refuse(self):
        path=self.database();pin=file_pin(path)
        for flag in ('0','1'):
            with patch.dict(os.environ,S1_PREP_SELECT_SQL=flag):
                for indices in ([0,1101],[1<<70],[1,1],[-1],[True]):
                    with self.assertRaises(ValueError):_database(pin,indices,Rule(),'source')
        path.write_bytes(path.read_bytes()+b'changed')
        for flag in ('0','1'):
            with patch.dict(os.environ,S1_PREP_SELECT_SQL=flag),self.assertRaises(ValueError):
                _database(pin,[0],Rule(),'source')

    def test_dense_prefix_uses_native_scan_and_sparse_selection_uses_keyed_reads(self):
        import student_pilot.s1_exclusions as native
        path = self.database(True)
        with patch.dict(os.environ, S1_PREP_SELECT_SQL='1'):
            with patch.object(native, '_selected_rows', side_effect=AssertionError('dense keyed read')):
                _database(file_pin(path), list(range(1100)), Rule(), 'dense')
            with patch.object(native, '_selected_rows', wraps=native._selected_rows) as selected:
                _database(file_pin(path), [1099, 2, 800], Rule(), 'sparse')
                self.assertEqual(selected.call_count, 2)

    def test_no_sql_mutations_and_bounded_bindings(self):
        from student_pilot.s1_exclusions import _selected_rows
        path=self.database(True)
        with sqlite3.connect(path.as_uri()+'?mode=ro',uri=True) as db:
            queries=[];db.set_trace_callback(queries.append)
            self.assertEqual(len(list(_selected_rows(db,set(range(1100))))),1100)
        self.assertEqual(len(queries),5)
        self.assertTrue(all(q.startswith('SELECT i,row FROM rows WHERE i IN (') for q in queries))
        self.assertTrue(all(q.count(',')<=256 for q in queries))


if __name__ == '__main__':unittest.main()
