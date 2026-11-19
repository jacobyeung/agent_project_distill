"""Two real gloo ranks exercise the production loop with tiny CPU models."""
from contextlib import ExitStack, nullcontext
import copy
import json
import os
from pathlib import Path
import random
import sqlite3
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import numpy as np
import torch
import torch.distributed as dist
import torch.multiprocessing as mp

from student_pilot import decoupled_resume as state
from student_pilot import decoupled_v_run as run
from student_pilot.decoupled_vc import VC_BATCH4H_RECIPE
from student_pilot.p3_provenance import file_pin


class Cancelled(Exception):
    pass


class CpuValue:
    def __init__(self, index):
        self.value = torch.tensor([[index/19.]])

    def to(self, device):
        return self.value


class Tiny(torch.nn.Module):
    def __init__(self, seen):
        super().__init__()
        self.auxiliary_heads = torch.nn.Linear(1, 1)
        self.model = torch.nn.Module()
        self.model.visual = torch.nn.Linear(1, 1)
        self.register_buffer('counter', torch.tensor(0))
        self.config = SimpleNamespace(p3={'feature_backing':'decoupled_vc'})
        self.seen = seen
        self.stop_after = None

    def to(self, *args, **kwargs):
        return self

    def forward(self, batch, targets):
        if self.stop_after is not None and len(self.seen) == self.stop_after:
            raise Cancelled('Simulated cancellation between milestones')
        self.seen.append(round(float(batch['x'])*19))
        self.counter.add_(1)
        noise = torch.rand(()) + random.random() + float(np.random.random())
        return (self.auxiliary_heads(self.model.visual(batch['x']))-noise).square()


def export(model, directory, step, provenance):
    from safetensors.torch import save_file
    directory.mkdir()
    save_file(model.auxiliary_heads.state_dict(), str(directory/'heads.safetensors'))
    save_file(model.model.visual.state_dict(), str(directory/'encoder.safetensors'))
    (directory/'heads.json').write_text(json.dumps(dict(step=step, provenance=provenance,
        weights=file_pin(directory/'heads.safetensors'),
        encoder_copy=dict(weights=file_pin(directory/'encoder.safetensors')))))


def worker(rank, root, distributed=True):
    root = Path(root)
    torch.set_num_threads(1)
    recipe = {**VC_BATCH4H_RECIPE, 'steps':6, 'milestones':[2,4,6], 'global_batch':16, 'world_size':2}
    cfg = dict(recipe=recipe, preparation=None, mode='decoupled_vc', output=str(root/'full'))
    receipt = dict(count=19, settings={}, model={}, database={'path':str(root/'rows.sqlite')})
    seen, models = [], []
    real_init, ddp, real_save = dist.init_process_group, torch.nn.parallel.DistributedDataParallel, state.save
    attempt = 0

    def init(backend):
        nonlocal attempt
        attempt += 1
        real_init('gloo', init_method='file://'+str(root/f'join_{attempt}'), rank=rank, world_size=2)

    def model(*args):
        item = Tiny(seen)
        models.append(item)
        return item

    with ExitStack() as stack:
        if not distributed:
            class LocalDDP:
                def __init__(self, model, **kwargs): self.model = model
                def __call__(self, *args): return self.model(*args)
                def no_sync(self): return nullcontext()
            ddp = LocalDDP
            real_init = lambda *args, **kwargs: None
            for name in ('barrier', 'destroy_process_group', 'all_reduce'):
                stack.enter_context(patch.object(dist, name))
            stack.enter_context(patch.object(dist, 'get_rank', return_value=rank))
            stack.enter_context(patch.object(dist, 'get_world_size', return_value=2))
            stack.enter_context(patch.object(dist, 'all_gather_object',
                side_effect=lambda values,value: values.__setitem__(slice(None), [value,value])))
        stack.enter_context(patch.dict(os.environ, RANK=str(rank), STAGE1_TRAINER_COMMIT='a'*40))
        stack.enter_context(patch.object(run, 'RECIPE', recipe))
        stack.enter_context(patch.object(run, 'training_ranks', return_value=(rank,2,rank)))
        stack.enter_context(patch.object(run, 'prepared', return_value=(receipt, {'root':'unused'})))
        stack.enter_context(patch.object(run, 'load_vision', side_effect=model))
        stack.enter_context(patch.object(run, 'processor_for', return_value=None))
        stack.enter_context(patch.object(run, 'row_workers', return_value=2))
        stack.enter_context(patch.object(run, 'encode', side_effect=lambda p,r: {'x':CpuValue(r['i'])}))
        stack.enter_context(patch.object(run, 'target_tensors', return_value={}))
        stack.enter_context(patch.object(run, 'export_heads', side_effect=export))
        stack.enter_context(patch.object(torch.cuda, 'set_device'))
        stack.enter_context(patch.object(dist, 'init_process_group', side_effect=init))
        stack.enter_context(patch('torch.nn.parallel.DistributedDataParallel',
            side_effect=lambda m,**kw: ddp(m, broadcast_buffers=False, find_unused_parameters=True)))
        random.seed(100+rank); np.random.seed(200+rank)
        run.train(cfg)
        expected = {n:t.clone() for n,t in models[-1].state_dict().items()}
        expected_order = list(seen)
        expected_rng = state.rng_state()
        seen.clear()
        cfg['output'] = str(root/'split')
        random.seed(100+rank); np.random.seed(200+rank)

        def stop_after_save(*args):
            real_save(*args)
            if args[1] == 2:
                # Finish step three, then cancel with a metric tail and prefetched rows.
                models[-1].stop_after = 24
            elif args[1] == 4:
                raise Cancelled('Simulated second cancellation after milestone')

        with patch.object(state, 'save', side_effect=stop_after_save):
            try:
                run.train(cfg)
            except Cancelled:
                pass
            else:
                raise AssertionError('Expected cancellation')
        assert len(seen) == 24
        seen[:] = seen[:16]  # Step three must replay from the saved step-two cursor.
        # A fresh process can start with any RNG and reconstruct the saved state.
        random.seed(999); np.random.seed(999); torch.manual_seed(999)
        with patch.object(state, 'save', side_effect=stop_after_save):
            try:
                run.train(cfg, resume=True)
            except Cancelled:
                pass
            else:
                raise AssertionError('Expected second cancellation')
        run.train(cfg, resume=True)
        assert seen == expected_order, (seen, expected_order)
        for name, tensor in models[-1].state_dict().items():
            torch.testing.assert_close(tensor, expected[name], rtol=0, atol=0)
        actual_rng = state.rng_state()
        assert actual_rng['python'] == expected_rng['python']
        assert np.array_equal(actual_rng['numpy'][1], expected_rng['numpy'][1])
        assert actual_rng['numpy'][2:] == expected_rng['numpy'][2:]
        assert torch.equal(actual_rng['torch'], expected_rng['torch'])
        if rank == 0:
            assert (root/'full/train/metrics.jsonl').read_bytes() == (root/'split/train/metrics.jsonl').read_bytes()
        (root/f'rank_{rank}.ok').write_text('weights, buffers, RNG, LRs, losses and batch order match exactly\n')


