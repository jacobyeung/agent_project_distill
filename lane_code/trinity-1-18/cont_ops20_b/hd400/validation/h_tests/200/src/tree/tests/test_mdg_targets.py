"""Retained synthetic r7 unions, negative selection and local embedding/audit CLIs."""
import csv
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

import numpy as np
import torch

from student_pilot import grounding_targets as G, mdg_targets as M
from tests import test_grounding_targets as gh_fixtures
from tests.test_carrier_c1_final import FakeTokenizer


class MDGTargets(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = Path(tempfile.mkdtemp(prefix='mdg_targets_', dir=os.environ['LANE_TEST_OUTPUT']))

    def folder(self):
        return Path(tempfile.mkdtemp(prefix='case_', dir=self.root))

    fixture = gh_fixtures.GroundingTargets.fixture

    def units(self, source, **kwargs):
        args = dict(max_visible=24, absent_share=.3, confuser_share=.5, seed_key='fixed')
        args.update(kwargs)
        vocab = ['sofa', 'stool', 'desk', 'bed', 'bench', ' Chair ', 'LAMP', ' WALL ', '', 'CHAIR']
        table = {'chair': [' Sofa ', 'stool', 'LAMP', 'wall', 'CHAIR', 'unknown', ''],
                 'sidewall': ['bed', 'stool', 'lamp', 'sidewall']}
        return M.mdg_units_for_clip(source, vocab, table, **args)

    def test_presence_matches_gh0_and_union_keeps_ignore_band_pixels(self):
        _, path, inst, used, row = self.fixture()
        units = self.units(path)
        original = G.units_for_clip(path, (2, 3), [], absent_share=0, seed_key='fixed')
        self.assertEqual((units.scene, units.qid), (row['scene'], row['qid']))
        self.assertEqual(units.labels[:2], original.labels)
        np.testing.assert_equal(units.frame_presence[:2], original.presence)
        self.assertEqual(units.frame_presence.dtype, np.float32)
        self.assertEqual(units.masks.dtype, np.bool_)
        self.assertEqual(units.masks.nbytes, len(units.labels) * np.prod(G.SHAPE))
        np.testing.assert_array_equal(units.used, used)
        for q, label in enumerate(units.labels[:2]):
            ids = {'chair': [1, 2], 'sidewall': [5]}[label]
            for f in np.flatnonzero(used):
                np.testing.assert_array_equal(units.masks[q, f], np.isin(inst[f], ids))
        chair = units.labels.index('chair')
        self.assertTrue(np.isnan(units.frame_presence[chair, 3]))
        self.assertEqual(units.masks[chair, 3].sum(), 200)
        self.assertTrue(units.masks[chair, 0, 205, 310])
        self.assertFalse(units.masks[:, ~used].any())
        self.assertFalse(units.unique[chair])
        self.assertTrue(units.unique[units.labels.index('sidewall')])
        self.assertTrue(all(not units.unique[q] for q in range(2, len(units.labels))))
        self.assertTrue(M.in_mask([20, 20], M.eval_masks(units, chair, 0)))

    def test_negative_shares_order_exclusions_and_determinism(self):
        _, path, _, used, _ = self.fixture()
        units = self.units(path, absent_share=.6)
        n_absent = math.ceil(.6 / .4 * 2)
        self.assertEqual(units.kind.count('confuser'), round(.5 * n_absent))
        self.assertEqual(units.kind.count('scene_absent'), n_absent - round(.5 * n_absent))
        self.assertEqual(len(units.labels), len(set(units.labels)))
        negative = units.labels[2:]
        self.assertFalse(set(negative) & {'chair', 'sidewall', 'lamp', 'wall', 'ceiling panel'})
        candidates = {'sofa', 'stool', 'bed'}
        expected = sorted(candidates, key=lambda s: (G._hash(f'fixed|c|{s}'), s))[:2]
        self.assertEqual(units.labels[2:4], expected)
        expected_absent = sorted({'sofa', 'stool', 'desk', 'bed', 'bench'} - set(expected),
                                key=lambda s: (G._hash(f'fixed|{s}'), s))[:1]
        self.assertEqual(units.labels[4:], expected_absent)
        np.testing.assert_array_equal(units.clip_present, [1, 1, 0, 0, 0])
        np.testing.assert_array_equal(units.frame_presence[2:, used], 0)
        self.assertTrue(np.isnan(units.frame_presence[:, ~used]).all())
        self.assertFalse(units.masks[2:].any())
        repeat = self.units(path, absent_share=.6)
        self.assertEqual(units.labels, repeat.labels)
        np.testing.assert_equal(units.frame_presence, repeat.frame_presence)
        np.testing.assert_array_equal(units.masks, repeat.masks)
        self.assertEqual(units.labels[:2], self.units(path, seed_key='different').labels[:2])

    def test_confuser_shortfall_fills_scene_absent_without_duplicates(self):
        _, path, _, _, _ = self.fixture()
        units = M.mdg_units_for_clip(path, ['sofa', 'stool', 'bed', 'desk'], {'chair': ['sofa']},
                                     absent_share=.6, confuser_share=1, seed_key=17)
        self.assertEqual(units.kind, ['visible', 'visible', 'confuser', 'scene_absent', 'scene_absent'])
        self.assertEqual(units.labels[2], 'sofa')
        self.assertEqual(len(units.labels), len(set(units.labels)))
        for share in (0, 1):
            units = self.units(path, confuser_share=share, absent_share=.5)
            self.assertEqual(units.kind.count('confuser'), 2 * share)
        units = M.mdg_units_for_clip(path, [], {}, absent_share=.9, seed_key='fixed')
        self.assertEqual(units.kind, ['visible', 'visible'])

    def test_max_visible_gh0_hash_order_row_input_and_empty_selection(self):
        _, path, _, _, row = self.fixture()
        source = {**row, 'path': str(path)}
        units = self.units(source, max_visible=1)
        gh0 = G.units_for_clip(source, (1, 1), [], max_visible=1, absent_share=0, seed_key=999)
        self.assertEqual(units.labels[:1], gh0.labels)
        np.testing.assert_equal(units.frame_presence[:1], gh0.presence)
        negative = M.mdg_units_for_clip(source, ['chair', 'sidewall', 'sofa'],
                                        {'chair': ['sidewall'], 'sidewall': ['chair']},
                                        max_visible=1, absent_share=.5, confuser_share=1, seed_key='fixed')
        self.assertEqual(negative.kind, ['visible', 'scene_absent'])
        self.assertEqual(negative.labels[1], 'sofa')
        empty = self.units(source, max_visible=0)
        self.assertEqual(empty.labels, [])
        self.assertEqual(empty.masks.shape, (0, *G.SHAPE))
        self.assertEqual(M.to_tensors(empty)['frame_presence'].shape, (0, 32))

    def test_to_tensors_validity_and_zero_copy_masks(self):
        _, path, _, used, _ = self.fixture()
        units = self.units(path, absent_share=.6)
        tensors = M.to_tensors(units)
        self.assertEqual(set(tensors), {'frame_presence', 'frame_valid', 'clip_present', 'masks', 'mask_valid'})
        self.assertEqual(tensors['masks'].dtype, torch.bool)
        self.assertEqual(tensors['masks'].data_ptr(), units.masks.ctypes.data)
        self.assertEqual(tensors['clip_present'].data_ptr(), units.clip_present.ctypes.data)
        np.testing.assert_equal(tensors['frame_presence'], np.nan_to_num(units.frame_presence))
        np.testing.assert_equal(tensors['frame_valid'],
                                np.isfinite(units.frame_presence) & (units.clip_present[:, None] == 1))
        np.testing.assert_equal(tensors['mask_valid'], units.frame_presence == 1)
        self.assertFalse(tensors['frame_valid'][2:].any())
        self.assertFalse(tensors['mask_valid'][:, ~used].any())
        self.assertTrue(np.isnan(units.frame_presence[:, ~used]).all())

    def test_union_work_is_limited_to_used_nonempty_frames(self):
        _, path, _, _, _ = self.fixture()
        isin = np.isin
        shapes = []
        def observed(array, ids):
            shapes.append(array.shape)
            return isin(array, ids)
        with mock.patch.object(M.np, 'isin', side_effect=observed):
            self.units(path, absent_share=.6)
        self.assertEqual(shapes, [(240, 320)] * 5)

    def test_bad_parameters_and_r7_errors_propagate(self):
        root, path, _, _, _ = self.fixture()
        for kwargs in (dict(max_visible=-1), dict(max_visible=1.2), dict(absent_share=1),
                       dict(absent_share=-.1), dict(confuser_share=-.1), dict(confuser_share=1.1)):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                self.units(path, **kwargs)
        unsupported = root / 'p013.npz'
        np.savez(unsupported, inst=np.full(G.SHAPE, -1, np.int16))
        with self.assertRaisesRegex(NotImplementedError, 'SCENE_VISIBILITY'):
            self.units(unsupported)

    def test_cosine_neighbors_normalization_ties_and_small_vocab(self):
        vectors = {'chair': [2, 0], 'stool': [3, 0], 'bed': [0, 2], 'sofa': [-1, 0]}
        table = M.build_confusers([' Chair ', 'chair', 'stool', 'sofa', 'bed', 'wall', ''], vectors.__getitem__, k=10)
        self.assertEqual(table['chair'], ['stool', 'bed', 'sofa'])
        self.assertEqual(table['bed'], ['chair', 'sofa', 'stool'])
        self.assertEqual(set(table), set(vectors))
        self.assertTrue(all(k not in v and len(v) == 3 for k, v in table.items()))
        self.assertEqual(M.build_confusers([], vectors.__getitem__), {})
        self.assertEqual(M.build_confusers(['chair'], vectors.__getitem__), {'chair': []})
        self.assertEqual(M.build_confusers(['chair', 'stool'], vectors.__getitem__, k=0), {'chair': [], 'stool': []})
        for vector in ([0, 0], [np.nan, 1], [[1, 2]], []):
            with self.assertRaises(ValueError):
                M.build_confusers(['chair'], lambda _: vector)
        with self.assertRaises(ValueError):
            M.build_confusers(['chair', 'stool'], lambda v: [1] if v == 'chair' else [1, 2])
        with self.assertRaises(ValueError):
            M.build_confusers(['chair'], vectors.__getitem__, k=-1)

    def embeddings(self, tokenizer=None):
        from safetensors.torch import save_file
        tokenizer = tokenizer or FakeTokenizer()
        weight = torch.arange(64 * 4, dtype=torch.float32).reshape(64, 4).to(torch.bfloat16)
        path = self.folder() / 'tiny.safetensors'
        save_file({'embed': weight, 'never_load': torch.ones(3)}, path)
        return path, weight, tokenizer

    def test_embedder_reads_only_named_tensor_on_cpu_and_mean_rows(self):
        from safetensors import safe_open
        path, weight, tokenizer = self.embeddings()
        loaded = []
        class Reader:
            def __enter__(self):
                self.handle = safe_open(str(path), framework='pt', device='cpu')
                self.handle.__enter__()
                return self
            def __exit__(self, *args):
                return self.handle.__exit__(*args)
            def get_tensor(self, name):
                loaded.append(name)
                return self.handle.get_tensor(name)
        with mock.patch('safetensors.safe_open', return_value=Reader()) as opened:
            embed = M.label_embedder(path, 'embed', tokenizer)
        opened.assert_called_once_with(str(path), framework='pt', device='cpu')
        self.assertEqual(loaded, ['embed'])
        for label in ('chair', 'red chair'):
            expected = weight[tokenizer.encode(label)].float().mean(0).numpy()
            np.testing.assert_array_equal(embed(label), expected)
            self.assertEqual(embed(label).dtype, np.float32)
        with self.assertRaises(ValueError):
            embed('')
        with self.assertRaises(ValueError):
            M.label_embedder(path, 'never_load', tokenizer)
        with self.assertRaises(Exception):
            M.label_embedder(path, 'missing', tokenizer)

    def test_hf_tokenizer_directory_and_confusers_cli(self):
        from transformers import AutoTokenizer
        from safetensors.torch import save_file
        directory = '/scratch/jjyeung/orch_cd/p3_build/fixtures/qwen35_processor'
        tokenizer = AutoTokenizer.from_pretrained(directory, local_files_only=True)
        root = self.folder()
        ids = tokenizer.encode('chair', add_special_tokens=False)
        weight = torch.arange((max(ids) + 1) * 2, dtype=torch.float32).reshape(-1, 2)
        path = root / 'tiny.safetensors'
        save_file({'embed': weight}, path)
        np.testing.assert_array_equal(M.label_embedder(path, 'embed', directory)('chair'), weight[ids].mean(0).numpy())
        index = root / 'index.json'
        index.write_text(json.dumps(dict(vocab=['chair'])))
        output = root / 'confusers.json'
        result = subprocess.run([sys.executable, '-B', '-m', 'student_pilot.mdg_targets', 'confusers',
                                 '--index', str(index), '--embed', f'{path}:embed', '--tokenizer', directory,
                                 '--out', str(output)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(output.read_text()), {'chair': []})

    def test_confusers_cli_index_forms(self):
        root, path, _, _, _ = self.fixture()
        expected = G.build_index([root / 'clips.jsonl'], exclude_scenes=[])
        self.assertEqual(M._load_index([str(root / 'clips.jsonl')]), expected)
        listing = root / 'list.json'
        listing.write_text(json.dumps([str(root / 'clips.jsonl')]))
        self.assertEqual(M._load_index([str(listing)]), expected)

    def audit_fixture(self):
        from PIL import Image
        root, _, inst, used, row = self.fixture()
        path = root / 'audit_clip.npz'
        np.savez_compressed(path, inst=inst, used=used, ids=np.arange(1, 7),
                            labels=np.array(['chair', 'chair', 'desk', 'ceiling panel', 'sidewall', 'lamp']))
        frame_root = root / 'rgb'
        hashes = []
        for f in range(32):
            original = root / f'rgb_{f}.png'
            Image.new('RGB', (40, 30), (f * 7, 30, 80)).save(original)
            raw = original.read_bytes()
            sha = hashlib.sha256(raw).hexdigest()
            hashes.append(sha)
            destination = frame_root / 'k8pd' / sha[:2] / f'{sha}.png'
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(raw)
        index = root / 'audit_clips.jsonl'
        row = {**row, 'path': str(path), 'frame_indices': list(range(32)), 'frame_sha256': hashes}
        index.write_text(json.dumps(row) + '\n')
        table = dict(chair=['sofa'], desk=['sofa'], sidewall=['sofa'], sofa=['chair'], stool=['chair'])
        confusers = root / 'table.json'
        confusers.write_text(json.dumps(table))
        return root, index, confusers, frame_root

    def test_audit_cli_emits_each_negative_kind_with_four_used_rgb_frames(self):
        from PIL import Image
        root, index, confusers, frame_root = self.audit_fixture()
        output = root / 'audit'
        result = subprocess.run([sys.executable, '-B', '-m', 'student_pilot.mdg_targets', 'audit',
                                 '--clips-jsonl', str(index), '--confusers', str(confusers), '--n', '1',
                                 '--frame-root', str(frame_root), '--out', str(output)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        with (output / 'AUDIT.csv').open() as stream:
            records = list(csv.DictReader(stream))
        self.assertEqual([r['kind'] for r in records], ['scene_absent', 'confuser'])
        self.assertEqual([r['label'] for r in records], ['stool', 'sofa'])
        for record in records:
            self.assertEqual(record['scene'], 'recording')
            self.assertEqual(record['clip'], 'full-question-id-not-the-short-name')
            with Image.open(record['sheet_path']) as sheet:
                self.assertEqual(sheet.size, (640, 528))
                for slot, f in enumerate((0, 2, 4, 7)):
                    self.assertEqual(sheet.getpixel(((slot % 2) * 320 + 10, 32 + (slot // 2) * 248 + 10)),
                                     (f * 7, 30, 80))
                self.assertLess(np.asarray(sheet)[:30].min(), 255)

    def test_audit_insufficient_and_changed_rgb_fail_clearly(self):
        root, index, confusers, frame_root = self.audit_fixture()
        table = json.loads(confusers.read_text())
        with self.assertRaisesRegex(ValueError, 'Insufficient audit negatives'):
            M.audit([index], table, frame_root=frame_root, out=root / 'too_many', n=40)
        row = json.loads(index.read_text())
        sha = row['frame_sha256'][0]
        (frame_root / 'k8pd' / sha[:2] / f'{sha}.png').write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError, 'RGB SHA256 differs'):
            M.audit([index], table, frame_root=frame_root, out=root / 'bad_rgb', n=1)


if __name__ == '__main__':
    unittest.main()
