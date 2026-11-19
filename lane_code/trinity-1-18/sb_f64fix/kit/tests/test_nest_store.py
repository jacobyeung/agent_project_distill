"""nest_store publishes a nested store only when every source row nests, and the published store keeps
the source's indices, targets, row count and anchor order (review sb_f64rev finding 1).
F64_WORK names a scratch directory these tests may write; they never write anywhere else."""
import contextlib
import copy
import json
import os
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

KIT = Path(__file__).resolve().parents[1]
WORK = Path(os.environ['F64_WORK'])
sys.path[:0] = [str(KIT / 'scripts')]

import f64_dryrun  # noqa: E402,F401  (puts the trainer tree on sys.path)
import f64_rows  # noqa: E402
import nest_store  # noqa: E402
from student_pilot.carrier_c1_data import layout_inputs, nested_indices  # noqa: E402
from student_pilot.frame_input import NESTED, anchors, check_row, nest_row  # noqa: E402


def read_store(path):
    with contextlib.closing(sqlite3.connect(f'file:{path}?mode=ro', uri=True)) as connection:
        return [tuple(r) for r in connection.execute('SELECT i, row, target FROM rows ORDER BY i')]


def write_store(path, values):
    with contextlib.closing(sqlite3.connect(path)) as connection:
        with connection:
            connection.execute('CREATE TABLE rows (i INTEGER PRIMARY KEY, row TEXT NOT NULL, target TEXT NOT NULL)')
            connection.executemany('INSERT INTO rows VALUES (?,?,?)', values)
    return path


class NestStore(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.clip = f64_rows.make_clip(WORK, 'a43')
        cls.source = {s: Path(v['database']['path']) for s, v in f64_rows.build(WORK, cls.clip, nested=False).items()}
        cls.nested = {s: Path(v['database']['path']) for s, v in f64_rows.build(WORK, cls.clip, nested=True).items()}
        cls.tmp = Path(tempfile.mkdtemp(prefix='nest_store_', dir=WORK))
        cls.pose = read_store(cls.source['pose'])
        cls.key = nest_store.video_key(json.loads(cls.pose[0][1])['student_input'])
        cls.pins = {cls.key: {str(k): v for k, v in cls.clip['pins'].items()}}

    def fresh(self, name):
        return Path(tempfile.mkdtemp(prefix=name + '_', dir=self.tmp)) / 'nested.sqlite'

    def assert_refused(self, report, out, count):
        self.assertEqual((report['status'], report['published'], report['out']), ('REFUSED', False, None))
        self.assertEqual(report['counts']['refused'], count)
        self.assertFalse(out.exists())
        self.assertFalse(out.with_name(out.name + '.partial').exists())

    def test_reviewer_missing_pins_refuse_the_store(self):
        out = self.fresh('missing_pins')
        report = nest_store.apply(self.source['pose'], {}, out)
        self.assert_refused(report, out, 4)
        self.assertEqual([r['i'] for r in report['refused']], [0, 1, 2, 3])
        self.assertTrue(all('FRAME_INPUT_DENSE_FRAME_MISSING' in r['reason'] for r in report['refused']))

    def test_reviewer_reversed_anchors_refuse_the_store(self):
        rows = [list(r) for r in self.pose]
        row = json.loads(rows[0][1])
        for key in ('frames', 'frame_indices', 'timestamps'):
            row['student_input'][key].reverse()
        layout_inputs(copy.deepcopy(row), 'duplicate', frame_count=32)  # the 32-frame layout gate still admits it
        rows[0][1] = json.dumps(row)
        store = write_store(self.fresh('reversed_source'), rows)
        out = self.fresh('reversed')
        report = nest_store.apply(store, self.pins, out)
        self.assert_refused(report, out, 1)
        self.assertEqual(report['refused'][0]['i'], 0)
        self.assertIn('SOURCE_ANCHORS_NOT_INCREASING', report['refused'][0]['reason'])
        self.assertEqual(nest_store.plan(store)['refused'], [dict(i=0, reason='SOURCE_ANCHORS_NOT_INCREASING')])

    def test_absent_or_stale_frame_refuses_the_store(self):
        indices, _ = nested_indices(self.clip['anchors'], 64)
        ordinal = next(k for k in indices if k not in self.clip['anchors'])
        for name, pin in (('absent', dict(path=str(self.tmp / 'absent.png'), sha256='0' * 64)),
                          ('stale', dict(self.clip['pins'][ordinal], sha256='0' * 64))):
            pins = {self.key: dict(self.pins[self.key], **{str(ordinal): pin})}
            out = self.fresh(name)
            report = nest_store.apply(self.source['vqa'], pins, out)
            self.assert_refused(report, out, 4)
            self.assertTrue(all(f'FRAME_MISSING:{ordinal}:' in r['reason'] for r in report['refused']), report['refused'])

    def test_published_store_keeps_indices_targets_count_and_anchor_order(self):
        single = json.loads(self.pose[0][1])
        si = single['student_input']
        si.update(frames=si['frames'][:1], frame_indices=si['frame_indices'][:1], timestamps=si['timestamps'][:1])
        values = [(i, text, target) for i, (_, text, target) in zip((3, 7, 8, 20), self.pose)]
        values.append((21, json.dumps(single, indent=2), '{"kept": true}'))
        store = write_store(self.fresh('sparse_source'), values)
        out = self.fresh('sparse')
        report = nest_store.apply(store, self.pins, out)
        self.assertEqual(report['status'], 'PUBLISHED')
        self.assertEqual(report['counts'], dict(source=5, nested=4, single_image=1, refused=0))
        self.assertEqual(report['out']['sha256'], nest_store.file_sha256(out))
        published = read_store(out)
        self.assertEqual([(i, target) for i, _, target in published], [(i, target) for i, _, target in values])
        self.assertEqual(published[-1][1], values[-1][1])
        for (_, text, _), (_, new, _) in zip(values[:4], published[:4]):
            source, result = json.loads(text), json.loads(new)
            check_row(result, NESTED)
            self.assertEqual(anchors(result['student_input']), source['student_input']['frame_indices'])
            slots = result['student_input']['anchor_slots']
            self.assertEqual([result['student_input']['frames'][s] for s in slots], source['student_input']['frames'])
            self.assertEqual({k: v for k, v in result.items() if k != 'student_input'},
                             {k: v for k, v in source.items() if k != 'student_input'})
            self.assertEqual(result, nest_row(source, self.clip['pins']))

    def test_every_stream_publishes_the_dry_run_rows(self):
        for stream, source in self.source.items():
            out = self.fresh(stream)
            report = nest_store.apply(source, self.pins, out)
            self.assertEqual((report['status'], report['counts']['source']), ('PUBLISHED', 4), stream)
            self.assertEqual(read_store(out), read_store(self.nested[stream]), stream)

    def test_existing_output_and_empty_store_refuse(self):
        out = self.fresh('exists')
        out.write_text('')
        with self.assertRaisesRegex(ValueError, 'output store exists'):
            nest_store.apply(self.source['pose'], self.pins, out)
        empty = write_store(self.fresh('empty_source'), [])
        target = self.fresh('empty')
        report = nest_store.apply(empty, self.pins, target)
        self.assert_refused(report, target, 0)
        self.assertEqual(report['reason'], 'empty source store')


if __name__ == '__main__':
    unittest.main()
