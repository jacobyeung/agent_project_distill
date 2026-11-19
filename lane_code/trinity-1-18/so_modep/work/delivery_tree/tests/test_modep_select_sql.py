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
    def database(self, view=False, count=1100, frames=None):
        root = Path(tempfile.mkdtemp(prefix='modep_sql_', dir=os.environ['TMPDIR']))
        p = root/'rows.sqlite'
        with sqlite3.connect(p) as db:
            db.execute('CREATE TABLE payloads(i INTEGER PRIMARY KEY,row TEXT,target TEXT)')
            db.executemany('INSERT INTO payloads VALUES(?,?,?)',
                          ((i,json.dumps(dict(qid=i,ground_record={'x':i},routing={},
                              student_input={'frames': [frames[i//5]]} if frames else {})), '{}') for i in range(count)))
            if view:
                db.execute("CREATE VIEW rows AS SELECT i,json_set(row,'$.routing.ground_record',json_extract(row,'$.ground_record')) AS row,target FROM payloads")
            else:db.execute('ALTER TABLE payloads RENAME TO rows')
        return p

    def test_sparse_dense_unsorted_and_empty(self):
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

    def test_multichunk_sparse_events_and_order_sensitive_output(self):
        import student_pilot.s1_exclusions as native

        class OrderedRule(Rule):
            def __init__(self):
                super().__init__()
                self.previous = -1

            def keep(self, row, source):
                super().keep(row, source)
                keep = row['qid'] > self.previous
                self.previous = row['qid']
                return keep

        indices = list(range(0, 4096, 5))[::-1]  # 820 keys, four chunks, density < 1/4.
        self.assertLess(len(indices)*4, max(indices)+1)
        connect = sqlite3.connect
        for view in (False, True):
            path = self.database(view, count=4096)
            pin = file_pin(path)
            outputs = []
            for flag in ('0', '1'):
                queries = []
                def traced(*args, **kwargs):
                    db = connect(*args, **kwargs)
                    db.set_trace_callback(queries.append)
                    return db
                rule = OrderedRule()
                with patch.dict(os.environ, S1_PREP_SELECT_SQL=flag), patch.object(
                        native.sqlite3, 'connect', traced), patch.object(
                        native, '_selected_rows', wraps=native._selected_rows) as spy:
                    result = _database(pin, indices, rule, 'source')
                outputs.append((result, rule.events))
                self.assertEqual(spy.call_count, 2 if flag == '1' else 0)
                self.assertEqual(len(queries), 8 if flag == '1' else 2)
                self.assertTrue(all(q.endswith('ORDER BY i') for q in queries))
                if flag == '1':
                    self.assertTrue(all('WHERE i IN (' in q for q in queries))
                    self.assertTrue(all(len(q.partition('IN (')[2].partition(')')[0].split(',')) <= 256
                                        for q in queries))
            self.assertEqual(outputs[0], outputs[1])  # Every expect/keep payload in order.
            self.assertEqual(outputs[0][0], indices)  # Output itself depends on visitation order.
            with connect(path.as_uri()+'?mode=ro', uri=True) as db:
                expected = [row for row in db.execute('SELECT i,row FROM rows ORDER BY i')
                            if row[0] in set(indices)]
                self.assertEqual(list(native._selected_rows(db, set(indices))), expected)
            self.assertEqual(file_pin(path), pin)

    def test_multichunk_frame_inventory_bytes_are_order_sensitive(self):
        from student_pilot.s1_admission import FrameAudit
        root = Path(tempfile.mkdtemp(prefix='modep_order_', dir=os.environ['TMPDIR']))
        frame_root = root/'frames'
        frame_root.mkdir()
        frames = []
        for i in range(820):
            path = frame_root/str(i)
            path.write_bytes(str(i).encode())
            frames.append(file_pin(path))
        indices = list(range(0, 4096, 5))[::-1]
        for view in (False, True):
            database = self.database(view, count=4096, frames=frames)
            results = []
            for flag in ('0', '1'):
                output = root/(str(view)+flag)
                output.mkdir()
                audit = FrameAudit(output, [frame_root], sample_size=8)
                try:
                    with patch.dict(os.environ, S1_PREP_SELECT_SQL=flag):
                        self.assertEqual(_database(file_pin(database), indices, audit, 'source'), indices)
                    report = audit.finish()
                finally:
                    audit.close()
                self.assertEqual(report['sources']['source']['unique_frames'], 820)
                results.append((output/'frame_inventory.sqlite').read_bytes())
            self.assertEqual(results[0], results[1])

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
            expected = list(db.execute('SELECT i,row FROM rows ORDER BY i'))
            queries.clear()
            self.assertEqual(list(_selected_rows(db,set(range(1100)))), expected)
        self.assertEqual(len(queries),5)
        self.assertTrue(all(q.startswith('SELECT i,row FROM rows WHERE i IN (') for q in queries))
        self.assertTrue(all(q.count(',')<=256 for q in queries))


if __name__ == '__main__':unittest.main()
