import copy
import importlib.util
import json
from pathlib import Path
import sys
import unittest
import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import score as S
BASE = HERE.parents[1]/'gbuild'
KIT = BASE/'orchard_tower2x'
spec = importlib.util.spec_from_file_location('worker', KIT/'2.py')
W = importlib.util.module_from_spec(spec)
spec.loader.exec_module(W)


def trajectory(angle=0):
    c = np.tile(np.eye(4), (32, 1, 1))
    t = np.arange(32)/5
    c[:, :3, 3] = np.c_[np.cos(t), np.sin(t), t/10]
    q = np.radians(angle*np.sin(t))
    c[:, 0, 0] = c[:, 1, 1] = np.cos(q)
    c[:, 1, 0], c[:, 0, 1] = np.sin(q), -np.sin(q)
    return c


def fixture(fix=True):
    refs, rows = [], []
    for k in range(10):
        gt, before = trajectory(), trajectory(120 if k < 5 else 0)
        ref = dict(key=str(k), capture=str(k), group='failing' if k < 5 else 'reference',
                   t1=before.tolist(), gt=gt.tolist(), scale=1., gravity=[0., -1., 0.], arms=[])
        row = dict(key=str(k), arms=[])
        for a, n in enumerate((32, 64)):
            ids = list(range(0, 64, 2)) if a == 0 else list(range(64))
            slots = list(range(32)) if a == 0 else list(range(0, 64, 2))
            plan = dict(ids=ids, sha256=[f'{i:064x}' for i in ids], slots=slots)
            c = before if a == 0 or not fix else gt
            full = c if a == 0 else np.repeat(c, 2, axis=0)
            ref['arms'].append(plan)
            row['arms'].append(dict(status='ok', **plan, c2w=full.tolist(), scale=1., gravity=ref['gravity']))
        ref['arms'].append(None)
        row['arms'].append(dict(status='unavailable'))
        refs.append(ref)
        rows.append(row)
    return dict(rows=rows, complete=True, stub=False), dict(captures=refs)


