"""Single-image pointing admission and native tiny-Qwen training, without model downloads."""
import copy
import json
import os
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock

import numpy as np
from PIL import Image
import torch

from student_pilot import carrier_c1_data as data, carrier_c1_run as run
from student_pilot.carrier_c1 import parameter_groups
from student_pilot.p3_provenance import file_pin, write
from tests.test_carrier_c1_final import final_fixture


class ImageTokenizer:
    pad_token_id, eos_token_id, eos_token = 0, 1, '<|im_end|>'
    _c1_frame_markers = True

    def __init__(self):
        self.vocab = {c: i + 10 for i, c in enumerate(sorted(set('{"point_2d": [0123456789,]}')))}
        self.vocab.update({'null': 40, '"point_2d"': 41, '<|im_end|>': 1, '<think>\n\n</think>\n\n': 2,
                           '<|vision_start|>': 62, '<|image_pad|>': 60, '<|vision_end|>': 63})
        self.inverse = {i: s for s, i in self.vocab.items()}

    def encode(self, text, **kwargs):
        ids = []
        while text:
            token = next(s for s in sorted(self.vocab, key=len, reverse=True) if text.startswith(s))
            ids.append(self.vocab[token]); text = text[len(token):]
        return ids

    def decode(self, ids, **kwargs):
        return ''.join(self.inverse[int(i)] for i in ids)


class ImageProcessor:
    image_token_id = 60

    def __init__(self):
        self.tokenizer = ImageTokenizer()
        self.image_processor = SimpleNamespace(merge_size=2)
        self.messages, self.calls = [], []

    def apply_chat_template(self, messages, **kwargs):
        self.messages.append((copy.deepcopy(messages), kwargs))
        prefix = '<|vision_start|><|image_pad|><|vision_end|><think>\n\n</think>\n\n'
        return prefix if kwargs['add_generation_prompt'] else prefix + messages[-1]['content'] + '<|im_end|>\n'

    def __call__(self, **kwargs):
        self.calls.append(kwargs)
        ids = torch.tensor([self.tokenizer.encode(kwargs['text'][0])])
        return dict(input_ids=ids, attention_mask=torch.ones_like(ids),
                    mm_token_type_ids=torch.where(ids == 60, 1, 0),
                    pixel_values=torch.arange(96, dtype=torch.float32).reshape(4, 24) / 96,
                    image_grid_thw=torch.tensor([[1, 2, 2]]))


