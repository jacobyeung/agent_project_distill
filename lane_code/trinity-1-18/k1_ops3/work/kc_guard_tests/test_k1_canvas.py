"""CPU canvas tests using pinned GT and real converted candidate features."""
import importlib.util
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
import numpy as np

ROOT = Path(__file__).resolve().parent
WORK = ROOT.parent / 'kc_guard/k1_build/work/kit_k1a/work'
sys.path.insert(0, str(WORK))
import k1_pipeline as K
K._native()
B = K.B
import k1_guard as guard
import build_tables as T
from student_pilot import routed_features as F
guard.install()
M = B.load(ROOT.parent / 'manifest_v2/a40fbc19.json')
CAPTURES = {c['canonical']: c for c in M['captures']}
CACHE = Path('/scratch/jjyeung/k1/run_convert_2')
OUT = ROOT / 'patch3_canvas'
OUT.mkdir()
EVIDENCE = {}


def raw_gt(c):
    with np.load(B.checked(c['gt']), allow_pickle=False) as z:
        return dict(instances=z['instances'] if 'instances' in z else z['inst'], frame_indices=z['frame_indices'])


class CanvasTests(unittest.TestCase):
    def test_real_portrait_every_frame_every_label(self):
        c = CAPTURES['arkitscenes/41048124']
        source = raw_gt(c)['instances']
        actual, mapping = K.gt_canvas(source)
        self.assertEqual(mapping, 'stretch_nearest_320x240_to_240x320')
        self.assertEqual(actual.dtype, source.dtype)
        checks = 0
        for before, after in zip(source, actual, strict=True):
            union = np.empty_like(after)
            covered = np.zeros(F.OUTPUT_SHAPE, bool)
            for label in np.unique(before):
                mask = F.resize(before == label, F.OUTPUT_SHAPE)
                np.testing.assert_array_equal(after == label, mask)
                self.assertFalse(np.any(covered & mask))
                union[mask] = label
                covered |= mask
                checks += 1
            self.assertTrue(covered.all())
            self.assertEqual(after.tobytes(), union.tobytes())
        EVIDENCE['portrait'] = dict(frames=len(source), label_mask_checks=checks, dtype=str(source.dtype), union_byte_equal=True)

    def test_landscape_tables_byte_equal(self):
        c = CAPTURES['scannet/scene0452_02']
        source = raw_gt(c)
        mapped, mapping = K.gt_canvas(source['instances'])
        self.assertIs(mapped, source['instances'])
        self.assertEqual(mapping, 'identity')
        self.assertEqual(mapped.tobytes(), source['instances'].tobytes())
        spec = importlib.util.spec_from_file_location('pipeline_before_canvas', ROOT / 'patch3_before/kc_guard/k1_build/work/kit_k1a/work/k1_pipeline.py')
        before = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(before)
        before._native()
        m = dict(captures=[c], inventory=M['inventory'])
        before.tables(m, CACHE, OUT / 'landscape_before')
        K.tables(m, CACHE, OUT / 'landscape_after')
        for name in ('candidates.jsonl', 'pairs.jsonl'):
            self.assertEqual((OUT / 'landscape_before' / name).read_bytes(), (OUT / 'landscape_after' / name).read_bytes())
        EVIDENCE['landscape'] = {name: dict(sha256=B.sha(OUT / 'landscape_after' / name), rows=sum(1 for _ in (OUT / 'landscape_after' / name).open())) for name in ('candidates.jsonl', 'pairs.jsonl')}

    def test_wrong_shapes_and_noninteger_labels_halt(self):
        for shape in ((1, 240, 240), (1, 480, 640), (1, 640, 480), (1, 0, 240), (240, 320)):
            with self.subTest(shape=shape), self.assertRaises(ValueError):
                K.gt_canvas(np.zeros(shape, np.int32))
        with self.assertRaisesRegex(ValueError, 'integer'):
            K.gt_canvas(np.zeros((1, 240, 320), float))
        c = CAPTURES['arkitscenes/41048124']
        with patch.object(K.np, 'load') as load:
            load.return_value.__enter__.return_value = dict(instances=np.zeros((32, 100, 100), np.int32), frame_indices=np.array(c['anchor_indices']))
            with self.assertRaisesRegex(ValueError, 'no silent resize'):
                K.tables(dict(captures=[c], inventory=M['inventory']), CACHE, OUT / 'wrong_shape')
        self.assertFalse((OUT / 'wrong_shape/TABLE_RECEIPT.json').exists())

    def test_render_passes_mapped_gt_to_mask_agreement(self):
        # Real captures/cache/GT; fixture policy and calls isolate render plumbing.
        cs = [CAPTURES[n] for n in ('arkitscenes/41048124', 'scannet/scene0452_02')]
        m = dict(captures=cs, inventory=M['inventory'])
        fit = OUT / 'fixture_fit'; fit.mkdir()
        B.write(fit / 'NATIVE_POLICY.json', dict(fixture_only=True))
        B.write(fit / 'FIT_RECEIPT.json', dict(fixture_only=False, native_policy_sha256=B.sha(fit / 'NATIVE_POLICY.json'), inputs={M['inventory']['path']: M['inventory']['sha256']}, train_rooms=[], heldout_rooms=[]))
        expected = {c['canonical']: K.gt_arrays(c) for c in cs}
        by_row = {r['id']: c for c in cs for r in c['rows']}
        seen = []
        def agreement(record, row, gt, anchors):
            c = by_row[row['id']]
            self.assertEqual(gt['instances'].shape[1:], (240, 320))
            np.testing.assert_array_equal(gt['instances'], expected[c['canonical']]['instances'])
            self.assertEqual(anchors, c['anchor_indices'])
            seen.append(row['id'])
            return {'ok': False}
        def execute(geo, backend, calls):
            return dict(calls=[dict(call=calls[0], kind='gap', response='distance 1.00 m')])
        with patch.object(K, 'native_backend', return_value=object()), patch.object(B.perception, 'execute_calls', side_effect=execute), patch.object(K.P, 'mask_agreement', side_effect=agreement):
            K.responses(m, CACHE, fit, OUT / 'render_fixture')
        self.assertEqual(len(seen), sum(len(c['rows']) for c in cs))
        receipt = B.load(OUT / 'render_fixture/RENDER_RECEIPT.json')
        self.assertEqual(receipt['gt_canvas_map_counts'], {'identity': 1, 'stretch_nearest_320x240_to_240x320': 1})
        self.assertEqual(receipt['gt_canvas_map'], {c['canonical']: expected[c['canonical']]['gt_canvas_map'] for c in cs})
        EVIDENCE['render_fixture'] = dict(rows=len(seen), gt_canvas_map=receipt['gt_canvas_map'], counts=receipt['gt_canvas_map_counts'])


if __name__ == '__main__':
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(CanvasTests))
    (OUT / 'EVIDENCE.json').write_text(json.dumps(EVIDENCE, indent=2) + '\n')
    raise SystemExit(not result.wasSuccessful())