class Scoring(unittest.TestCase):
    def test_parent_admission_pins_and_archive_sizes(self):
        import hashlib
        import tempfile
        spec = importlib.util.spec_from_file_location('entry', KIT/'0.py')
        entry = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(entry)
        p = Path(tempfile.mkdtemp(prefix='admission-', dir=KIT))
        (p/'a').mkdir()
        (p/'0.tgz').write_bytes(b'fixture')
        (p/'8').write_bytes(b'1234')
        (p/'a/1.json').write_text(json.dumps(dict(archives=[dict(parts=[dict(path=str(p/'8'), bytes=4)])])))
        cfg = dict(xg=str(p), xh=entry.sha(p/'0.tgz'), xi=entry.sha(p/'a/1.json'))
        entry.admit(cfg)
        with self.assertRaises(ValueError):
            entry.admit(dict(cfg, xh='0'*64))
        (p/'8').write_bytes(b'12345')
        with self.assertRaises(ValueError):
            entry.admit(cfg)

    def test_confirm_and_refute(self):
        for fix, verdict in [(True, 'confirm'), (False, 'refute')]:
            data, ref = fixture(fix)
            out = S.score(data, ref)
            self.assertEqual(out['verdict'], verdict)
            self.assertEqual(out['leaves_gross'], 5 if fix else 0)

    def test_failed_control_void(self):
        data, ref = fixture()
        data['rows'][0]['arms'][0]['c2w'] = trajectory().tolist()
        self.assertEqual(S.score(data, ref)['verdict'], 'void')

    def test_missing_and_stub_not_refute(self):
        data, ref = fixture()
        data['rows'][0]['arms'][1] = dict(status='unavailable')
        self.assertEqual(S.score(data, ref)['verdict'], 'incomplete')
        data['stub'] = True
        self.assertEqual(S.score(data, ref)['verdict'], 'synthetic')

    def test_reference_regression_partial(self):
        data, ref = fixture()
        data['rows'][5]['arms'][1]['c2w'] = np.repeat(trajectory(10), 2, axis=0).tolist()
        self.assertEqual(S.score(data, ref)['verdict'], 'partial')

    def test_ids_hashes_and_slots_fail_closed(self):
        for key in ('ids', 'sha256', 'slots'):
            data, ref = fixture()
            data['rows'][0]['arms'][0][key] = list(reversed(data['rows'][0]['arms'][0][key]))
            with self.assertRaises(ValueError):
                S.score(data, ref)

    def test_no_scale_fit_and_degenerate_centers(self):
        c = trajectory()
        gt = c.copy()
        gt[:, :3, 3] *= 2
        self.assertFalse(S.rigid(c, gt)['accepted'])
        c[:, :3, 3] = 0
        self.assertEqual(S.rigid(c, c)['classification'], 'moderate')

    def test_relative_gauge_invariance(self):
        a = trajectory(70)
        transform = trajectory(50)[5]
        b = transform @ a
        self.assertLess(S.relative(a, b)['rotation_deg']['rms'], 1e-5)
        self.assertLess(S.relative(a, b)['translation_m']['rms'], 1e-12)

    def test_all_496_pairs_and_round7_reproduction(self):
        reference = json.loads((HERE/'REFERENCE.json').read_text())
        split = {r['capture']:r for r in json.loads((HERE.parent/'score_t1/CAMERA_SPLIT.json').read_text())['captures']}
        for r in reference['captures']:
            actual = S.rigid(S.poses(r['t1']), S.poses(r['gt']))
            prior = split[r['capture']]['rigid_fit']
            for k in ('translation_rms_m', 'rotation_rms_deg', 'rotation_max_deg'):
                self.assertAlmostEqual(actual[k], prior[k], places=6)
            pairs = S.relative(S.poses(r['t1']), S.poses(r['gt']))
            self.assertEqual(pairs['pairs'], 496)
            self.assertAlmostEqual(pairs['rotation_deg']['rms'], split[r['capture']]['relative_errors']['rotation_deg']['rms'], delta=1e-5)

    def test_worker_one_capture_shapes_and_missing_arms(self):
        cfg = json.loads((KIT/'1.json').read_text())
        result = W.run(cfg, stub=True, only=1)
        self.assertTrue(result['complete'])
        arms = result['rows'][0]['arms']
        self.assertEqual(np.asarray(arms[0]['c2w']).shape, (32, 4, 4))
        self.assertEqual(arms[0]['ids'], cfg['x3'][0]['x4'][0]['x0'])
        self.assertEqual([x['status'] for x in arms], ['ok', 'unavailable', 'unavailable'])
        self.assertLess(len(json.dumps(result)), 5_000_000)

    def test_worker_64_96_nested_binding_and_forecast_refusal(self):
        cfg = json.loads((KIT/'1.json').read_text())
        row = cfg['x3'][0]
        row['x4'] = [dict(x0=list(range(0, 96, 3)), x1=[f'{i:064x}' for i in range(0, 96, 3)], x2=list(range(32))), None, None]
        for a, ids in [(1, sorted(list(range(0, 96, 3))+list(range(1, 96, 3)))), (2, list(range(96)))]:
            row['x4'][a] = dict(x0=ids, x1=[f'{i:064x}' for i in ids], x2=[ids.index(i) for i in row['x4'][0]['x0']])
            self.assertEqual(len(W.binding(row, a)[0]), (32, 64, 96)[a])
        result = W.run(cfg, stub=True, only=1)
        self.assertTrue(result['complete'])
        self.assertEqual([len(x['c2w']) for x in result['rows'][0]['arms']], [32, 64, 96])
        cfg['x7'][0] = 1501
        with self.assertRaises(ValueError):
            W.run(cfg, stub=True)

    def test_control_threshold(self):
        a = trajectory()
        below, above = trajectory(.4), trajectory(.8)
        self.assertLessEqual(S.relative(a, below)['rotation_deg']['rms'], .5)
        self.assertGreater(S.relative(a, above)['rotation_deg']['rms'], .5)

    def test_frozen_gravity_reconstructs_reference(self):
        sys.path.insert(0, str(BASE/'work/payload/tree'))
        from student_pilot.camera_targets import encode_cameras, to_gravity_reference_frame
        for row in json.loads((HERE/'REFERENCE.json').read_text())['captures']:
            c = np.array(row['t1'])
            raw, _, _ = encode_cameras(c, np.tile(np.eye(3), (32, 1, 1)), [480, 640], all_frames=True)
            r, t, _ = to_gravity_reference_frame(raw, row['gravity'])
            np.testing.assert_allclose(r, c[:, :3, :3], atol=1e-6)
            np.testing.assert_allclose(t, c[:, :3, 3], atol=1e-6)

    def test_real_native_preprocessing_and_worker_with_cpu_stub(self):
        import hashlib
        import tempfile
        from types import SimpleNamespace
        from unittest import mock
        import torch
        from PIL import Image
        sys.path.insert(0, str(BASE/'work/payload/tree'))
        from student_pilot import tower_read as T, _tower_native as N
        from student_pilot.camera_targets import to_gravity_reference_frame
        torch.set_num_threads(1)
        cfg = json.loads((KIT/'1.json').read_text())
        row = copy.deepcopy(cfg['x3'][0])
        root = Path(tempfile.mkdtemp(prefix='cpu-', dir=KIT))
        row['x4'][0]['x1'] = []
        for i in range(32):
            import io
            stream = io.BytesIO()
            Image.new('RGB', tuple(reversed(row['x5'])), (i, 2*i, 3*i)).save(stream, format='PNG')
            raw = stream.getvalue()
            h = hashlib.sha256(raw).hexdigest()
            p = root/h[:2]/(h+'.png')
            p.parent.mkdir(exist_ok=True)
            p.write_bytes(raw)
            row['x4'][0]['x1'].append(h)
        class Head(torch.nn.Module):
            def __init__(self, local):
                super().__init__()
                self.local = local
            def forward(self, camera):
                n = camera[0].shape[1]
                values = [0., 0., 0., 1., 1., 1.2] if self.local else [0., 0., 0., 0., 1.]
                a = torch.tensor(values).repeat(1, n, 1)
                if not self.local:
                    a[0, :, 0] = torch.arange(n)/100
                return [a]
        class Depth(torch.nn.Module):
            def forward(self, small, images, **kw):
                shape = (1, images.shape[1], 518, 518)
                return torch.ones(*shape, 1), torch.ones(shape)
        module = torch.nn.Module()
        module.aggregator = torch.nn.Identity()
        module.local_camera_head, module.global_camera_head = Head(True), Head(False)
        module.depth_head, module.point_head = Depth(), None
        unit = T.FrozenG3TTower(dict(device='cpu', dense_frames=32, depth_chunk_size=8), module=module)
        engine = W.Engine.__new__(W.Engine)
        engine.cfg, engine.stub, engine.unit, engine.np = dict(cfg, xc=str(root)), False, unit, np
        engine.convert = to_gravity_reference_frame
        engine.pt = SimpleNamespace(cuda=SimpleNamespace(reset_peak_memory_stats=lambda:None,
            synchronize=lambda:None, max_memory_allocated=lambda:0, max_memory_reserved=lambda:0))
        def aggregate(_, inputs):
            self.assertEqual(tuple(inputs.shape), (1, 32, 3, 518, 518))
            self.assertTrue(torch.isfinite(inputs).all())
            blocks = [None]*24
            for k in (4, 11, 17, 23):
                blocks[k] = torch.zeros(1, 32, 1, 1)
            return blocks, 0
        with mock.patch.object(N, 'selected_layers', side_effect=aggregate) as called:
            result = engine.run(row, 0)
        self.assertEqual(called.call_count, 1)
        self.assertEqual(result['ids'], row['x4'][0]['x0'])
        self.assertEqual(result['sha256'], row['x4'][0]['x1'])
        self.assertEqual(S.poses(result['c2w']).shape, (32, 4, 4))
        (root/'RESULT.json').write_text(json.dumps(dict(stub=True, native_input=T.NATIVE_INPUT, result=result)))


if __name__ == '__main__':
    unittest.main()
