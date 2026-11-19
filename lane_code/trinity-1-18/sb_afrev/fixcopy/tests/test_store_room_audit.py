"""Run CLI regression tests with real pinned lists and explicitly synthetic rows."""
import hashlib
import json
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import store_room_audit as audit

RUN = Path(tempfile.mkdtemp(prefix='regression-', dir=ROOT/'out'))
INPUTS = {}


def pin(path):
    path = path.resolve()
    INPUTS[str(path)] = {'sha256': audit.sha256(path), 'bytes': path.stat().st_size}


def write_fixture(path, rows):
    path.write_text(json.dumps({'schema': 'synthetic-audit-test-rows-v1', 'inputs': dict(INPUTS), 'rows': rows}, indent=2)+'\n')
    pin(path)
    return path


class AuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ledger = audit.Inputs()
        cls.rooms, cls.mint, cls.sets, _, cls.aliases, _ = audit.prepare(ROOT/'inputs/tree_r1', ROOT/'inputs/lists', cls.ledger)
        cls.mint = staticmethod(cls.mint)
        INPUTS.update(cls.ledger.pins)
        pin(Path(__file__))
        pin(ROOT/'store_room_audit.py')
        bench = json.loads((ROOT/'inputs/lists/3119aa4a.raw').read_text())
        cls.bench_scene = next(s for s in bench['physical_groups'] if s.startswith('scannetppv2/'))
        dev = json.loads((ROOT/'inputs/lists/969cdb56.raw').read_text())
        cls.dev_scene = next(s for s in dev['physical_groups'] if s.startswith('scannetppv2/'))
        k1 = json.loads((ROOT/'inputs/lists/4d4736cf.raw').read_text())
        cls.k1_scene = next(c['canonical'] for c in k1['captures'] if c['k1_split'] == 'heldout' and c['canonical'].startswith('arkitscenes/'))
        r0 = next(s for s in (ROOT/'inputs/lists/bdb5d402.raw').read_text().split() if s.startswith('scannet/'))
        withheld = json.loads((ROOT/'inputs/lists/634820b4.raw').read_text())
        withheld_scene = next(s for s in withheld['rooms'] if s.startswith('scannet/'))
        venue = next(s for s in bench['physical_groups'] if s.startswith('arkitscenes/venue'))
        video = next(v for v, visit in cls.rooms.visits.items() if 'arkitscenes/venue'+visit == venue)
        cases = [('bench-v2', cls.bench_scene, 'BENCH v2'),
                 ('bench-native', cls.bench_scene.replace('scannetppv2/', 'scannetpp/'), 'BENCH v2'),
                 ('r0-rescan', r0+'_99', 'R0'),
                 ('withheld-rescan', withheld_scene+'_99', 'withheld-80'),
                 ('dev-v2', cls.dev_scene, 'dev-S1'), ('k1-visit', cls.k1_scene, 'K1'),
                 ('bench-visit', 'arkitscenes/'+video, 'BENCH v2')]
        cls.rows = [dict(qid=qid, dataset=scene.split('/')[0], scene=scene.split('/')[1],
                         pool='synthetic-'+str(i%2), question_type='family-'+str(i%3))
                    for i, (qid, scene, _) in enumerate(cases)]
        cls.required = {qid: name for qid, _, name in cases}
        cls.synthetic = write_fixture(RUN/'synthetic.json', cls.rows)
        cls.unknown_row = dict(qid='unknown', dataset='scannetpp', scene='v000000000000', pool='synthetic', question_type='unknown')
        assert 'd2/v000000000000' not in cls.aliases

    def invoke(self, label, store=None, extra=(), tree=None, lists=None):
        output = RUN/label
        cmd = [sys.executable, '-s', str(ROOT/'store_room_audit.py'), '--store', str(store or self.synthetic),
               '--tree', str(tree or ROOT/'inputs/tree_r1'), '--lists', str(lists or ROOT/'inputs/lists'),
               '--out', str(output), *extra]
        result = subprocess.run(cmd, capture_output=True, text=True)
        report = json.loads((output/'audit.json').read_text())
        pin(output/'audit.json')
        return result, report, output

    def test_synthetic_list_hits_and_persisted_rows(self):
        result, report, output = self.invoke('synthetic')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(report['unresolved_rows'], 0)
        self.assertEqual(report['rows'], 7)
        self.assertTrue(all(report['hits'][name] >= 1 for name in audit.NAMES))
        with sqlite3.connect(output/'rows.sqlite') as conn:
            rows = conn.execute('SELECT row_id,scene,room,hits FROM rows').fetchall()
        self.assertEqual(len(rows), 7)
        for qid, scene, room, hits in rows:
            self.assertTrue(scene and room)
            self.assertIn(self.required[qid], json.loads(hits))
        by_id = {row[0]: row for row in rows}
        self.assertEqual(by_id['bench-v2'][1:3], by_id['bench-native'][1:3])
        for name, count in report['hits'].items():
            self.assertEqual(count, sum(report['hits_by_tier'][name].values()))
            self.assertEqual(count, sum(report['hits_by_stream'][name].values()))
            self.assertEqual(count, sum(report['hits_by_family'][name].values()))
            self.assertEqual(count, sum(x['rows'] for x in report['hits_by_list_tier_stream_family'] if x['list'] == name))
        self.assertEqual(audit.sha256(output/'rows.sqlite'), report['row_records']['sha256'])

    def test_unknown_refuses_and_counts_distinct_tokens(self):
        store = write_fixture(RUN/'unknown.json', [self.unknown_row, dict(self.unknown_row, qid='unknown-2')])
        result, report, output = self.invoke('unknown', store)
        self.assertEqual(result.returncode, 2)
        self.assertEqual(report['status'], 'REFUSED')
        self.assertFalse(report['complete'])
        self.assertEqual(report['unresolved_token_count'], 1)
        self.assertEqual(report['unresolved_rows'], 2)
        self.assertIn('unresolved tokens=1, rows=2', result.stdout)
        with sqlite3.connect(output/'rows.sqlite') as conn:
            self.assertEqual(conn.execute('SELECT count(*) FROM rows WHERE scene IS NULL AND room IS NULL').fetchone()[0], 2)

    def test_allow_unresolved_stays_incomplete(self):
        store = write_fixture(RUN/'allow.json', [self.unknown_row, self.rows[0]])
        result, report, _ = self.invoke('allow', store, ['--allow-unresolved'])
        self.assertEqual(result.returncode, 0)
        self.assertEqual(report['status'], 'INCOMPLETE')
        self.assertFalse(report['complete'])
        self.assertTrue(report['counts_are_lower_bounds'])
        self.assertEqual(report['hits']['BENCH v2'], 1)

    def test_conflicting_witness_refuses(self):
        token = self.mint(self.bench_scene)
        row = dict(qid='conflict', dataset='d2', scene=token.split('/')[1],
                   canonical=self.dev_scene.replace('scannetppv2/', 'scannetpp/'))
        store = write_fixture(RUN/'conflict.json', [row])
        result, report, _ = self.invoke('conflict', store)
        self.assertEqual(result.returncode, 2)
        self.assertEqual(report['unresolved_rows'], 1)

    def test_current_tree_is_executed_and_hashed(self):
        tree = RUN/'alternate_tree'
        (tree/'student_pilot').mkdir(parents=True)
        for name in ('r1_rooms.py','p3_provenance.py','r1_persisted.py','carrier_c1_routing.py'):
            data = (ROOT/'inputs/tree_r1/student_pilot'/name).read_bytes()
            if name == 'r1_rooms.py':
                self.assertIn(b"return 'scannetpp/'+capture", data)
                data = data.replace(b"return 'scannetpp/'+capture", b"return 'scannetpp/'+capture+'-selected-tree'")
            (tree/'student_pilot'/name).write_bytes(data)
        result, report, output = self.invoke('alternate_tree_output', tree=tree)
        self.assertEqual(result.returncode, 0, result.stderr)
        path = tree/'student_pilot/r1_rooms.py'
        self.assertEqual(report['inputs'][str(path)]['sha256'], audit.sha256(path))
        with sqlite3.connect(output/'rows.sqlite') as conn:
            room = conn.execute("SELECT room FROM rows WHERE row_id='bench-v2'").fetchone()[0]
        self.assertTrue(room.endswith('-selected-tree'))

    def test_missing_input_reports_exact_path(self):
        missing = RUN/'absent_tree'
        result, report, _ = self.invoke('missing', tree=missing)
        self.assertEqual(result.returncode, 1)
        self.assertEqual(report['status'], 'MISSING')
        self.assertIn(str(missing/'student_pilot/p3_provenance.py'), report['error'])

    def test_changed_list_hash_refuses(self):
        directory = RUN/'bad_lists'
        directory.mkdir()
        manifest = json.loads((ROOT/'inputs/lists/manifest.json').read_text())
        for pin_value in list(manifest['authority'].values())+list(manifest['lists'].values())+[manifest['alias_map']]:
            pin_value['path'] = str(ROOT/'inputs/lists'/pin_value['path'])
        manifest['lists']['BENCH v2']['sha256'] = '0'*64
        manifest['inputs'] = dict(INPUTS)
        (directory/'manifest.json').write_text(json.dumps(manifest)+'\n')
        result, report, _ = self.invoke('changed_list', lists=directory)
        self.assertEqual(result.returncode, 1)
        self.assertIn('SHA256 mismatch', report['error'])

    def test_output_directory_cannot_reuse_stale_success(self):
        result, _, output = self.invoke('no_overwrite')
        self.assertEqual(result.returncode, 0)
        digest = audit.sha256(output/'audit.json')
        second = subprocess.run(result.args, capture_output=True, text=True)
        self.assertEqual(second.returncode, 2)
        self.assertIn('--out must be empty', second.stderr)
        self.assertEqual(digest, audit.sha256(output/'audit.json'))


if __name__ == '__main__':
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(AuditTests)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    summary = {'schema': 'auditfix-test-results-v1', 'command': ' '.join([sys.executable, '-s', str(Path(__file__).resolve())]),
               'inputs': INPUTS, 'status': 'PASS' if result.wasSuccessful() else 'FAIL',
               'tests_run': result.testsRun, 'failures': len(result.failures), 'errors': len(result.errors),
               'outputs': str(RUN)}
    (RUN/'TEST_RESULTS.json').write_text(json.dumps(summary, indent=2, sort_keys=True)+'\n')
    print('Test outputs:', RUN)
    sys.exit(0 if result.wasSuccessful() else 1)
