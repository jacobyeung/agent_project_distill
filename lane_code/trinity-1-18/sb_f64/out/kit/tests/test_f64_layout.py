"""Nested 64-viewpoint input: rows, anchor-only markers and depth view, pose check, config keys,
and agreement between the training and read frame layouts."""
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import torch

from student_pilot import frame_input as F
from student_pilot.carrier_c1_data import nested_indices

T, FPS = 368, 24.0
ANCHORS = [i * (T - 1) // 31 for i in range(32)]


def pin(k, root='/frames'):
    return {'path': f'{root}/{k:05d}.png', 'sha256': f'{k:064x}'}


def row32(anchors=ANCHORS, root='/frames'):
    return {'qid': 'q1', 'dataset': 'd1', 'scene': 's1', 'question_type': 'object_counting',
            'student_input': {'frames': [pin(k, root) for k in anchors], 'frame_indices': list(anchors),
                              'timestamps': [k / FPS for k in anchors], 'fps': FPS, 'total_num_frames': T,
                              'question': 'How many chairs are in frame 3 of 32?', 'options': []}}


def bisection_pins(anchors=ANCHORS, root='/frames'):
    indices, _ = nested_indices(anchors, 64)
    return {k: pin(k, root) for k in indices if k not in set(anchors)}


class NestedRows(unittest.TestCase):
    def test_nest_row_keeps_anchors_and_follows_the_rule(self):
        source = row32()
        source['student_input']['timestamps'][5] += 0.004
        si = F.nest_row(source, bisection_pins())['student_input']
        indices, slots = nested_indices(ANCHORS, 64)
        self.assertEqual((si['frame_indices'], si['anchor_slots']), (indices, slots))
        self.assertEqual(len(si['frames']), 64)
        self.assertEqual([si['frames'][s] for s in slots], source['student_input']['frames'])
        self.assertEqual([si['timestamps'][s] for s in slots], source['student_input']['timestamps'])
        self.assertEqual(si['timestamps'][1], indices[1] / FPS)
        F.check_row({'student_input': si}, F.NESTED)

    def test_missing_frames_short_clips_and_double_nesting_refuse(self):
        pins = bisection_pins()
        dropped = sorted(pins)[7]
        del pins[dropped]
        with self.assertRaisesRegex(ValueError, f'FRAME_INPUT_DENSE_FRAME_MISSING:{dropped}'):
            F.nest_row(row32(), pins)
        with self.assertRaisesRegex(ValueError, 'FRAME_INPUT_CLIP_TOO_SHORT'):
            F.nest_row(row32(list(range(32))), {})
        nested = F.nest_row(row32(), bisection_pins())
        with self.assertRaisesRegex(ValueError, 'FRAME_INPUT_SOURCE_NOT_32'):
            F.nest_row(nested, bisection_pins())

    def test_check_row_and_spec_refusals(self):
        nested = F.nest_row(row32(), bisection_pins())
        with self.assertRaisesRegex(ValueError, 'FRAME_INPUT_NESTED_ROW_UNDECLARED'):
            F.check_row(nested, None)
        with self.assertRaisesRegex(ValueError, 'FRAME_INPUT_ROW_NOT_NESTED'):
            F.check_row(row32(), F.NESTED)
        F.check_row(row32(), None)
        F.check_row({'student_input': {'frames': [pin(0)]}}, F.NESTED)
        bent = F.nest_row(row32(), bisection_pins())
        bent['student_input']['frame_indices'][1] += 1
        with self.assertRaisesRegex(ValueError, 'FRAME_INPUT_ROW_RULE_DIFFERS'):
            F.check_row(bent, F.NESTED)
        for bad in ({'viewpoints': 48, 'anchors': 32, 'rule': 'nested_bisection_v1'}, {'viewpoints': 64}):
            with self.assertRaisesRegex(ValueError, 'FRAME_INPUT_UNSUPPORTED'):
                F.check_spec(bad)
        self.assertIsNone(F.check_spec(None))


class AnchorOnlyLayout(unittest.TestCase):
    class Tok:
        _c1_frame_markers = True
        _c1_frame_input = F.NESTED

        def encode(self, text, **kwargs):
            if not text.startswith('Frame '):
                return [5]
            return [40, 100 + int(text.split()[1].rstrip(':'))]

        def convert_tokens_to_ids(self, token):
            return {'<|fim_middle|>': 5, '<|vision_start|>': 62}.get(token, 61)

    def batch(self, groups):
        ids = torch.tensor([[2] + [v for _ in range(groups) for v in (62, 61, 63)] + [10, 11, 12]])
        batch = dict(input_ids=ids, attention_mask=torch.ones_like(ids), labels=torch.full_like(ids, -100),
                     mm_token_type_ids=torch.where(ids == 61, 2, 0), video_grid_thw=torch.tensor([[groups, 2, 2]]))
        batch['labels'][0, -2:] = ids[0, -2:]
        return batch

    def test_markers_and_carriers_sit_on_anchor_groups_numbered_by_anchor(self):
        from student_pilot.carrier_c1_data import insert_frame_carriers
        _, slots = nested_indices(ANCHORS, 64)
        out = insert_frame_carriers(self.batch(64), self.Tok(), carrier_placement='append_after_temporal_group_video_tokens_v1',
                                    frame_layout='duplicate', anchors=slots)
        seq = out['input_ids'][0].tolist()
        anchor_of = {g: k for k, g in enumerate(slots, 1)}
        expected = [2] + [v for g in range(64) for v in ((40, 100 + anchor_of[g], 62, 61, 5, 63) if g in anchor_of
                                                         else (62, 61, 63))] + [10, 11, 12]
        self.assertEqual(seq, expected)
        self.assertEqual(out['aux_anchor_groups'][0].tolist(), slots)
        self.assertEqual(len(out['aux_camera_positions'][0]), 32)
        self.assertEqual(out['labels'][0, -2:].tolist(), [11, 12])

    def test_depth_view_reads_only_anchor_patches(self):
        t, h, w = 64, 2, 3
        _, slots = nested_indices(ANCHORS, 64)
        pixels = torch.arange(t * h * w, dtype=torch.float32)[:, None].repeat(1, 4)
        batch = dict(pixel_values_videos=pixels, video_grid_thw=torch.tensor([[t, h, w]]),
                     aux_anchor_groups=torch.tensor([slots]))
        view = F.anchor_view(batch)
        self.assertEqual(view['video_grid_thw'].tolist(), [[32, h, w]])
        self.assertEqual(view['pixel_values_videos'][:, 0].long().tolist(),
                         [g * h * w + i for g in slots for i in range(h * w)])
        every = dict(batch, aux_anchor_groups=torch.tensor([list(range(t))]))
        self.assertIs(F.anchor_view(every), every)
        with self.assertRaisesRegex(ValueError, 'FRAME_INPUT_ANCHOR_VIEW_SHAPE'):
            F.anchor_view(dict(batch, pixel_values_videos=pixels[:-1]))

    def test_pose_sample_keeps_the_anchor_record(self):
        from student_pilot.camera_targets import trajectory_scale
        from student_pilot.pose_samples import AUGMENT, CATEGORY, SCHEMA, check_sample
        camera = [[0.02 * i, 0., 0.01 * i, 0., 0., 0., 1., 1.0, 1.25] for i in range(32)]
        sample = dict(schema=SCHEMA, recording=dict(sampling=dict(variant='all_frames32')), frames=32,
                      positions=list(range(32)), temporal_grouping='fused_pairs_all_frames', anchors=list(range(1, 33)),
                      augment={**AUGMENT, 'seed': 17}, metric=True, camera=camera, camera_mask=[True] * 32,
                      trajectory_scale=trajectory_scale(camera, [True] * 32), gravity=[0., -1., 0.], gravity_mask=True)
        row = dict(row32(), category=CATEGORY, pose_sample=sample)
        expected = check_sample(row, max_groups=32)
        self.assertEqual(check_sample(F.nest_row(row, bisection_pins()), max_groups=32), expected)
        dense = F.nest_row(row, bisection_pins())
        del dense['student_input']['anchor_slots']
        with self.assertRaisesRegex(ValueError, 'frame count disagrees'):
            check_sample(dense, max_groups=32)


class ConfigKeys(unittest.TestCase):
    def test_b7_layout_carries_frame_input_only_with_32_slots(self):
        from student_pilot.b7_inputs import layout
        base = dict(frame_count=32, frame_layout='duplicate', frame_markers=True, max_pixels=384 * 384, min_pixels=128 * 128)
        self.assertNotIn('frame_input', layout(base))
        self.assertEqual(layout(dict(base, frame_input=F.NESTED))['frame_input'], F.NESTED)
        with self.assertRaisesRegex(ValueError, 'nested_frame_input_requires_32_slots'):
            layout(dict(base, frame_count=64, frame_input=F.NESTED))
        with self.assertRaisesRegex(ValueError, 'FRAME_INPUT_UNSUPPORTED'):
            layout(dict(base, frame_input={'viewpoints': 64}))

    def test_handover_names_frame_input_and_reads_null_pixels_as_defaults(self):
        from student_pilot import r1_handover as H
        self.assertIn('frame_input', H.HANDOVER_ROW_KEYS)
        self.assertEqual((H.EFFECTIVE_DEFAULTS['max_pixels'], H.EFFECTIVE_DEFAULTS['min_pixels']), (384 * 384, 128 * 128))


def reader_root():
    root = os.environ.get('F64_READER_ROOT')
    return Path(root) if root else None


@unittest.skipUnless(reader_root(), 'F64_READER_ROOT names the patched reader (e2e_reader, parity_kit, f64_read)')
class TrainingReadAgreement(unittest.TestCase):
    """The reader's student row equals the training row for one clip, and the layout check binds the export."""

    @classmethod
    def setUpClass(cls):
        sys.path.insert(0, str(reader_root()))
        import f64_read
        from e2e_reader import parity
        cls.f64_read, cls.parity = f64_read, parity

    def capture(self, root):
        return {'native': 'd1/s1', 'anchor_indices': list(ANCHORS), 'timestamps': [k / FPS for k in ANCHORS],
                'fps': FPS, 'total_num_frames': T,
                'frames': [dict(index=k, path=f'{k:05d}.png', sha256=pin(k)['sha256']) for k in ANCHORS]}

    def read_row(self, root):
        capture = self.capture(root)
        task = {'id': 'q1', 'dataset': 'd1', 'scene': 's1', 'question_type': 'object_counting',
                'question': row32()['student_input']['question'], 'options': []}
        row = self.parity.trainer_row(task, capture, root, verify=False)
        plan = self.f64_read.plan_manifest({'captures': [capture]})['captures']['d1/s1']
        plan['pins'] = {str(k): pin(k, root) for k in plan['decode']}
        return self.f64_read.student_row(row, capture, plan)

    def test_student_frames_match_training_rows(self):
        root = '/scratch/frames'
        train = F.nest_row(row32(root=root), bisection_pins(root=root))['student_input']
        read = self.read_row(root)['student_input']
        for key in ('frame_indices', 'anchor_slots', 'timestamps', 'fps', 'total_num_frames'):
            self.assertEqual(read[key], train[key], key)
        self.assertEqual([f['sha256'] for f in read['frames']], [f['sha256'] for f in train['frames']])
        self.assertEqual(read['video_identity']['kind'], 'devS1-pinned-PNG-clip-nested64-v1')

    def test_layout_check_binds_the_export(self):
        R = self.f64_read
        artifact = {'frame_layout': 'duplicate', 'frame_input': F.NESTED}
        trained = R.training_layout(artifact, {'frame_count': 32, 'frame_input': F.NESTED})
        self.assertEqual(R.check_layout(R.READ_FRAMES, trained)['matches_training'], True)
        old = R.training_layout({'frame_layout': 'duplicate'}, {'frame_count': 32})
        with self.assertRaisesRegex(ValueError, 'read_frame_layout_differs_from_training'):
            R.check_layout(R.READ_FRAMES, old)
        with self.assertRaisesRegex(ValueError, 'read_frame_layout_differs_from_training'):
            R.check_layout(dict(layout='duplicate', count=32), trained)
        with self.assertRaisesRegex(ValueError, 'export_frame_input_differs_from_config'):
            R.training_layout(artifact, {'frame_count': 32, 'frame_input': dict(F.NESTED, viewpoints=48)})

    def test_manifest_entry_must_follow_the_rule(self):
        root = '/scratch/frames'
        capture = self.capture(root)
        plan = self.f64_read.plan_manifest({'captures': [capture]})['captures']['d1/s1']
        with self.assertRaisesRegex(ValueError, 'lacks decoded frames'):
            self.f64_read.check_manifest_entry(capture, dict(plan, pins={}))
        bent = dict(plan, frame_indices=[*plan['frame_indices'][:-1], plan['frame_indices'][-1] - 1])
        with self.assertRaisesRegex(ValueError, 'differs from the nesting rule'):
            self.f64_read.check_manifest_entry(capture, bent)


@unittest.skipUnless(reader_root() and os.environ.get('F64_META') and os.environ.get('F64_CONFIG'),
                     'F64_META and F64_CONFIG name the real processor files and the 64-frame config')
class EncodedAgreement(unittest.TestCase):
    """Training encode (data.encode, as Rows.get) and read encode (canary.prompt_batch, as the reader)
    produce the same video, markers, carriers and anchor groups for one clip."""

    def test_encoded_frames_agree(self):
        import numpy as np
        from PIL import Image
        from student_pilot import carrier_c1_data as data
        from student_pilot.carrier_c1_canary import prompt_batch
        from student_pilot.carrier_c1_run import processor_for_receipt
        sys.path.insert(0, str(reader_root()))
        import f64_read
        from e2e_reader import parity
        cfg = json.loads(Path(os.environ['F64_CONFIG']).read_text())
        receipt = {k: cfg[k] for k in ('frame_layout', 'frame_pair_gap_seconds', 'r1_training', 'frame_count',
                                       'frame_input', 'max_pixels', 'min_pixels', 'frame_markers') if k in cfg}
        processor = processor_for_receipt({'root': os.environ['F64_META']}, receipt)
        with tempfile.TemporaryDirectory() as tmp:
            indices, _ = nested_indices(ANCHORS, 64)
            rng = np.random.default_rng(3)
            for k in indices:
                Image.fromarray(rng.integers(0, 255, (96, 128, 3), dtype=np.uint8)).save(f'{tmp}/{k:05d}.png')
            real = lambda k: {'path': f'{tmp}/{k:05d}.png', 'sha256': __import__('hashlib').sha256(
                Path(f'{tmp}/{k:05d}.png').read_bytes()).hexdigest()}
            source = row32(root=tmp)
            source['student_input']['frames'] = [real(k) for k in ANCHORS]
            train_row = F.nest_row(source, {k: real(k) for k in indices if k not in ANCHORS})
            capture = {'native': 'd1/s1', 'anchor_indices': list(ANCHORS), 'timestamps': [k / FPS for k in ANCHORS],
                       'fps': FPS, 'total_num_frames': T,
                       'frames': [dict(index=k, path=f'{k:05d}.png', sha256=real(k)['sha256']) for k in ANCHORS]}
            task = {'id': 'q1', 'dataset': 'd1', 'scene': 's1', 'question_type': 'object_counting',
                    'question': source['student_input']['question'], 'options': []}
            plan = f64_read.plan_manifest({'captures': [capture]})['captures']['d1/s1']
            plan['pins'] = {str(k): real(k) for k in plan['decode']}
            read_row = f64_read.student_row(parity.trainer_row(task, capture, tmp, verify=True), capture, plan)
            layout, gap = data.layout_settings(cfg)
            with mock.patch('student_pilot.r0_exclusion.reserve') as reserve:
                reserve.return_value.check.return_value = None
                train, _, _ = data.encode(processor, {**train_row, 'target': 'A'}, {}, 'vqa', cfg['carrier_placement'],
                                          'final', frame_layout=layout, frame_pair_gap_seconds=gap)
                read = prompt_batch(processor, read_row, cfg)
        cut = read['input_ids'].shape[1]
        self.assertEqual(train['input_ids'][0, :cut].tolist(), read['input_ids'][0].tolist())
        for key in ('video_grid_thw', 'pixel_values_videos', 'aux_camera_positions', 'aux_anchor_groups'):
            self.assertTrue(torch.equal(train[key], read[key]), key)
        self.assertEqual(train['video_grid_thw'].tolist()[0][0], 64)


if __name__ == '__main__':
    unittest.main()
