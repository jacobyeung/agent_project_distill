"""Pinned pointing K1 list admission and shared removal semantics on CPU fixtures."""
import copy
import io
import json
from contextlib import redirect_stdout
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from student_pilot import r1_launch22 as launch
from student_pilot.p3_provenance import file_pin
from student_pilot.row_removals import Removals


POINTING_PIN = 'd21e374f39048c0e142680e0d3b26e5b2b774138747610c1fc4a00da0ec580e1'


class RemovalOrder(unittest.TestCase):
    def cfg(self, order):
        return dict(remove_files=[dict(path='/fixture/'+str(i), sha256=h) for i, h in enumerate(order)],
                    r1_training=dict(launch22=dict(removal_order=list(order))))

    def extended(self):
        return launch.REMOVAL_ORDER[:-1] + (POINTING_PIN, launch.NAMING_REMOVE)

    def accepts(self, order):
        cfg = self.cfg(order)
        # The production naming bytes are not in this fixture; verify the exact pin call.
        with patch('student_pilot.p3_provenance.pinned') as pinned:
            self.assertIsNone(launch.validate_removals(cfg))
            pinned.assert_called_once_with(cfg['remove_files'][-1])

    def refuses(self, order, spec=None):
        cfg = self.cfg(order)
        if spec is not None:
            cfg['r1_training']['launch22']['removal_order'] = list(spec)
        with patch('student_pilot.p3_provenance.pinned') as pinned:
            with self.assertRaisesRegex(ValueError, '^R1_NAMING_REMOVAL_ORDER$'):
                launch.validate_removals(cfg)
            pinned.assert_not_called()

    def test_twelve_pass(self):
        self.accepts(launch.REMOVAL_ORDER)

    def test_thirteen_pass(self):
        self.assertEqual(launch.POINTING_K1_REMOVE, POINTING_PIN)
        self.accepts(self.extended())

    def test_different_thirteenth_refuses(self):
        self.refuses(launch.REMOVAL_ORDER[:-1] + ('f'*64, launch.NAMING_REMOVE))

    def test_pointing_after_naming_refuses(self):
        self.refuses(launch.REMOVAL_ORDER + (POINTING_PIN,))

    def test_pointing_in_any_other_position_refuses(self):
        for index in range(len(launch.REMOVAL_ORDER)-1):
            with self.subTest(index=index):
                order = launch.REMOVAL_ORDER[:index] + (POINTING_PIN,) + launch.REMOVAL_ORDER[index:]
                self.refuses(order)

    def test_duplicate_pointing_refuses(self):
        self.refuses(launch.REMOVAL_ORDER[:-1] + (POINTING_PIN, POINTING_PIN, launch.NAMING_REMOVE))
        self.refuses(launch.REMOVAL_ORDER[:-2] + (POINTING_PIN, POINTING_PIN, launch.NAMING_REMOVE))

    def test_spec_mismatch_refuses(self):
        self.refuses(self.extended(), launch.REMOVAL_ORDER)
        self.refuses(launch.REMOVAL_ORDER, self.extended())

    def test_duplicate_or_missing_naming_refuses(self):
        self.refuses(self.extended() + (launch.NAMING_REMOVE,))
        self.refuses(self.extended()[:-1])

    def test_naming_bytes_still_authenticated(self):
        root = Path(tempfile.mkdtemp(prefix='naming24l4_'))
        path = root/'wrong.json'
        path.write_text('{}')
        for order in (launch.REMOVAL_ORDER, self.extended()):
            cfg = self.cfg(order)
            cfg['remove_files'][-1]['path'] = str(path)
            with self.assertRaisesRegex(ValueError, 'Missing or changed pinned input:'):
                launch.validate_removals(cfg)


