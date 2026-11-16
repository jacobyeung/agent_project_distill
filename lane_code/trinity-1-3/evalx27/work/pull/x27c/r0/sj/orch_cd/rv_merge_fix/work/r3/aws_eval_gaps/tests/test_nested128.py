"""CPU contracts for nested 96–192-frame evaluation cells."""
import json
from pathlib import Path
import subprocess
import sys
import tarfile
import unittest
from unittest.mock import patch

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'evaluator'), str(ROOT/'local')]
from cells import FRAME_COUNTS, frame_count, validate_token_budget
from common import save, sha
from evalpath.sampling import _sample_floor_uniform_indices
from media import decode, frame_list, identity, item_key, kwargs, load, pixel_digest
from nested_sampling import nested_indices, sample_nested_video
import test_nested64 as legacy
from test_frames import video


def cell(count):
    return {**legacy.NESTED, 'model': 't0m800', 'benchmarks': ['official5130'],
            'frames': count, 'frame_set': 'uniform' if count==96 else 'nested'}


class Nested128(unittest.TestCase):
    def test_nested_supersets_in_source_and_insertion_order(self):
        for total in (96, 97, 128, 200, 1000, 4096):
            with self.subTest(total=total):
                previous = []
                insertion_order = []
                reference = _sample_floor_uniform_indices(total, 32)
                for count in FRAME_COUNTS:
                    if count > total:
                        with self.assertRaisesRegex(ValueError, f'need {count}'):
                            nested_indices(total, count)
                        continue
                    while len(reference) < count:
                        slot = max(range(len(reference)-1),
                                   key=lambda i: reference[i+1]-reference[i])
                        reference.insert(slot+1, sum(reference[slot:slot+2])//2)
                    indices = nested_indices(total, count)
                    self.assertEqual(indices, reference)
                    self.assertEqual(len(indices), count)
                    self.assertEqual(indices, sorted(set(indices)))
                    self.assertEqual([i for i in indices if i in set(previous)], previous)
                    additions = [i for i in indices if i not in set(previous)]
                    extended = insertion_order + additions
                    self.assertEqual(extended[:len(insertion_order)], insertion_order)
                    self.assertEqual(set(extended), set(indices))
                    anchors = _sample_floor_uniform_indices(total, 32)
                    slots = [indices.index(i) for i in anchors]
                    self.assertEqual([indices[i] for i in slots], anchors)
                    previous, insertion_order = indices, extended

    def test_default_64_is_byte_identical_to_original_algorithm(self):
        for total in (64, 65, 94, 96, 97, 125, 128, 200, 1000, 4096):
            original = _sample_floor_uniform_indices(total, 32)
            while len(original) < 64:
                slot = max(range(len(original)-1), key=lambda i: original[i+1]-original[i])
                a, b = original[slot:slot+2]
                original.insert(slot+1, (a+b)//2)
            self.assertEqual(json.dumps(nested_indices(total)).encode(),
                             json.dumps(original).encode())

    def test_short_sources_and_blocked_gaps_report_requested_count(self):
        for count in FRAME_COUNTS:
            for total in (0, 31, count-1):
                with self.subTest(count=count, total=total), \
                     self.assertRaisesRegex(ValueError, f'need {count}'):
                    nested_indices(total, count)
        with patch('nested_sampling._sample_floor_uniform_indices', return_value=[0]*32):
            with self.assertRaisesRegex(ValueError, 'need 96'):
                nested_indices(200, 96)
        for count in (0, 16, 31, True, 64.0, '96'):
            with self.assertRaises(ValueError):
                nested_indices(200, count)

    def test_frame_count_acceptance_and_rejection(self):
        for count in FRAME_COUNTS:
            for benchmarks in (['vsi500'], ['vsi500_slice'], ['devrows'], ['official5130'],
                               ['vsi500', 'official5130', 'devrows']):
                value = {**cell(count), 'benchmarks': benchmarks}
                if count == 32:
                    value.pop('frame_set')
                self.assertEqual(frame_count(value), count)
            if count > 32:
                for benchmarks in ([], ['revsi'], ['pointing'], ['pointing_video'],
                                   ['official5130', 'revsi']):
                    with self.assertRaisesRegex(ValueError, f'frames={count}'):
                        frame_count({**cell(count), 'benchmarks': benchmarks})
                for layout in ('duplicate', 'paired', 'P0.2', 'P0.5'):
                    with self.assertRaisesRegex(ValueError, f'frames={count}'):
                        frame_count({**cell(count), 'layout': layout})
            if count > 64:
                value = cell(count)
                value.pop('frame_set')
                with self.assertRaisesRegex(ValueError, 'frame_set'):
                    frame_count(value)
                for frame_set in (('nested', None, False) if count==96 else ('uniform', None, False)):
                    with self.assertRaisesRegex(ValueError, 'frame_set'):
                        frame_count({**value, 'frame_set': frame_set})
        for count in (100, True, 128.0, '128'):
            with self.assertRaisesRegex(ValueError, 'frames'):
                frame_count(cell(count))
        value = cell(64)
        value.pop('frame_set')
        self.assertEqual(frame_count(value), 64)

    def test_token_budget_arithmetic_and_context_rejection(self):
        expected = (22592, 26752, 30912, 35072, 39232, 43392)
        for count, required in zip(FRAME_COUNTS, expected):
            self.assertEqual(validate_token_budget(cell(count)), required)
            self.assertEqual(required, count*130 + 16384 + 2048)
            self.assertLessEqual(required, 49152)
        self.assertEqual(validate_token_budget(cell(192), context_limit=43392), 43392)
        with self.assertRaisesRegex(ValueError, '43392.*43391'):
            validate_token_budget(cell(192), context_limit=43391)

    def test_decode_count_pixels_anchor_slots_and_pixel_kwargs(self):
        root = legacy.retained()
        path = root/'source.mp4'
        video(path, 200, 10)
        task = dict(benchmark='official5130', video_path=str(path))
        anchors, original_audit = decode(task, 'spread')
        for count in (64,128,160,192):
            arrays, audit = decode(task, 'spread', count, 'nested')
            selected, indices, fps, total = sample_nested_video(task, count=count)
            self.assertEqual((len(arrays), total, fps), (count, 200, 10.))
            self.assertEqual(indices, nested_indices(200, count))
            self.assertEqual(audit['metadata']['frames_indices'], indices)
            self.assertEqual(audit['anchor_indices'], indices)
            slots = audit['anchor_slots']
            self.assertEqual(len(slots), 32)
            self.assertEqual([indices[i] for i in slots], original_audit['anchor_indices'])
            np.testing.assert_array_equal(arrays[slots], anchors)
            np.testing.assert_array_equal(arrays, selected)
            self.assertEqual(frame_list(indices, fps, total, 'spread', count), (indices, []))
            if count != 64:
                with self.assertRaises(ValueError):
                    frame_list(indices, fps, total, 'duplicate', count)
            self.assertEqual(kwargs(count)['size'],
                             dict(shortest_edge=count*128**2, longest_edge=count*384**2))

    def test_load_checks_exact_requested_count_with_synthetic_png_receipt(self):
        task = dict(benchmark='official5130', example_id='png', video_path='/unavailable')
        for count in FRAME_COUNTS[1:]:
            for array_count, anchor_count in ((count, count), (count-1, count), (count, count-1)):
                with self.subTest(count=count, arrays=array_count, anchors=anchor_count):
                    root = legacy.retained()
                    image = np.zeros((4, 6, 3), dtype=np.uint8)
                    Image.fromarray(image).save(root/'frame.png')
                    indices = nested_indices(200, count)
                    arrays = np.repeat(image[None], array_count, axis=0)
                    audit = dict(anchor_indices=indices[:anchor_count],
                                 anchor_slots=[indices.index(i) for i in nested_indices(200, 32)],
                                 metadata=dict(frames_indices=indices[:array_count], height=4, width=6),
                                 pixel_sha256=pixel_digest(arrays))
                    receipt = dict(identity=identity(task, 'spread', count, 'uniform' if count==96 else 'nested'), audit=audit,
                                   frames=[dict(path='frame.png', sha256=sha(root/'frame.png'), index=i)
                                           for i in indices[:array_count]])
                    save(root/'receipt.json', receipt)
                    save(root/'0.json', dict(items={item_key(task, 'spread', count, 'uniform' if count==96 else 'nested'):
                         dict(path='receipt.json', sha256=sha(root/'receipt.json'))}))
                    with patch.dict(sys.modules, {'av': None}):
                        if array_count == anchor_count == count:
                            loaded, report = load(task, 'spread', root, sha(root/'0.json'), count, 'uniform' if count==96 else 'nested')
                            np.testing.assert_array_equal(loaded, arrays)
                            self.assertEqual(report['anchor_slots'], audit['anchor_slots'])
                        else:
                            with self.assertRaisesRegex(ValueError, f'exactly {count} staged anchors'):
                                load(task, 'spread', root, sha(root/'0.json'), count, 'uniform' if count==96 else 'nested')

    def test_official128_build_only_cli_bind_round_trip(self):
        root = legacy.retained()
        cells = [cell(128)]
        save(root/'cells.json', cells)
        models = json.loads((ROOT/'inputs/MODELS.json').read_text())
        models['t0m800'] = dict(kind='archive', path='/review/t0m800.tar', sha256='0'*64)
        save(root/'models.json', models)
        command = [sys.executable, '-I', '-s', '-B', str(ROOT/'local/bind_vl.py'), '--preset', 'custom',
                   '--cells', str(root/'cells.json'), '--models', str(root/'models.json'),
                   '--gpu-cap', '8', '--build-only', '--artifact-dir', str(root/'bind')]
        result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, check=False)
        self.assertEqual(result.returncode, 0, result.stdout+result.stderr)
        request = json.loads((root/'bind/inputs/REQUEST.json').read_text())
        self.assertEqual(request['cells'], cells)
        self.assertEqual((request['max_tokens'], request['max_model_len']), (16384, 49152))
        self.assertTrue(request['build_only'])
        self.assertEqual(request['datasets'][0]['benchmark'], 'official5130')
        with tarfile.open(root/'bind/kit/k/1.tar') as archive:
            self.assertEqual(json.load(archive.extractfile('0.json')), request)
        # The CLI must enforce the actual context selected by the caller.
        rejected = subprocess.run(command+['--max-model-len', '32768'], cwd=ROOT,
                                  capture_output=True, text=True, check=False)
        self.assertNotEqual(rejected.returncode, 0)
        self.assertIn('Cell token budget needs 35072', rejected.stderr)


if __name__ == '__main__':
    unittest.main()