def fixture():
    root = Path(tempfile.mkdtemp(prefix='resume_', dir=os.environ['LANE_TEST_OUTPUT']))
    conn = sqlite3.connect(root/'rows.sqlite')
    conn.execute('CREATE TABLE rows(i INTEGER PRIMARY KEY,row TEXT,target TEXT)')
    conn.executemany('INSERT INTO rows VALUES(?,?,?)', [(i,json.dumps({'i':i}),'{}') for i in range(19)])
    conn.commit(); conn.close()
    return root


class GlooResumeTests(unittest.TestCase):
    def test_two_ranks_resume_matches_uninterrupted(self):
        root = fixture()
        mp.start_processes(worker, args=(str(root),), nprocs=2, start_method='fork', join=True)
        for rank in range(2):
            self.assertTrue((root/f'rank_{rank}.ok').is_file())


class ResumeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = fixture()
        # Unit checks remain runnable in sandboxes that prohibit local sockets.
        # GlooResumeTests above always uses real collectives and never falls back.
        worker(0, cls.root, distributed=False)

    def saved(self):
        directory = self.root/'split/train/step_2'
        marker = json.loads((directory/'complete.json').read_bytes())
        return directory, marker

    def copy_state(self, names=None):
        source, marker = self.saved()
        root = Path(tempfile.mkdtemp(prefix='partial_', dir=os.environ['LANE_TEST_OUTPUT']))
        dest = root/'step_2'; dest.mkdir()
        for name in names or [*marker['files'], 'complete.json']:
            (dest/name).write_bytes((source/name).read_bytes())
        return root, marker['binding']

    def test_local_loop_resume_and_immutable_exports(self):
        self.assertTrue((self.root/'rank_0.ok').is_file())
        directory, marker = self.saved()
        artifact = json.loads((directory/'heads.json').read_bytes())
        self.assertEqual(artifact['weights'], file_pin(directory/'heads.safetensors'))
        self.assertEqual(artifact['encoder_copy']['weights'], file_pin(directory/'encoder.safetensors'))
        # Resume retained the selected export byte-for-byte.
        for name, digest in marker['files'].items():
            self.assertEqual(state.sha(directory/name), digest)

    def test_missing_partial_corrupt_and_wrong_identity_refused(self):
        root, bound = self.copy_state(['heads.json', 'heads.safetensors'])
        with self.assertRaisesRegex(ValueError, 'partial'):
            state.newest(root, bound)
        root, bound = self.copy_state()
        for key, value in [('config_sha256','b'*64), ('trainer_commit','b'*40), ('world_size',8), ('row_count',20)]:
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, 'differs'):
                state.newest(root, {**bound, key:value})
        (root/'step_2/resume.pt').write_bytes(b'incomplete')
        with self.assertRaisesRegex(ValueError, 'Partial'):
            state.newest(root, bound)
        empty = root/'empty'; empty.mkdir()
        (empty/'.step_2.crashed.pending').mkdir()
        with self.assertRaisesRegex(ValueError, 'Missing'):
            state.newest(empty, bound)

    def test_latest_complete_pending_tail_metrics_and_completed_refusal(self):
        root, bound = self.copy_state()
        (root/'.step_4.crashed.pending').mkdir()
        payload = state.newest(root, bound)
        self.assertEqual(payload['next_batch'],2)
        (root/'metrics.jsonl').write_bytes(payload['metrics']+b'{"step":3}\n')
        state.restore_metrics(root, payload)
        self.assertEqual((root/'metrics.jsonl').read_bytes(),payload['metrics'])
        self.assertEqual(len(list(root.glob('metrics.*.jsonl'))),1)
        # A public partial export cannot be skipped or overwritten.
        (root/'step_4').mkdir()
        with self.assertRaisesRegex(ValueError, 'partial'):
            state.newest(root, bound)
        with self.assertRaisesRegex(ValueError, 'Final export'):
            state.newest(self.root/'split/train', bound)

    def test_selects_latest_complete_and_preserves_cancelled_publication(self):
        root, bound = self.copy_state()
        source = self.root/'split/train/step_4'
        (root/'step_4').mkdir()
        for path in source.iterdir():
            (root/'step_4'/path.name).write_bytes(path.read_bytes())
        self.assertEqual(state.newest(root, bound)['step'],4)
        saved = {p:p.read_bytes() for p in (root/'step_4').iterdir()}
        with self.assertRaisesRegex(ValueError, 'overwritten'):
            state.final_export(root,4,lambda p: self.fail('Must refuse before exporting'))
        for path, raw in saved.items():
            self.assertEqual(path.read_bytes(),raw)
        def interrupted(path):
            path.mkdir()
            (path/'heads.safetensors').write_bytes(b'partial')
            raise Cancelled()
        with self.assertRaises(Cancelled):
            state.final_export(root,6,interrupted)
        self.assertFalse((root/'step_6').exists())
        self.assertEqual(len(list(root.glob('.step_6.*.pending'))),1)
        self.assertEqual(state.newest(root,bound)['step'],4)

    def test_interrupted_state_write_never_publishes_a_milestone(self):
        root, bound = self.copy_state()
        payload = state.newest(root,bound)
        model = Tiny([])
        optimizer = torch.optim.AdamW(run.parameter_groups(model, bound['recipe']))
        (root/'metrics.jsonl').write_bytes(payload['metrics'])
        with ExitStack() as stack:
            stack.enter_context(patch.object(dist,'get_rank',return_value=0))
            stack.enter_context(patch.object(dist,'get_world_size',return_value=2))
            stack.enter_context(patch.object(dist,'all_gather_object',
                side_effect=lambda values,value: values.__setitem__(slice(None), [value,value])))
            stack.enter_context(patch.object(torch,'save',side_effect=Cancelled()))
            with self.assertRaises(Cancelled):
                state.save(root,4,model,optimizer,bound,lambda p: export(model,p,4,{}))
        self.assertFalse((root/'step_4').exists())
        self.assertEqual(len(list(root.glob('.step_4.*.pending'))),1)
        self.assertEqual(state.newest(root,bound)['step'],2)

    def test_run_lock_and_smoke_rejection(self):
        root = Path(tempfile.mkdtemp(prefix='lock_', dir=os.environ['LANE_TEST_OUTPUT']))
        with state.run_lock(root,0):
            with self.assertRaisesRegex(ValueError, 'active'), state.run_lock(root,0):
                pass
        with state.run_lock(root,0):
            pass
        with self.assertRaisesRegex(ValueError, 'smoke'):
            run.train({},3,resume=True)

    def test_rank_order_resume_across_epoch_wraps(self):
        for count in (3,19,65,200):
            for rank in (0,1):
                all_rows = list(run.rank_rows(count, rank, 2, 8))
                self.assertEqual(list(run.rank_rows(count,rank,2,8,3)), all_rows[3*32:])

    def test_schedule_tampering_is_rejected(self):
        root, bound = self.copy_state()
        payload = state.newest(root, bound)
        model = Tiny([])
        optimizer = torch.optim.AdamW(run.parameter_groups(model, bound['recipe']))
        bad = copy.deepcopy(payload); bad['schedule'][1]['step'] += 1
        with self.assertRaisesRegex(ValueError, 'schedule'):
            state.restore(bad, model, optimizer,0)
