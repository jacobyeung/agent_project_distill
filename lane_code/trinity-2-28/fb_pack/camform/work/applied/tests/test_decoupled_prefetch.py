"""CPU row parity, bounded overlap, allocation sizing and worker cleanup."""
from contextlib import closing
import copy
import json
import os
import random
import sqlite3
import threading
import unittest
from unittest.mock import patch

import torch
from PIL import Image

from student_pilot import decoupled_v_run as run
from student_pilot.p3_provenance import file_pin
from tests import test_decoupled_startup as startup


class PrefetchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        startup.StartupTests.setUpClass()

    def fixture(self, all_frames=False):
        helper = startup.StartupTests()
        out, _, _, _ = helper.fixture('decoupled_vc', all_frames=all_frames)
        return out/'rows.sqlite', helper

    def test_exact_rows_order_and_every_tensor_across_steps_and_wraps(self):
        for all_frames in (False, True):
            database, helper = self.fixture(all_frames)
            # Distinct RGB and target values expose accidental reuse/reordering.
            with closing(sqlite3.connect(database)) as conn:
                for index, raw, target in conn.execute('SELECT i,row,target FROM rows').fetchall():
                    row, target = json.loads(raw), json.loads(target)
                    image = database.parent/f'{index}_rgb.png'
                    Image.new('RGB', (64, 64), color=(index*20, 70, 110)).save(image)
                    row['student_input']['frames'] = [file_pin(image)]*32
                    target['trajectory_scale'] = index+.125
                    # A1 also expands inherited 16-slot depth rows into 32 slots.
                    if all_frames and index % 2:
                        for key in ('camera', 'camera_mask'):
                            target[key] = target[key][::2]
                        target['point_depth'] = {k: v[::2] for k, v in target['point_depth'].items()}
                    conn.execute('UPDATE rows SET row=?,target=? WHERE i=?',
                                 (json.dumps(row), json.dumps(target), index))
                conn.commit()
                records = {i: (json.loads(r), json.loads(t))
                           for i, r, t in conn.execute('SELECT i,row,target FROM rows')}
            for rank in (0, 3, 7):
                batches = run.index_batches(9)
                expected_order = [i for _ in range(3) for i in next(batches)[rank::8]]
                self.assertEqual(list(run.rank_rows(9, rank, 8, 3)), expected_order)
                with patch('student_pilot.batches.training_stop_token', side_effect=helper.tiny_stop):
                    reference = {}
                    for index, (row, target) in records.items():
                        reference[index] = (run.encode(helper.processor, row),
                            run.target_tensors(target, 'cpu', all_frames=all_frames))
                    observed = []
                    real_encode = run.encode

                    def record(processor, row):
                        observed.append(copy.deepcopy(row))
                        return real_encode(processor, row)

                    rng, python_rng = torch.get_rng_state().clone(), random.getstate()
                    with patch.object(run, 'encode', side_effect=record), run.prefetch_rows(
                            database, helper.processor, iter(expected_order), workers=3,
                            all_frames=all_frames) as rows:
                        for expected_index in expected_order:
                            index, batch, targets = next(rows)
                            self.assertEqual(index, expected_index)
                            for got, expected in zip((batch, targets), reference[index]):
                                self.assertEqual(got.keys(), expected.keys())
                                for name in got:
                                    self.assertEqual(got[name].device.type, 'cpu')
                                    torch.testing.assert_close(got[name], expected[name], rtol=0, atol=0)
                        with self.assertRaises(StopIteration):
                            next(rows)
                    self.assertEqual(sorted(r['qid'] for r in observed),
                                     sorted(records[i][0]['qid'] for i in expected_order))
                    for row in observed:
                        self.assertEqual(row, records[int(row['qid'])][0])
                    self.assertTrue(torch.equal(torch.get_rng_state(), rng))
                    self.assertEqual(random.getstate(), python_rng)

    def test_bounded_overlap_private_processors_and_cleanup(self):
        database, helper = self.fixture()
        second_started = threading.Event()
        calls, connections, owners = [], [], {}
        real_connect = sqlite3.connect
        lock = threading.Lock()

        def connect(*args, **kwargs):
            connection = real_connect(*args, **kwargs)
            connections.append(connection)
            return connection

        def encode(processor, row):
            index = int(row['qid'])
            with lock:
                calls.append(index)
                owners[threading.get_ident()] = processor
            if index == 0:
                self.assertTrue(second_started.wait(5), 'Second decoder did not overlap the first')
            else:
                second_started.set()
            return {'index': torch.tensor(index)}

        with patch.object(run.sqlite3, 'connect', side_effect=connect), \
             patch.object(run, 'encode', side_effect=encode):
            with run.prefetch_rows(database, helper.processor, range(9), workers=2) as rows:
                self.assertEqual(next(rows)[0], 0)  # Row 1 finishes before row 0, but cannot overtake it.
                self.assertLessEqual(len(calls), 5)  # Current row plus four ahead, never the whole epoch.
                self.assertEqual(next(rows)[0], 1)
                # Exit early, as on a consumer/forward failure.
        self.assertGreaterEqual(len(owners), 2)
        self.assertEqual(len({id(p) for p in owners.values()}), len(owners))
        self.assertNotIn(id(helper.processor), [id(p) for p in owners.values()])
        self.assertFalse(any(t.name.startswith('row-decode') for t in threading.enumerate()))
        for connection in connections:
            with self.assertRaises(sqlite3.ProgrammingError):
                connection.execute('SELECT 1')

    def test_worker_exception_reaches_consumer_and_closes_resources(self):
        database, helper = self.fixture()
        connections = []
        real_connect = sqlite3.connect

        def connect(*args, **kwargs):
            connection = real_connect(*args, **kwargs)
            connections.append(connection)
            return connection

        def encode(processor, row):
            if row['qid'] == '1':
                raise ValueError('row decode failed')
            return {}

        with patch.object(run.sqlite3, 'connect', side_effect=connect), \
             patch.object(run, 'encode', side_effect=encode):
            with self.assertRaisesRegex(ValueError, 'row decode failed'):
                with run.prefetch_rows(database, helper.processor, range(9), workers=2) as rows:
                    self.assertEqual(next(rows)[0], 0)
                    next(rows)
        self.assertFalse(any(t.name.startswith('row-decode') for t in threading.enumerate()))
        for connection in connections:
            with self.assertRaises(sqlite3.ProgrammingError):
                connection.execute('SELECT 1')

    def test_worker_count_respects_slurm_and_affinity(self):
        cases = [({}, 48, 4), ({'SLURM_CPUS_PER_GPU': '2'}, 48, 1),
                 ({'SLURM_CPUS_PER_GPU': '6'}, 48, 4),
                 ({'SLURM_CPUS_PER_TASK': '24'}, 128, 2),
                 ({'SLURM_CPUS_ON_NODE': '16'}, 128, 1), ({}, 8, 1), ({}, 1, 1)]
        for env, affinity, expected in cases:
            with self.subTest(env=env, affinity=affinity), patch.dict(os.environ, env, clear=True), \
                 patch.object(os, 'sched_getaffinity', return_value=set(range(affinity))):
                self.assertEqual(run.row_workers(8), expected)


if __name__ == '__main__':
    unittest.main()