class SingleImageTests(unittest.TestCase):
    def fixture(self):
        root = Path(tempfile.mkdtemp(prefix='c1_single_image_', dir=os.environ['LANE_TEST_OUTPUT']))
        Image.new('RGB', (8, 8), (30, 40, 50)).save(root/'rgb.png')
        mask = np.zeros((8, 8), dtype=bool); mask[1:3, 4:7] = True
        np.savez(root/'mask.npz', mask=mask, absent=np.zeros_like(mask))
        frame = file_pin(root/'rgb.png')
        question = ('Point to the chair in this image. Output the point as JSON {"point_2d": [x, y]} '
                    'with integer coordinates on a 0-1000 grid. If there is no chair in the image, '
                    'output {"point_2d": null}.')
        row = dict(qid='image', dataset='d', scene='train', provenance={'input': 'single_image'},
            student_input=dict(frames=[frame], frame_indices=[7], timestamps=[.7], fps=10., total_num_frames=100,
                               question=question, options=[]),
            pointing=dict(kind='gt_instance_mask', frame=1, rgb_sha256=frame['sha256'],
                          instance_id='chair', mask=file_pin(root/'mask.npz')))
        absent = copy.deepcopy(row); absent['qid'] = 'absent'
        absent['pointing'].update(kind='gt_absent', label='chair', key='absent')
        video = copy.deepcopy(row); video['qid'] = 'video'; video.pop('provenance')
        video['student_input'].update(frames=[frame]*32, frame_indices=list(range(32)),
                                     timestamps=[i / 10 for i in range(32)], question='Point to the chair in frame 1.')
        write(root/'division.json', dict(schema='diagnostic-whole-scene-division-v1', training_only=True,
                                       train_scenes=['d/train'], heldout_scenes=['d/held']))
        return root, [row, absent, video]

    def build(self, root, rows, name='built', stream='pointing'):
        source = root/(name+'.jsonl')
        source.write_text(''.join(json.dumps(row)+'\n' for row in rows))
        return data.build_stream(file_pin(source), file_pin(root/'division.json'), root/name, stream)

    def test_mixed_stream_and_image_rows_train_with_decision_weights(self):
        root, source = self.fixture()
        receipt = self.build(root, source)
        self.assertEqual((receipt['count'], receipt['heldout_overlap'], receipt['gt_masks_only']), (3, 0, True))
        processor = ImageProcessor()
        rows = run.Rows(dict(streams={'pointing': receipt}, training_mode='final', frame_layout='paired',
                            frame_pair_gap_seconds=1., pointing_weights=dict(decision=5., row_mean=2.)), processor)
        try:
            for placement in data.PLACEMENTS:
                model, _, _ = final_fixture(placement)
                model.frame_layout = 'paired'
                for index in (0, 1):
                    with self.subTest(placement=placement, kind=source[index]['pointing']['kind']):
                        rows.placement = placement
                        batch, targets, audit = rows.get('pointing', index)
                        self.assertIsNone(targets)
                        self.assertEqual(audit['frame_count'], 1)
                        self.assertTrue({'pixel_values', 'image_grid_thw'} <= set(batch))
                        self.assertFalse(any('video' in k or 'camera' in k or 'carrier' in k for k in batch))
                        self.assertEqual(set(processor.calls[-1]), {'text', 'images', 'return_tensors'})
                        np.testing.assert_array_equal(np.asarray(processor.calls[-1]['images'][0]), np.full((8, 8, 3), [30, 40, 50]))
                        for messages, kwargs in processor.messages[-2:]:
                            self.assertEqual(messages[0], {'role': 'user', 'content': [{'type': 'image'},
                                {'type': 'text', 'text': source[index]['student_input']['question']}]})
                            self.assertIs(kwargs['enable_thinking'], False)
                        self.assertEqual(processor.calls[-1]['text'][0], processor.tokenizer.decode(
                            batch['input_ids'][0, :audit['prompt_tokens']]))
                        positions = batch['labels'][0] != -100
                        text = processor.tokenizer.decode(batch['labels'][0, positions])
                        target, _ = data.mask_target(source[index]['pointing']['mask'],
                            source[index]['pointing'].get('key', 'mask'), source[index]['pointing']['kind'])
                        self.assertEqual(text, target + processor.tokenizer.eos_token)
                        self.assertTrue((batch['labels'][0, :audit['prompt_tokens']] == -100).all())
                        self.assertTrue((batch['labels'][batch['attention_mask'] == 0] == -100).all())
                        weights = batch['aux_token_weights'][0, positions]
                        tokens = batch['labels'][0, positions]
                        self.assertEqual(processor.tokenizer.decode([tokens[weights.argmax()]]), '[' if index == 0 else 'null')
                        self.assertAlmostEqual(float(weights.max() / weights.min()), 5.)
                        self.assertAlmostEqual(float(weights.mean()), 2., places=5)
                        self.assertTrue((batch['aux_token_weights'][0, ~positions] == 0).all())
                        self.assertTrue((batch['aux_segments'][0, ~positions] == -1).all())
                        run.check_row(batch, targets, 'pointing', model)
                        model.zero_grad(set_to_none=True)
                        with mock.patch.object(model.auxiliary_heads.pose, 'loss', side_effect=AssertionError('pose')), \
                             mock.patch.object(model.auxiliary_heads.depth, 'forward', side_effect=AssertionError('depth')):
                            result = model(batch, targets, stream='pointing')
                            result['loss'].backward()
                        self.assertTrue(torch.isfinite(result['loss']))
                        self.assertGreater(float(result['components']['pointing']), 0.)
                        for key in ('pose', 'depth', 'depth_fov'):
                            self.assertEqual(float(result['components'][key]), 0.)
                        self.assertTrue(any(p.grad is not None and p.grad.abs().sum() > 0 for p in model.model.language_model.parameters()))
                        self.assertTrue(all(p.grad is None or not p.grad.any() for p in model.auxiliary_heads.parameters()))
                        self.assertIn('pointing_null' if index else 'pointing_coord', result['metrics']['segments'])
        finally:
            rows.close()

    def test_video_encoding_is_exactly_the_existing_encoder_plus_carriers(self):
        _, source = self.fixture()
        from tests.test_carrier_c1 import Tokenizer
        processor = SimpleNamespace(tokenizer=Tokenizer(),
                                    video_processor=SimpleNamespace(merge_size=2))
        from tests.test_carrier_c1 import fixture
        _, native, _ = fixture()
        # Remove only the fixture's inserted carriers to exercise the unchanged video path.
        keep = native['input_ids'][0] != 5
        original = {k: v[:, keep].clone() if k in ('input_ids', 'labels', 'attention_mask', 'mm_token_type_ids') else v.clone()
                    for k, v in native.items() if not k.startswith('aux_')}
        for layout in ('spread', 'duplicate', 'paired'):
            with mock.patch('student_pilot.pose_samples.encode_row', return_value=(original, {'old': True})), \
                 mock.patch.object(data, 'encode_layout_row', return_value=(original, {'old': True})):
                expected = data.insert_frame_carriers(original, processor.tokenizer, frame_layout=layout)
                batch, targets, audit = data.encode(processor, source[2], {}, 'pointing', frame_layout=layout)
                self.assertEqual(set(batch), set(expected))
                for key in expected:
                    torch.testing.assert_close(batch[key], expected[key], rtol=0, atol=0)
                self.assertIsNone(targets)
                self.assertEqual(audit, {'old': True})

    def test_single_image_marker_does_not_relax_video_or_mask_guards(self):
        root, source = self.fixture()
        changes = [('unmarked', {'provenance': {}}, '32 pinned'),
                   ('wrong_frame', {'pointing': {**source[0]['pointing'], 'frame': 2}}, 'pointing.frame'),
                   ('rgb', {'pointing': {**source[0]['pointing'], 'rgb_sha256': '0'*64}}, 'provenance'),
                   ('mask', {'pointing': {**source[1]['pointing'], 'key': 'mask'}}, 'empty'),
                   ('heldout', {'scene': 'held'}, 'division')]
        for name, change, error in changes:
            with self.subTest(name=name), self.assertRaisesRegex(ValueError, error):
                self.build(root, [{**source[0], **change}], name)
        with self.assertRaisesRegex(ValueError, '32 pinned'):
            self.build(root, [source[0]], 'vqa', stream='vqa')
        for field in ('frames', 'frame_indices', 'timestamps'):
            bad = copy.deepcopy(source[0]); bad['student_input'][field] *= 2
            with self.assertRaisesRegex(ValueError, 'one aligned frame'):
                data.encode(ImageProcessor(), bad, {}, 'pointing')

    def test_optimizer_step_logs_image_grid_without_carriers(self):
        root, source = self.fixture()
        receipt = self.build(root, source[:2])
        rows = run.Rows(dict(streams={'pointing': receipt}, training_mode='final'), ImageProcessor())
        model, pose_batch, pose_targets = final_fixture()
        rows.counts['pose'] = 1
        original = rows.get
        rows.get = lambda stream, index: (pose_batch, pose_targets, {}) if stream == 'pose' else original(stream, index)
        optimizer = torch.optim.AdamW(parameter_groups(model))
        try:
            info, _ = run.optimize_step(model, optimizer, rows, [('pose', [0]), ('pointing', [0])],
                                        0, torch.device('cpu'), 1)
            self.assertEqual((info['shapes'][1]['grid'], info['shapes'][1]['carriers']), ([[1, 2, 2]], 0))
            self.assertGreater(info['stream_means']['pointing'], 0.)
        finally:
            rows.close()

    def test_prepare_skips_paired_layout_only_for_single_images(self):
        root, source = self.fixture()
        from student_pilot.p3_provenance import load
        pose = dict(schema='decoupled-v-preparation-v1', count=321152,
            settings=dict(anchors=list(range(1, 33)), temporal_grouping='fused_pairs_all_frames',
                          camera={'point_depth': {}}), inputs={'division': file_pin(root/'division.json')},
            model={'path': 'model'}, database={'path': 'pose-db'})
        codepath=root/'code.json';write(codepath,dict(schema='fixture'))
        manifest = dict(kind='base', base_identity='fixture', root='/fixture/snapshot', files={'config.json': 'hash'})
        conn = mock.MagicMock(); conn.__enter__.return_value = conn
        conn.execute.side_effect = lambda query: SimpleNamespace(fetchone=lambda: (321152, 0, 321151)) if 'count(*)' in query else []
        connect = run.connect
        for name, items in [('images', source[:2]), ('mixed', source)]:
            receipt = self.build(root, items, name)
            cfg = dict(streams={'pose': {'path': 'pose'}, 'pointing': file_pin(root/name/'receipt.json')},
                code=file_pin(codepath), base_identity='fixture', trace_program_version='3.13', frame_layout='paired', frame_pair_gap_seconds=1.,
                preparation_output=str(root/(name+'_prepared')), carrier_placement=data.C1_A, recipe={})
            with mock.patch.object(run, 'validate'), mock.patch.object(run, 'authenticate', return_value='commit'), \
                 mock.patch.object(run, 'pinned', side_effect=lambda pin: pin['path']), \
                 mock.patch.object(run, 'load', side_effect=lambda path: {'pose': pose, 'model': manifest}.get(str(path)) or load(path)), \
                 mock.patch.object(run, 'connect', side_effect=lambda pin: conn if pin['path'] == 'pose-db' else connect(pin)), \
                 mock.patch('student_pilot.students.get_student', return_value=dict(snapshot=Path('/snapshot'), config_sha256='hash')):
                if name == 'images':
                    prepared = run.prepare(cfg)
                    self.assertEqual(prepared['streams']['pointing']['count'], 2)
                else:
                    with self.assertRaisesRegex(ValueError, 'prepared partner_frames'):
                        run.prepare(cfg)

    def test_image_batch_checks_reject_video_carriers_and_missing_labels(self):
        root, source = self.fixture()
        receipt = self.build(root, source[:1])
        rows = run.Rows(dict(streams={'pointing': receipt}, training_mode='final'), ImageProcessor())
        try:
            batch, _, _ = rows.get('pointing', 0)
            for change in ({'video_grid_thw': torch.tensor([[1, 2, 2]])},
                           {'pixel_values_videos': torch.zeros(4, 24)},
                           {'aux_camera_positions': torch.zeros(1, 32)},
                           {'image_grid_thw': torch.tensor([[2, 2, 2]])},
                           {'labels': torch.full_like(batch['labels'], -100)}):
                with self.assertRaises(ValueError):
                    run.check_row({**batch, **change}, None, 'pointing', None)
            with self.assertRaises(ValueError):
                run.check_row(batch, {}, 'pointing', None)
        finally:
            rows.close()


if __name__ == '__main__':
    unittest.main()
