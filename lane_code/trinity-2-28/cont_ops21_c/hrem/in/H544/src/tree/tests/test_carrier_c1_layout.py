import copy
import json
import os
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import MagicMock, patch

import numpy as np
from PIL import Image
import torch

from student_pilot import carrier_c1_data as data, carrier_c1_run as run
from student_pilot.p3_provenance import file_pin, write
from tests.test_carrier_c1 import fixture, Tokenizer


def raw_batch(groups):
    ids = torch.tensor([[2] + [v for _ in range(groups) for v in (62, 61, 63)] + [10, 11]])
    return dict(input_ids=ids, attention_mask=torch.ones_like(ids), labels=torch.full_like(ids, -100),
                mm_token_type_ids=torch.where(ids == 61, 2, 0), video_grid_thw=torch.tensor([[groups, 2, 2]]),
                pixel_values_videos=torch.randn(groups * 4, 24))


class LayoutTests(unittest.TestCase):
    def row(self, count=32):
        root = Path(tempfile.mkdtemp(prefix='c1_layout_', dir=os.environ['LANE_TEST_OUTPUT']))
        Image.new('RGB', (32, 32), (30, 40, 50)).save(root / 'rgb.png')
        pin = file_pin(root / 'rgb.png')
        indices = list(range(0, 4 * count, 4))
        return dict(qid='fixture', target='answer', student_input=dict(frames=[pin] * count,
            frame_indices=indices, timestamps=[i / 10 for i in indices], fps=10., total_num_frames=400,
            question='Pose?', options=[], recording_id='recording'))

    def test_default_spread_bytes_and_config_identity_unchanged(self):
        processor = SimpleNamespace(tokenizer=Tokenizer(), video_processor=SimpleNamespace(merge_size=2))
        raw = raw_batch(16)
        with patch('student_pilot.pose_samples.encode_row', return_value=(raw, {'native': True})) as encode:
            default, _, audit = data.encode(processor, {}, {}, 'vqa')
            explicit, _, _ = data.encode(processor, {}, {}, 'vqa', frame_layout='spread')
        self.assertEqual(encode.call_count, 2)
        self.assertEqual(audit, {'native': True})
        self.assertEqual(default.keys(), explicit.keys())
        for key in default:
            self.assertTrue(torch.equal(default[key], explicit[key]), key)
        self.assertNotIn('aux_frame_layout', default)
        cfg = dict(base_identity='fixture')
        self.assertEqual(run.identity(cfg), run.identity({**cfg, 'frame_layout': 'spread'}))
        self.assertNotEqual(run.identity(cfg), run.identity({**cfg, 'frame_layout': 'duplicate'}))
        self.assertNotEqual(run.identity({**cfg, 'frame_layout': 'paired', 'frame_pair_gap_seconds': 1}),
                            run.identity({**cfg, 'frame_layout': 'paired', 'frame_pair_gap_seconds': 2}))

    def test_duplicate_pixels_metadata_augmentation_and_masking(self):
        row = self.row()
        row.update(category='camera_pose_only', pose_sample={'augment': {'fixture': True}})
        processor = SimpleNamespace(tokenizer=Tokenizer(), video_processor=SimpleNamespace(merge_size=2))
        _, _, targets = fixture()
        def encode(processor, question, options, arrays, metadata, target, *args):
            self.assertEqual(arrays.shape, (64, 32, 32, 3))
            np.testing.assert_array_equal(arrays[::2], arrays[1::2])
            self.assertEqual(metadata.frames_indices, [i for i in range(0, 128, 4) for _ in (0, 1)])
            self.assertEqual(metadata.fps, 10.)
            self.assertEqual(metadata.total_num_frames, 400)
            self.assertEqual(target, data.READOUT_TARGET)
            return raw_batch(32), {'native': True}
        def augment(arrays, settings):
            self.assertEqual(len(arrays), 32)
            return arrays + np.arange(32, dtype=np.uint8)[:, None, None, None]
        with patch('student_pilot.pose_samples.check_sample') as check, \
             patch('student_pilot.pose_samples.augment', side_effect=augment), \
             patch('student_pilot.pose_samples.encode_frames', side_effect=encode), \
             patch.object(data, 'target_tensors', return_value=targets):
            batch, actual, audit = data.encode(processor, row, {}, 'pose', training_mode='pose_only', frame_layout='duplicate')
        check.assert_called_once_with({**row, 'target': data.READOUT_TARGET}, max_groups=32)
        self.assertIs(actual, targets)
        self.assertTrue((batch['labels'] == -100).all())
        self.assertEqual(audit['viewpoint_timestamps_seconds'], row['student_input']['timestamps'])
        self.assertEqual(len(row['student_input']['frames']), 32)

    def test_duplicate_native_video_processor_keeps_32_temporal_patches(self):
        from transformers.models.qwen3_vl.video_processing_qwen3_vl import Qwen3VLVideoProcessor
        from transformers.video_utils import VideoMetadata
        processor = Qwen3VLVideoProcessor(patch_size=16, temporal_patch_size=2, merge_size=2)
        frames = np.random.default_rng(1).integers(0, 255, (32, 32, 32, 3), dtype=np.uint8)
        arrays = np.repeat(frames, 2, axis=0)
        metadata = VideoMetadata(total_num_frames=400, fps=10., frames_indices=[4*i for i in range(32) for _ in (0, 1)])
        result = processor(videos=[arrays], video_metadata=[metadata], do_sample_frames=False,
                           do_resize=False, do_convert_rgb=False, do_normalize=False, return_tensors='pt')
        self.assertEqual(result['video_grid_thw'].tolist(), [[32, 2, 2]])
        patches = result['pixel_values_videos'].reshape(128, 3, 2, 16, 16)
        self.assertTrue(torch.equal(patches[:, :, 0], patches[:, :, 1]))
        from transformers.models.qwen3_vl.processing_qwen3_vl import Qwen3VLProcessor
        timestamps = Qwen3VLProcessor._calculate_timestamps(None, metadata.frames_indices, metadata.fps)
        self.assertEqual(timestamps, [4*i/10 for i in range(32)])

    def test_nonspread_b_appends_all_cams_ac_stay_local_and_depth_works(self):
        for layout in ('duplicate', 'paired'):
            for placement in data.PLACEMENTS:
                model, _, targets = fixture(placement=placement)
                model.frame_layout = layout
                model.auxiliary_heads.depth.config.p3['frame_layout'] = layout
                batch = data.insert_frame_carriers(raw_batch(32), Tokenizer(), carrier_placement=placement,
                                                   frame_layout=layout)
                positions = batch['aux_camera_positions'][0]
                self.assertEqual(len(positions), 32)
                visual = torch.where(batch['input_ids'][0] == 61)[0]
                if placement == data.C1_B:
                    last_patch_end = int(visual[-1])
                    self.assertEqual(positions.tolist(), list(range(last_patch_end + 1, last_patch_end + 33)))
                    self.assertTrue(torch.equal(batch['aux_camera_rope_sources'][0], visual))
                    native, _ = model.model.get_rope_index(batch['input_ids'], batch['mm_token_type_ids'],
                                                          video_grid_thw=batch['video_grid_thw'])
                    anchored = data.frame_position_ids(native, batch)
                    torch.testing.assert_close(anchored[:, 0, positions], native[:, 0, visual])
                    embeds = model.get_input_embeddings()(batch['input_ids'])
                    changed = model.carrier_embeddings(embeds, batch['aux_camera_positions'])
                    tokens = model.auxiliary_heads.pose.tokens
                    expected = torch.cat((tokens[:1], tokens[1:].expand(31, -1)))
                    expected = expected + model.auxiliary_heads.frame_embeddings.weight
                    torch.testing.assert_close(changed[0, positions], expected)
                else:
                    self.assertTrue((batch['input_ids'][0, positions - 1] == 61).all())
                    self.assertTrue(torch.equal(batch['aux_camera_rope_sources'][0], positions - 1))
                result = model(batch, targets, return_states=True)
                self.assertEqual(result['states'].shape[1], 32)
                self.assertTrue(torch.isfinite(result['loss']))
                result['loss'].backward()
                self.assertGreater(float(model.auxiliary_heads.depth.fov.weight.grad.norm()), 0)
                model.eval().generate(batch, max_new_tokens=1, do_sample=False)
                model.frame_layout = 'spread'
                with self.assertRaisesRegex(ValueError, 'frame_layout'):
                    model(batch, targets)

    def test_nonspread_b_rope_anchors_first_token_of_multitoken_patch(self):
        ids = torch.tensor([[2] + [v for _ in range(32) for v in (62, 61, 61, 63)] + [10, 11]])
        raw = dict(input_ids=ids, attention_mask=torch.ones_like(ids), video_grid_thw=torch.tensor([[32, 2, 4]]))
        first_tokens = torch.where(ids[0] == 61)[0].reshape(32, 2)[:, 0]
        last_patch_end = int(torch.where(ids[0] == 61)[0][-1])
        for layout in ('duplicate', 'paired'):
            batch = data.insert_frame_carriers(raw, Tokenizer(), carrier_placement=data.C1_B, frame_layout=layout)
            self.assertEqual(batch['aux_camera_positions'][0].tolist(),
                             list(range(last_patch_end + 1, last_patch_end + 33)))
            self.assertTrue(torch.equal(batch['aux_camera_rope_sources'][0], first_tokens))

    def test_paired_requires_pins_recording_and_true_gap(self):
        row = self.row(4)
        with self.assertRaisesRegex(ValueError, 'prepared partner_frames'):
            data.layout_inputs(row, 'paired', 1.)
        inputs = row['student_input']
        inputs['partner_frames'] = [dict(**frame, recording_id='recording', frame_index=i + 10, timestamp=t + 1)
            for frame, i, t in zip(inputs['frames'], inputs['frame_indices'], inputs['timestamps'])]
        paired = data.layout_inputs(row, 'paired', 1., verify_partners=True)
        self.assertEqual(paired['frame_indices'], [0, 10, 4, 14, 8, 18, 12, 22])
        self.assertEqual(paired['timestamps'], [0., 1., .4, 1.4, .8, 1.8, 1.2, 2.2])
        for key, value in [('recording_id', 'other'), ('timestamp', 2.), ('frame_index', 399), ('sha256', '')]:
            bad = copy.deepcopy(row); bad['student_input']['partner_frames'][0][key] = value
            with self.assertRaisesRegex(ValueError, 'paired partner'):
                data.layout_inputs(bad, 'paired', 1.)
        for cfg in ({'frame_layout': 'bad'}, {'frame_layout': 'paired'},
                    {'frame_layout': 'paired', 'frame_pair_gap_seconds': float('nan')},
                    {'frame_layout': 'paired', 'frame_pair_gap_seconds': -1},
                    {'frame_layout': 'duplicate', 'frame_pair_gap_seconds': 1}):
            with self.assertRaises(ValueError):
                data.layout_settings(cfg)

    def test_paired_refuses_at_preparation_before_writing_receipt(self):
        row = self.row()
        pose = dict(schema='decoupled-v-preparation-v1', count=321152,
                    settings=dict(anchors=list(range(1, 33)), temporal_grouping='fused_pairs_all_frames'),
                    inputs={'division': {}}, model={'path': 'model'}, database={'path': 'database'})
        manifest = dict(kind='base', base_identity='fixture', root='/fixture/snapshot', files={'config.json': 'hash'})
        conn = MagicMock()
        conn.__enter__.return_value = conn
        conn.execute.side_effect = [SimpleNamespace(fetchone=lambda: (321152, 0, 321151)),
                                   [(json.dumps(row),)]]
        cfg = dict(streams={'pose': {'path': 'pose'}}, base_identity='fixture', frame_layout='paired', trace_program_version='3.13',
                   frame_pair_gap_seconds=1.)
        with patch.object(run, 'validate'), patch.object(run, 'authenticate', return_value='commit'), \
             patch.object(run, 'pinned', side_effect=lambda pin: pin['path']), \
             patch.object(run, 'load', side_effect=[pose, manifest]), \
             patch.object(run, 'connect', return_value=conn), patch.object(run, 'write') as write_receipt, \
             patch('student_pilot.students.get_student', return_value=dict(snapshot=Path('/snapshot'), config_sha256='hash')):
            with self.assertRaisesRegex(ValueError, 'prepared partner_frames'):
                run.prepare(cfg)
            write_receipt.assert_not_called()

    def test_rows_forward_layout_and_artifact_rejects_mismatch(self):
        root = Path(tempfile.mkdtemp(prefix='c1_layout_identity_', dir=os.environ['LANE_TEST_OUTPUT']))
        receipt = dict(streams={}, frame_layout='duplicate')
        rows = run.Rows(receipt, None)
        row = self.row()
        rows.connections['vqa'] = SimpleNamespace(execute=lambda *args: SimpleNamespace(fetchone=lambda: (json.dumps(row), '{}')))
        with patch.object(data, 'encode', return_value=({}, None, {'encoded': True})) as encoder:
            self.assertEqual(rows.get('vqa', 0), ({}, None, {'encoded': True}))
            self.assertEqual(encoder.call_args.kwargs, dict(frame_layout='duplicate', frame_pair_gap_seconds=None))
        model, _, _ = fixture()
        write(root / 'artifact.json', dict(schema='carrier-c1-artifact-v1', pose_backing='lm_final_norm',
            placement=data.C1_A, training_mode='mixed', frame_layout='duplicate'))
        with self.assertRaisesRegex(ValueError, 'differs'):
            run.load_artifact(model, file_pin(root / 'artifact.json'))
