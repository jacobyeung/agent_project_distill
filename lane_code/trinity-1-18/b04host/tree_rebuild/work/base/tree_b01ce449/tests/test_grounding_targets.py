"""Synthetic first-hit rasters for GH clip regrouping and evaluation."""
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np
import torch

from student_pilot import grounding_targets as G


class GroundingTargets(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = Path(tempfile.mkdtemp(prefix='grounding_targets_', dir=os.environ['LANE_TEST_OUTPUT']))

    def folder(self):
        return Path(tempfile.mkdtemp(prefix='case_', dir=self.root))

    def fixture(self):
        root = self.folder()
        inst = np.full(G.SHAPE, -1, np.int16)
        used = np.zeros(32, bool)
        used[:8] = True
        inst[0, :20, :20] = 1
        inst[0, 200:210, 300:320] = 2
        inst[1, :2, :10] = 1
        inst[2, :8, :20] = 1
        inst[3, :10, :10] = 1
        inst[3, 20:30, :10] = 2
        inst[0, 30:50, :20] = 3
        inst[0, 50:70, :20] = 4
        inst[0, 70:90, :20] = 5
        inst[8:] = -2
        labels = [' Chair ', 'CHAIR', ' WALL ', 'ceiling panel', 'SideWall', 'lamp']
        path = root / 'c' / 'recording' / 'full-question.npz'
        path.parent.mkdir(parents=True)
        with path.open('xb') as handle:
            np.savez_compressed(handle, inst=inst, used=used, ids=np.arange(1, 7, dtype=np.int32),
                                labels=np.array(labels, dtype='<U64'))
        row = dict(scene='recording', qid='full-question-id-not-the-short-name', path=str(path.relative_to(root)),
                   rgb_wh=[640, 480], clip13=path.stem)
        (root / 'clips.jsonl').write_text(json.dumps(row) + '\n')
        return root, path, inst, used, row

    def units(self, path, **kwargs):
        return G.units_for_clip(path, (10, 14), [], absent_share=0, seed_key='fixed', **kwargs)

    def test_presence_unused_structural_and_full_qid(self):
        _, path, _, used, row = self.fixture()
        units = self.units(path)
        self.assertEqual(units.qid, row['qid'])
        self.assertEqual(units.scene, row['scene'])
        self.assertEqual(set(units.labels), {'chair', 'sidewall'})
        q = units.labels.index('chair')
        np.testing.assert_equal(units.presence[q, :5], [1, np.nan, 1, np.nan, 0])
        self.assertTrue(np.isnan(units.presence[:, ~used]).all())
        self.assertTrue(np.isnan(units.point[units.presence != 1]).all())
        np.testing.assert_array_equal(units.mass[units.presence != 1], 0)
        self.assertEqual(units.largest[q, 0], 1)
        self.assertEqual(units.largest[q, 3], 1)
        self.assertEqual(units.largest[q, 4], -1)
        self.assertEqual(units.largest[q, 5], -1)

    def test_multi_instance_union_mass_largest_point_and_trainer_parity(self):
        from student_pilot.carrier_c1_data import mask_target
        _, path, inst, _, _ = self.fixture()
        units = self.units(path)
        q = units.labels.index('chair')
        mask = G.eval_masks(units, q, 0)
        self.assertEqual(mask.dtype, np.bool_)
        self.assertEqual(mask.shape, (480, 640))
        self.assertTrue(G.in_mask([960, 850], mask))  # Smaller chair instance also counts.
        self.assertFalse(G.in_mask([2, 40], mask))
        mask_path = path.parent / 'mask.npz'
        with mask_path.open('xb') as handle:
            np.savez_compressed(handle, mask=inst[0] == 1)
        pin = dict(path=str(mask_path), sha256=hashlib.sha256(mask_path.read_bytes()).hexdigest())
        _, target = mask_target(pin)
        np.testing.assert_array_equal(units.point[q, 0], target['uv'])
        self.assertTrue(G.in_mask(units.point[q, 0], mask))
        self.assertFalse(G.in_mask(units.point[q, 0], inst[0] == 2))
        self.assertAlmostEqual(float(units.mass[q, 0, -4:, -4:].sum()), 1 / 3, places=6)
        np.testing.assert_allclose(units.mass[units.presence == 1].sum(axis=(-2, -1)), 1, atol=1e-7)
        self.assertFalse(G.eval_masks(units, q, 4).any())

    def test_eroded_union_matches_scipy_with_resize_and_small_instance_fallback(self):
        try:
            from scipy.ndimage import binary_erosion
        except ImportError:
            self.skipTest('scipy is unavailable; production erosion uses numpy')
        from PIL import Image
        rng = np.random.default_rng(17)
        for mask in (np.ones((10, 12), bool), rng.random((30, 40)) > .2,
                     np.zeros((10, 12), bool)):
            np.testing.assert_array_equal(G.erode_cross(mask), binary_erosion(mask, iterations=2))
        _, path, inst, _, row = self.fixture()
        for rgb_wh in ([640, 480], [321, 241], [80, 60]):
            units = self.units({**row, 'path': str(path), 'rgb_wh': rgb_wh})
            q = units.labels.index('chair')
            for f in (0, 1, 2, 3, 4):
                expected = np.zeros(tuple(reversed(rgb_wh)), bool)
                for iid in (1, 2):
                    mask = np.asarray(Image.fromarray(inst[f] == iid).resize(rgb_wh, Image.Resampling.NEAREST))
                    eroded = binary_erosion(mask, iterations=2)
                    expected |= eroded if eroded.sum() >= 8 else mask
                np.testing.assert_array_equal(G.eval_masks(units, q, f), expected)

    def test_grid_mapping_uses_raster_pixel_centres(self):
        _, path, inst, _, _ = self.fixture()
        for gh, gw in ((10, 14), (12, 16)):
            units = G.units_for_clip(path, (gh, gw), [], absent_share=0, seed_key=17)
            q = units.labels.index('chair')
            expected = np.zeros((2 * gh, 2 * gw), np.float64)
            y, x = np.where((inst[0] == 1) | (inst[0] == 2))
            for py, px in zip(y, x):
                expected[int((py + .5) / 240 * 2 * gh), int((px + .5) / 320 * 2 * gw)] += 1
            expected /= expected.sum()
            np.testing.assert_allclose(units.mass[q, 0], expected, atol=1e-7)

    def test_tensors_mask_nan_values_and_empty_units(self):
        _, path, _, _, _ = self.fixture()
        units = self.units(path)
        targets = G.to_tensors(units)
        self.assertEqual(set(targets), {'presence', 'presence_valid', 'mass', 'point', 'point_valid'})
        for key in ('presence', 'mass', 'point'):
            self.assertEqual(targets[key].dtype, torch.float32)
            self.assertTrue(torch.isfinite(targets[key]).all())
        np.testing.assert_array_equal(targets['presence_valid'].numpy(), np.isfinite(units.presence))
        np.testing.assert_array_equal(targets['point_valid'].numpy(), units.presence == 1)
        self.assertEqual(targets['presence_valid'].dtype, torch.bool)
        empty = self.units(path, max_visible=0)
        self.assertEqual(empty.mass.shape, (0, 32, 20, 28))
        self.assertEqual(G.to_tensors(empty)['point'].shape, (0, 32, 2))

    def test_absent_whole_recording_exclusion_share_and_determinism(self):
        root = self.folder()
        inst = np.full(G.SHAPE, -1, np.int16)
        labels = [f'item {i}' for i in range(25)] + ['hidden fixture']
        for i in range(25):
            inst[0, i * 8:(i + 1) * 8, :20] = i
        used = np.ones(32, bool)
        used[-1] = False
        inst[-1] = -2
        path = root / 'many.npz'
        with path.open('xb') as handle:
            np.savez_compressed(handle, inst=inst, used=used, ids=np.arange(len(labels), dtype=np.int32),
                                labels=np.array(labels), scene='scene', qid='qid')
        vocab = labels + [f'absent {i}' for i in range(100)] + ['Wall', '']
        a = G.units_for_clip(path, (12, 16), vocab, max_visible=18, seed_key='seed 17')
        b = G.units_for_clip(path, (12, 16), reversed(vocab), max_visible=18, seed_key='seed 17')
        self.assertEqual(a.labels, b.labels)
        self.assertEqual(a.kind.count('visible'), 18)
        self.assertEqual(a.kind.count('clip_absent'), 2)
        self.assertAlmostEqual(a.kind.count('clip_absent') / len(a.labels), .1)
        expected = sorted(labels[:25], key=lambda label: G._hash(f'qid|{label}'))[:18]
        self.assertEqual(a.labels[:18], expected)
        for label, kind, pres in zip(a.labels, a.kind, a.presence):
            if kind == 'clip_absent':
                self.assertNotIn(label, labels)
                np.testing.assert_array_equal(pres[used], 0)
                self.assertTrue(np.isnan(pres[~used]).all())
        for key in ('presence', 'mass', 'point', 'largest'):
            np.testing.assert_equal(getattr(a, key), getattr(b, key))
        c = G.units_for_clip(path, (12, 16), vocab, max_visible=18, seed_key='seed 18')
        self.assertEqual(a.labels[:18], c.labels[:18])
        self.assertNotEqual(a.labels[18:], c.labels[18:])

    def test_vectorised_in_mask_broadcast_boundaries_and_invalid(self):
        mask = np.zeros((240, 320), bool)
        mask[120, 160] = True
        mask[-1, -1] = True
        points = np.array([[500, 500], [1000, 1000], [0, 0], [np.nan, 2], [-1, 500], [1001, 500], [np.inf, 0]])
        np.testing.assert_array_equal(G.in_mask(points, mask), [True, True, False, False, False, False, False])
        masks = np.stack([mask, ~mask])
        np.testing.assert_array_equal(G.in_mask([500, 500], masks), [True, False])
        np.testing.assert_array_equal(G.in_mask(np.array([[[500, 500]], [[0, 0]]]), masks), [[True, False], [False, True]])
        with self.assertRaises(ValueError):
            G.in_mask([0, 0], mask.astype(int))

    def metadata_index(self):
        root = self.folder()
        rows = []
        scenes = sorted([f'scene{i:02d}' for i in range(24)], key=G._hash)
        for s, scene in enumerate(scenes):
            path = root / (scene + '.npz')
            labels = [' Chair ', 'Wall', 'train rare' if s < 5 else 'train common']
            if s == 0:
                labels.append('validation only')
            inst = np.full(G.SHAPE, -1, np.int16)
            inst[0, :20, :20] = 0
            with path.open('xb') as handle:
                np.savez_compressed(handle, ids=np.arange(len(labels)), labels=np.array(labels),
                                    inst=inst, used=np.ones(32, bool))
            for clip in range(3):
                rows.append(dict(scene=scene, qid=f'{scene}-clip{clip}', path=path.name, rgb_wh=[640, 480]))
        index = root / 'clips.jsonl'
        index.write_text(''.join(json.dumps(r) + '\n' for r in rows))
        return root, index, scenes

    def test_scene_disjoint_split_excludes_and_training_recording_vocab(self):
        _, index, scenes = self.metadata_index()
        result = G.build_index([index], exclude_scenes=[scenes[-1]], holdout_fraction=.05)
        train = {r['scene'] for r in result['train']}
        val = {r['scene'] for r in result['val']}
        self.assertFalse(train & val)
        self.assertEqual(val, set(scenes[:2]))
        self.assertNotIn(scenes[-1], train | val)
        self.assertEqual(result['vocab'], ['chair'])
        self.assertTrue(all(Path(r['path']).is_absolute() for r in result['train']))
        self.assertEqual(result, G.build_index([index], exclude_scenes=[scenes[-1]], holdout_fraction=.05))
        unheld = G.build_index(index, exclude_scenes=[], holdout_fraction=0)
        self.assertEqual(unheld['vocab'], ['chair'])
        self.assertEqual(unheld['val'], [])
        with self.assertRaises(ValueError):
            G.build_index([index, index], exclude_scenes=[])

    def test_index_filters_gated_short_and_nonvisible_clips_and_counts_reasons(self):
        root = self.folder()
        rows = []
        cases = [('all_gated', 0, 'chair', 20), ('short', 7, 'chair', 20),
                 ('structural', 8, 'wall', 20), ('tiny', 8, 'chair', 2),
                 ('absent', 8, 'chair', 0), ('eligible', 8, 'chair', 20)]
        for name, n_used, label, side in cases:
            inst = np.full(G.SHAPE, -2, np.int16)
            inst[:n_used] = -1
            if n_used:
                inst[0, :side, :side] = 1
            path = root / f'{name}.npz'
            with path.open('xb') as stream:
                np.savez_compressed(stream, inst=inst, used=np.arange(32) < n_used,
                                    ids=np.array([1]), labels=np.array([label]))
            rows.append(dict(scene=name, qid=name, path=path.name, rgb_wh=[640, 480], n_used=32))
        index = root / 'clips.jsonl'
        index.write_text(''.join(json.dumps(row) + '\n' for row in rows))
        result = G.build_index(index, exclude_scenes=[], holdout_fraction=0)
        self.assertEqual([row['qid'] for row in result['train']], ['eligible'])
        self.assertEqual(result['filtered_clips'], dict(total=5, n_used_lt_8=2, no_visible_label=3))

    def test_training_vocabulary_threshold_is_distinct_recordings(self):
        _, index, scenes = self.metadata_index()
        self.assertEqual(G.build_index(index, exclude_scenes=scenes[19:], holdout_fraction=0)['vocab'], [])
        self.assertEqual(G.build_index(index, exclude_scenes=scenes[20:], holdout_fraction=0)['vocab'], ['chair'])

    def test_p013_without_labels_and_bad_r7_fail_clearly(self):
        root = self.folder()
        path = root / 'p013.npz'
        with path.open('xb') as handle:
            np.savez_compressed(handle, inst=np.full(G.SHAPE, -1, np.int16))
        with self.assertRaisesRegex(NotImplementedError, 'SCENE_VISIBILITY'):
            self.units(path)
        root, path, inst, used, row = self.fixture()
        used[8] = True
        bad = root / 'bad.npz'
        with bad.open('xb') as handle:
            np.savez_compressed(handle, inst=inst, used=used, ids=np.arange(1, 7),
                                labels=np.array(['chair'] * 6), scene='s', qid='q')
        with self.assertRaisesRegex(ValueError, 'Failed-gate'):
            self.units(bad)
        for kwargs in (dict(grid=(0, 14)), dict(absent_share=1), dict(max_visible=-1)):
            args = dict(grid=(10, 14), absent_share=.1, max_visible=24, seed_key=17)
            args.update(kwargs)
            with self.assertRaises(ValueError):
                G.units_for_clip(path, vocab=[], **args)

    def test_audit_cli_reports_counts_entropy_and_size_bins(self):
        root, path, _, _, _ = self.fixture()
        output = root / 'audit.json'
        result = subprocess.run([sys.executable, '-B', '-m', 'student_pilot.grounding_targets', 'audit',
                                 '--clips', str(root / 'clips.jsonl'), '--root', str(root), '--n', '50', '--out', str(output)],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(output.read_text())
        self.assertEqual(report['clip_count'], 1)
        clip = report['clips'][0]
        self.assertEqual(clip['label_count'], 2)
        self.assertEqual(clip['clip_absent_count'], 0)
        self.assertEqual(clip['presence'], {'1': 3, '0': 11, 'ignore': 50})
        self.assertEqual(clip['size_bins'], {'<1%': 3, '1-5%': 0, '>5%': 0})
        self.assertGreater(clip['mean_mass_entropy'], 0)
        relocated = root / 'separate-index.jsonl'
        relocated.write_text((root / 'clips.jsonl').read_text())
        self.assertEqual(G.audit(relocated, root), report)

    def test_grid_for_matches_native_video_processor(self):
        from student_pilot.decoupled_v_run import processor_for
        processor = processor_for('/scratch/jjyeung/orch_cd/p3_build/fixtures/qwen35_processor')
        video_processor = processor.video_processor
        from student_pilot.pose_samples import DEFAULT_PIXELS
        for w, h in ((640, 480), (1752, 1168)):
            with self.subTest(rgb_wh=(w, h)):
                frames = np.zeros((2, h, w, 3), np.uint8)
                native = video_processor(videos=[frames], do_sample_frames=False,
                    size=dict(shortest_edge=2 * DEFAULT_PIXELS[0], longest_edge=2 * DEFAULT_PIXELS[1]),
                    return_tensors='pt')
                native_grid = tuple(int(v) // 2 for v in native['video_grid_thw'][0, 1:])
                self.assertEqual(G.grid_for((w, h)), native_grid)
                self.assertEqual(G.grid_for((w, h), {'num_frames': 2}), native_grid)
        self.assertEqual(G.grid_for((640, 480)), (10, 13))
        self.assertEqual(G.grid_for((1752, 1168)), (9, 14))
        self.assertEqual(G.grid_for((640, 480), {'size': dict(shortest_edge=64 * 480 * 640,
                                                           longest_edge=64 * 480 * 640)}), (15, 20))


if __name__ == '__main__':
    unittest.main()