class RemovalConsumers(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix='removals24l4_'))

    def jsonl(self, name, rows):
        path = self.root/name
        path.write_text(''.join(json.dumps(row, sort_keys=True)+'\n' for row in rows))
        return file_pin(path)

    def test_shared_lists_remove_only_matching_pointing_keys(self):
        # Real pinned synthetic bytes fill the added list's role; no production hash is forged.
        empty = self.jsonl('empty.jsonl', [])
        pointing = self.jsonl('pointing_k1.jsonl', [dict(row_key='pointing-k1-630')])
        naming = self.jsonl('other.jsonl', [dict(row_key='unrelated-naming-key')])
        before_pins = [empty]*11 + [naming]
        after_pins = before_pins[:-1] + [pointing, naming]
        rows = dict(pointing=[dict(qid='pointing-qid', pointing=dict(row_key='pointing-k1-630'),
                                   provenance=dict(canonical_scene='scannet/scene0630')),
                              dict(qid='pointing-retained')],
                    vqa=[dict(qid='vqa-1', target='yes', provenance=dict(canonical_scene='scannet/scene0630'))],
                    pose=[dict(qid='pose-1', provenance=dict(canonical_scene='scannet/scene0280'))])
        untouched = copy.deepcopy(rows)
        before, after = Removals(before_pins), Removals(after_pins)
        old = {name:[row for row in stream if before.keep(row)] for name, stream in rows.items()}
        new = {name:[row for row in stream if after.keep(row)] for name, stream in rows.items()}
        self.assertEqual(old, rows)
        self.assertEqual(new['pointing'], rows['pointing'][1:])
        self.assertEqual(new['vqa'], old['vqa'])
        self.assertEqual(new['pose'], old['pose'])
        self.assertEqual(rows, untouched)
        self.assertEqual(after.files, after_pins)
        with redirect_stdout(io.StringIO()):
            report = after.report()
        self.assertEqual(len(report), 13)
        self.assertEqual([r['removed'] for r in report], [0]*11 + [1, 0])
        self.assertEqual(report[11]['matched_unique_keys'], 1)
        with self.assertRaisesRegex(ValueError, 'REMOVE-listed row remains'):
            after.assert_clean(rows['pointing'][0])
        for row in new['vqa'] + new['pose']:
            after.assert_clean(row)

    def test_pointing_pin_bytes_still_authenticated(self):
        pin = self.jsonl('pointing.jsonl', [dict(row_key='pointing-k1-630')])
        Path(pin['path']).write_text('[]\n')
        with self.assertRaisesRegex(ValueError, 'Missing or changed pinned input:'):
            Removals([pin])

    def test_union_checks_ignore_unrelated_added_pin(self):
        from student_pilot.r1_coverage import union_rows, verify_union
        base_rows = [dict(row_key='base-vqa', canonical='scannet/scene0001', reason='k1_heldout_v7')]
        extra_rows = [dict(row_key='extra-vqa', canonical='scannet/scene0002', reason='k1_heldout_v7')]
        base = self.jsonl('base.jsonl', base_rows)
        extra = self.jsonl('extra.jsonl', extra_rows)
        union = self.jsonl('union.jsonl', union_rows(base_rows, extra_rows))
        n = self.jsonl('n.jsonl', [dict(row_key='n')])
        pointing = self.jsonl('pointing.jsonl', [dict(row_key='pointing')])
        naming = self.jsonl('naming.jsonl', [dict(row_key='naming')])
        empty = self.jsonl('empty.jsonl', [])
        spec = dict(v7_k1_removal=union, v7_k1_union=dict(base=base, extra=extra, union=union))
        twelve = [empty]*8 + [base, union, n, naming]
        thirteen = twelve[:-1] + [pointing, naming]
        for pins in (twelve, thirteen):
            self.assertTrue(verify_union(spec, pins, base['sha256'], n['sha256']))
            self.assertFalse(verify_union({}, pins, base['sha256'], n['sha256']))
        with self.assertRaisesRegex(ValueError, '^R1_K1_UNION_ORDER$'):
            verify_union(spec, [union, base, n, pointing, naming], base['sha256'], n['sha256'])
        with self.assertRaisesRegex(ValueError, '^R1_K1_UNION_ORDER$'):
            verify_union(spec, thirteen + [union], base['sha256'], n['sha256'])
