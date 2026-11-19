"""Retained, offline CPU fixtures for online G3T carriers and replicated training."""
import copy
from contextlib import ExitStack
import io
import hashlib
import json
import os
import random
from pathlib import Path
import tempfile
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import numpy as np
from PIL import Image
import torch
import torch.distributed as dist
from torch.nn import functional as F

from student_pilot import g3t_online as gx, carrier_c1_data as data, carrier_c1_run as run, full_ft
from student_pilot.carrier_c1 import CarrierC1, parameter_groups, RECIPE
from student_pilot.carrier_c1_sweep import recipe_for, capped_steps
from student_pilot.carrier_c1_data import insert_frame_carriers, C1_A
from student_pilot.p3_provenance import file_pin, load, write
from tests.test_carrier_c1 import fixture, Tokenizer
from tests.test_carrier_c1_layout import raw_batch
from tests.test_fsdp import SOCKETS
from tests.retained_workers import run_workers


def settings(mode='frozen', **ft):
    return dict(schema='gx-carrier-v1', mode=mode, encoder=dict(repository=gx.REPOSITORY,
        revision=gx.REVISION, source_sha256=gx.vendor_digest(),
        weights=dict(path='/fixture/model.safetensors', sha256='a'*64),
        config=dict(path='/fixture/config.json', sha256='b'*64)), input=gx.INPUT, feature=gx.FEATURE,
        connector=dict(out_init='zero', rms_cam='warm_start_carrier_median_rms_v1', rms_scale=1.),
        finetune=(dict(lr_scale=.1, hold_steps=1, warmup_steps=2, scope='aggregator',
                       checkpointing=False, clip_norm=.25) | ft) if mode == 'finetune' else None,
        fail_fast=None)


def architecture(dino=False):
    dim = 384 if dino else 32
    return dict(aggregator=dict(img_size=28, patch_size=14, embed_dim=dim, depth=1 if dino else 2,
        num_heads=6 if dino else 4, patch_embed='dinov2_vits14_reg' if dino else 'conv'),
        head=dict(dim_in=dim*2, trunk_depth=1, num_heads=6 if dino else 4))


class TinyEncoder(gx.G3TEncoder):
    """Pad the tiny camera width to the production connector width for C1 integration."""
    def __init__(self, block):
        super().__init__(block, architecture(), image_size=28)

    def forward(self, images, coords=None):
        encoded = super().forward(images, coords)
        cam, local, global_ = encoded[:3]
        result = (F.pad(cam, (0, 2048-cam.shape[-1])), local, global_)
        if 'patch_fusion' in self.settings:
            # Keep the native aggregator graph, without allocating a production-sized teacher.
            patches = encoded[3].mean(1, keepdim=True)
            result += (F.pad(patches, (0, 2048-patches.shape[-1])).expand(-1, 37*37, -1),)
        return result


def root():
    return Path(tempfile.mkdtemp(prefix='gx_', dir=os.environ['LANE_TEST_OUTPUT']))


def configuration(mode='frozen'):
    cfg = dict(schema='carrier-c1-run-v1', trace_program_version='3.13', training_mode='pose_only', depth_enabled=False,
        frame_layout='duplicate', init='base', parallel='fsdp', all_frames=True, carrier_placement=C1_A,
        streams=dict(pose={}), steps=12, milestones=[0, 2, 12], geometry_online=settings(mode),
        schedule=dict(startup_seconds=0, p95_step_seconds=1, checkpoint_seconds=1, export_seconds=1))
    cfg['recipe'] = recipe_for(cfg)
    return cfg


def reference_pin():
    return dict(sha256='a'*64, config_sha256='b'*64, trainer_commit='verified-control')


def model_fixture(mode=None, patch_fusion=None, **ft):
    donor, _, targets = fixture(training_mode='pose_only', depth_enabled=False)
    donor.frame_layout = 'duplicate'
    batch = insert_frame_carriers(raw_batch(32), Tokenizer(), frame_layout='duplicate')
    if mode is None:
        return donor, batch, targets
    from transformers import Qwen3_5ForConditionalGeneration
    base = Qwen3_5ForConditionalGeneration(copy.deepcopy(donor.config))
    base.model.load_state_dict(donor.model.state_dict())
    base.lm_head.load_state_dict(donor.lm_head.state_dict())
    cfg = configuration(mode)
    cfg['geometry_online'] = settings(mode, **ft)
    if patch_fusion is not None:
        cfg['geometry_online']['patch_fusion'] = patch_fusion
    cfg['recipe'] = recipe_for(cfg)
    with patch.object(gx, 'G3TEncoder', TinyEncoder):
        model = CarrierC1(base, donor.auxiliary_heads.pose.settings, {}, 5,
            training_mode='pose_only', depth_enabled=False, frame_layout='duplicate', recipe=cfg['recipe'],
            geometry_online=cfg['geometry_online'], geometry_runtime=dict(image_mean=[.5]*3, image_std=[.25]*3))
    model.auxiliary_heads.pose.load_state_dict(donor.auxiliary_heads.pose.state_dict(), strict=False)
    model.trace_program_version = cfg['trace_program_version']
    model.auxiliary_heads.pose.cam_token_connector.rms_cam.fill_(.2)
    return model, batch, targets


class Rows:
    def __init__(self, batch, targets):
        self.batch, self.targets = batch, targets

    def get(self, stream, index):
        return self.batch, self.targets, {}


def collectives():
    context = ExitStack()
    for name, value in [('get_rank', 0), ('get_world_size', 1), ('get_backend', 'gloo')]:
        context.enter_context(patch.object(dist, name, return_value=value))
    for name in ('barrier', 'broadcast', 'broadcast_object_list'):
        context.enter_context(patch.object(dist, name))
    return context


def distributed_worker(rank, directory, port):
    torch.set_num_threads(1)
    dist.init_process_group('gloo', init_method=f'tcp://127.0.0.1:{port}', rank=rank, world_size=2)
    try:
        for mode in ('frozen', 'finetune'):
            model, batch, targets = model_fixture(mode, hold_steps=0, warmup_steps=1)
            batch['pixel_values_videos'] += rank * .13
            wrapped = run.wrap_model(model, torch.device('cpu'), mixed_precision=False)
            optimizer = torch.optim.AdamW(parameter_groups(wrapped, model.recipe))
            encoder = model.auxiliary_heads.geometry_encoder
            before = {k: v.clone() for k, v in encoder.state_dict().items()}
            rows = Rows(batch, targets)
            info, _ = run.optimize_step(wrapped, optimizer, rows, [('pose', [0, 1])], rank,
                                        torch.device('cpu'), 1, True)
            assert np.isfinite(info['components']['pose'])
            assert model.auxiliary_heads.pose.cam_token_connector.mlp[2].weight.grad.norm() > 0
            for name, p in encoder.named_parameters():
                other = p.detach().clone()
                dist.broadcast(other, src=0)
                assert torch.equal(p, other), name
                if mode == 'frozen':
                    assert torch.equal(p, before[name]), name
            if mode == 'finetune':
                info, _ = run.optimize_step(wrapped, optimizer, rows, [('pose', [0, 1])], rank,
                                            torch.device('cpu'), 2, True)
                assert info['gradient_norms']['geometry_encoder'] > 0
                saved = {k: p.clone() for k, p in encoder.state_dict().items()}
                moments = {n: copy.deepcopy(optimizer.state[p]) for n, p in encoder.named_parameters()
                           if p.requires_grad}
                pin = run.checkpoint(Path(directory)/'checkpoint', wrapped, optimizer, {'gx_fixture': True}, 2)
                run.optimize_step(wrapped, optimizer, rows, [('pose', [0, 1])], rank, torch.device('cpu'), 3, True)
                assert run.restore(pin, wrapped, optimizer, {'gx_fixture': True}) == 2
                for name, p in encoder.named_parameters():
                    assert torch.equal(p, saved[name]), name
                    if p.requires_grad:
                        for key, value in moments[name].items():
                            assert torch.equal(optimizer.state[p][key], value), (name, key)
            run.export(Path(directory)/mode, wrapped, model, {'base_identity': 'gx-fixture', 'trace_program_version': '3.13'}, 1)
            if rank == 0:
                state = torch.load(Path(directory)/mode/'heads.pt', weights_only=True)
                for k, v in encoder.state_dict().items():
                    assert torch.equal(state['geometry_encoder.'+k], v), k
        if rank == 0:
            write(Path(directory)/'result.json', dict(status='PASS', modes=['frozen', 'finetune']))
    finally:
        dist.destroy_process_group()


class GXTests(unittest.TestCase):
    def test_vendor_bytes_digest_and_import_origin(self):
        source = Path('/scratch/jjyeung/orch_cd/c1r/work/D/g3t_src/vggt')
        files = sorted((gx.VENDOR/'vggt').rglob('*.py'))
        self.assertEqual(len(files), 26)
        lines = []
        for path in files:
            self.assertEqual(path.read_bytes(), (source/path.relative_to(gx.VENDOR/'vggt')).read_bytes())
            lines.append(f'{path.relative_to(gx.VENDOR).as_posix()}\0{hashlib.sha256(path.read_bytes()).hexdigest()}\n')
        self.assertEqual(gx.vendor_digest(), hashlib.sha256(''.join(lines).encode()).hexdigest())
        with patch.dict(sys.modules, {'vggt.foreign': SimpleNamespace(__file__='/foreign/vggt/module.py')}):
            with self.assertRaisesRegex(ValueError, 'already imported'):
                gx.source_import(gx.VENDOR)

    def test_step_zero_identity_hidden_loss_readout_and_generation(self):
        donor, batch, target = model_fixture()
        donor.eval()
        with torch.no_grad():
            hidden = donor.hidden(batch)
            loss = donor(batch, target)['loss']
            readout = donor.pose_readout(batch)
        for mode in ('frozen', 'finetune'):
            model, _, _ = model_fixture(mode)
            model.eval()
            with torch.no_grad():
                self.assertTrue(torch.equal(model.hidden(batch), hidden))
                result = model(batch, target)
                self.assertTrue(torch.equal(result['loss'], loss))
                self.assertTrue(np.array_equal(model.pose_readout(batch), readout))
                self.assertEqual(result['metrics']['gx']['delta_ratio'], 0.)
                self.assertTrue(result['metrics']['gx']['feature_finite'])
                model.gx_zero_feature = True
                self.assertTrue(torch.equal(model.hidden(batch), hidden))
                model.gx_zero_feature = False
                self.assertTrue(torch.equal(model.generate(batch, max_new_tokens=1, do_sample=False,
                    pad_token_id=0, eos_token_id=1), donor.generate(batch, max_new_tokens=1,
                    do_sample=False, pad_token_id=0, eos_token_id=1)))
            model.train()
            self.assertFalse(model.model.visual.training)
            self.assertTrue(all(not m.training for m in model.auxiliary_heads.geometry_encoder.modules()))

    def test_artifact_warmstart_and_strict_planned_init(self):
        donor, batch, target = model_fixture()
        for _, p in full_ft.base_parameters(donor):
            p.data = p.bfloat16().float()
        directory = root()/'donor'
        with collectives(), patch('student_pilot.fsdp_training.publication_state', return_value=donor.state_dict()):
            run.export(directory, donor, donor, {'base_identity': 'fixture', 'trace_program_version': '3.13'}, 800)
        spec = dict(artifact=file_pin(directory/'artifact.json'), lm='full', heads=['pose'])
        for mode in ('frozen', 'finetune'):
            model, _, _ = model_fixture(mode)
            run.init_from_artifact(model, spec, part='lm')
            report = run.init_from_artifact(model, spec, part='heads')
            expected = sorted(k for k in model.auxiliary_heads.state_dict() if k.startswith('pose.cam_token_connector.'))
            self.assertEqual(report['planned_init'], expected)
            model.eval(); donor.eval()
            with torch.no_grad():
                self.assertTrue(torch.equal(model.hidden(batch), donor.hidden(batch)))
                self.assertTrue(torch.equal(model(batch, target)['loss'], donor(batch, target)['loss']))
                self.assertTrue(np.array_equal(model.pose_readout(batch), donor.pose_readout(batch)))
            state = torch.load(directory/'heads.pt', weights_only=True)
            state['pose.unexpected'] = torch.ones(1)
            bad = root()
            torch.save(state, bad/'heads.pt')
            artifact = load(directory/'artifact.json')
            artifact['heads'] = file_pin(bad/'heads.pt')
            write(bad/'artifact.json', artifact)
            with self.assertRaisesRegex(ValueError, 'init heads differ'):
                run.init_from_artifact(model, {**spec, 'artifact': file_pin(bad/'artifact.json')})

    def test_student_frames_real_processor_and_square_padding(self):
        from transformers.models.qwen3_vl.video_processing_qwen3_vl import Qwen3VLVideoProcessor
        from transformers.image_utils import SizeDict
        from transformers.video_utils import VideoMetadata
        processor = Qwen3VLVideoProcessor(patch_size=16, temporal_patch_size=2, merge_size=2,
                                          size=dict(shortest_edge=32*32, longest_edge=96*96))
        viewpoints = np.random.default_rng(42).integers(0, 256, (32, 35, 69, 3), dtype=np.uint8)
        arrays = np.repeat(viewpoints, 2, axis=0)
        metadata = VideoMetadata(total_num_frames=64, fps=2., frames_indices=list(range(64)))
        batch = processor(videos=[arrays], video_metadata=[metadata], do_sample_frames=False,
                          do_convert_rgb=False, return_tensors='pt')
        config = SimpleNamespace(patch_size=16, temporal_patch_size=2, spatial_merge_size=2)
        videos = gx.student_frames(**batch, vision_config=config,
                                   image_mean=processor.image_mean, image_std=processor.image_std)
        gh, gw = batch['video_grid_thw'][0, 1:].tolist()
        resized = processor.resize(torch.from_numpy(viewpoints).permute(0, 3, 1, 2),
                                   SizeDict(height=gh*16, width=gw*16), processor.resample).float()/255
        self.assertLessEqual(float((videos[0]-resized).abs().max()), 1/255)
        self.assertEqual(videos[0].dtype, torch.float32)
        square, coords = gx.square_518(videos[0])
        h, w = videos[0].shape[-2:]
        side = max(h, w); left = (side-w)//2; top = (side-h)//2
        expected = F.interpolate(F.pad(videos[0], (left, side-w-left, top, side-h-top)),
                                 (518, 518), mode='bilinear', align_corners=False, antialias=False)
        self.assertTrue(torch.equal(square, expected))
        gx.source_import(gx.VENDOR)
        from vggt.utils.load_fn import load_and_preprocess_images_square
        image = Image.fromarray(resized[0].mul(255).round().byte().permute(1, 2, 0).numpy())
        image_bytes = io.BytesIO(); image.save(image_bytes, format='PNG'); image_bytes.seek(0)
        _, upstream_coords = load_and_preprocess_images_square([image_bytes], 1024)
        torch.testing.assert_close(coords[0], upstream_coords[0, :4], rtol=0, atol=0)
        model, tiny_batch, _ = model_fixture('frozen')
        model.config.vision_config.patch_size = 16
        model.config.vision_config.temporal_patch_size = 2
        model.config.vision_config.spatial_merge_size = 2
        model.geometry_runtime = dict(image_mean=processor.image_mean, image_std=processor.image_std)
        model.auxiliary_heads.geometry_encoder.image_size = 518
        captured = []
        def fake(encoder, images, coords):
            captured.append(images)
            return torch.ones(32, 2058)
        with patch.object(gx, 'features', side_effect=fake):
            model.geometry_features({**tiny_batch, **batch})
        self.assertTrue(torch.equal(captured[0], square))
        multi = gx.student_frames(torch.cat([batch['pixel_values_videos']]*2),
            batch['video_grid_thw'].repeat(2, 1), config, processor.image_mean, processor.image_std)
        self.assertTrue(torch.equal(multi[1], videos[0]))
        with self.assertRaisesRegex(ValueError, '32'):
            gx.student_frames(batch['pixel_values_videos'], torch.tensor([[31, gh, gw]]), config,
                              processor.image_mean, processor.image_std)

    def test_native_layout_matches_vendor_on_augmented_viewpoints(self):
        from student_pilot.pose_samples import augment
        gx.source_import(gx.VENDOR)
        from vggt.utils.load_fn import load_and_preprocess_images_square
        processor = SimpleNamespace(tokenizer=Tokenizer(), video_processor=SimpleNamespace(merge_size=2))
        model, _, targets = model_fixture()
        jitter = dict(seed=17, brightness=.3, contrast=.2, saturation=.2, hue=.1,
                      blur_p=0., grayscale_p=0.)
        indices = list(range(0, 128, 4))
        for layout, h, w in (('duplicate', 35, 69), ('paired', 69, 35)):
            with self.subTest(layout=layout):
                source = np.random.default_rng(17).integers(0, 256,
                    (32 if layout == 'duplicate' else 64, h, w, 3), dtype=np.uint8)
                augmented = augment(source, jitter)
                viewpoints = augmented if layout == 'duplicate' else augmented[::2]
                self.assertFalse(np.array_equal(augmented, source))
                inputs = dict(frames=[dict(path='/fixture/rgb.png', sha256='a'*64)]*32,
                    frame_indices=indices, timestamps=[i/10 for i in indices], fps=10., total_num_frames=400,
                    question='Pose?', options=[], recording_id='recording')
                if layout == 'paired':
                    inputs['partner_frames'] = [dict(path='/fixture/partner.png', sha256='b'*64,
                        frame_index=i+1, timestamp=(i+1)/10, recording_id='recording') for i in indices]
                row = dict(qid='fixture', target='unused', student_input=inputs,
                           category='camera_pose_only', pose_sample=dict(augment=jitter))
                raw = raw_batch(32)
                receipt = dict(streams={}, frame_layout=layout, training_mode='pose_only',
                    **(dict(frame_pair_gap_seconds=.1) if layout == 'paired' else {}))
                def encode(processor, question, options, arrays, metadata, target, *args):
                    expected = np.repeat(augmented, 2, axis=0) if layout == 'duplicate' else augmented
                    np.testing.assert_array_equal(arrays, expected)
                    self.assertEqual(len(arrays), 64)
                    self.assertEqual(target, data.READOUT_TARGET)
                    return copy.deepcopy(raw), {'native': True}
                with patch('student_pilot.pose_samples.load_frames', return_value=source), \
                     patch('student_pilot.pose_samples.check_sample'), \
                     patch('student_pilot.pose_samples.augment', wraps=augment) as augment_call, \
                     patch('student_pilot.pose_samples.encode_frames', side_effect=encode), \
                     patch.object(data, 'target_tensors', return_value=targets), \
                     patch.object(run, 'dense_pose_row', return_value=True), \
                     patch.object(run.Rows, 'row', return_value=(row, {})), \
                     patch.object(gx, 'native_square_518', wraps=gx.native_square_518) as native:
                    legacy, _, legacy_audit = run.Rows(receipt, processor).get('pose', 0)
                    default, _, default_audit = run.Rows({**receipt, 'geometry_online': settings()}, processor).get('pose', 0)
                    native.assert_not_called()
                    block = {**settings(), 'input': gx.NATIVE_INPUT}
                    batch, actual, audit = run.Rows({**receipt, 'geometry_online': block}, processor).get('pose', 0)
                    native.assert_called_once()
                    np.testing.assert_array_equal(native.call_args.args[0], viewpoints)
                    self.assertEqual([len(call.args[0]) for call in augment_call.call_args_list], [len(source)]*3)
                self.assertEqual(audit, default_audit)
                self.assertEqual(audit, legacy_audit)
                self.assertIs(actual, targets)
                self.assertEqual(set(default), set(legacy))
                self.assertEqual(set(batch)-set(default), {'aux_g3t_images', 'aux_g3t_coords'})
                for key in legacy:
                    self.assertEqual(default[key].numpy().tobytes(), legacy[key].numpy().tobytes(), key)
                    self.assertEqual(batch[key].numpy().tobytes(), legacy[key].numpy().tobytes(), key)
                self.assertEqual(batch['aux_g3t_images'].shape, (1, 32, 3, 518, 518))
                self.assertEqual(batch['aux_g3t_images'].dtype, torch.float16)
                self.assertEqual(batch['aux_g3t_coords'].shape, (1, 32, 4))
                self.assertEqual(batch['aux_g3t_coords'].dtype, torch.float32)
                for i, frame in enumerate(viewpoints):
                    with io.BytesIO() as buffer:
                        Image.fromarray(frame).save(buffer, format='PNG'); buffer.seek(0)
                        square, coords = load_and_preprocess_images_square([buffer], 1024)
                    expected = F.interpolate(square, (518, 518), mode='bilinear', align_corners=False).half()
                    self.assertTrue(torch.equal(batch['aux_g3t_images'][0, i], expected[0]), i)
                    self.assertTrue(torch.equal(batch['aux_g3t_coords'][0, i], coords[0, :4]), i)
                run.check_row(batch, actual, 'pose', model)
                moved = run.move(batch, torch.device('cpu'))
                for key in ('aux_g3t_images', 'aux_g3t_coords'):
                    self.assertTrue(torch.equal(moved[key], batch[key]))

    def test_native_geometry_consumes_batch_images_and_requires_both_keys(self):
        model, batch, _ = model_fixture('frozen')
        model.geometry_online['input'] = gx.NATIVE_INPUT
        images = torch.rand(1, 32, 3, 518, 518).half()
        coords = torch.arange(128, dtype=torch.float32).reshape(1, 32, 4)
        batch = {**batch, 'aux_g3t_images': images, 'aux_g3t_coords': coords}
        captured = []
        def encoder(images, coords):
            captured.append((images, coords))
            return torch.ones(32, 2048), torch.ones(32, 6), torch.ones(32, 5)
        with patch.object(model.auxiliary_heads.geometry_encoder, 'forward', side_effect=encoder), \
             patch.object(gx, 'student_frames', side_effect=AssertionError('unpatchify')), \
             patch.object(gx, 'square_518', side_effect=AssertionError('square')), \
             patch.object(gx, 'pose9', return_value=(torch.ones(32, 9), None)), \
             patch.object(gx, 'disagreement', return_value=torch.ones(32, 1)):
            values = model.geometry_features(batch)
            self.assertEqual(values.shape, (1, 32, 2058))
            self.assertEqual(len(captured), 1)
            self.assertTrue(torch.equal(captured[0][0], images[0].float()))
            self.assertTrue(torch.equal(captured[0][1], coords[0]))
            device = next(model.auxiliary_heads.geometry_encoder.parameters()).device
            for value in captured[0]:
                self.assertEqual(value.dtype, torch.float32)
                self.assertEqual(value.device, device)
            for missing in (('aux_g3t_images',), ('aux_g3t_coords',), ('aux_g3t_images', 'aux_g3t_coords')):
                with self.subTest(missing=missing), self.assertRaisesRegex(ValueError, 'Native GX requires aux_g3t'):
                    model.geometry_features({k: v for k, v in batch.items() if k not in missing})
            with self.assertRaisesRegex(ValueError, 'one 32-viewpoint clip'):
                model.geometry_features({**batch, 'aux_g3t_images': images[:, :31]})
            self.assertEqual(len(captured), 1)

    def test_native_input_validation_and_viewpoint_count(self):
        for mode in ('frozen', 'finetune'):
            cfg = configuration(mode)
            cfg['init_artifact'] = dict(artifact=dict(path='/fixture/artifact.json', sha256='c'*64),
                                        lm='full', heads=['pose'])
            for input_ in (gx.INPUT, gx.NATIVE_INPUT):
                block = {**settings(mode), 'input': input_}
                self.assertEqual(gx.normalize(block), block)
                run.validate({**cfg, 'geometry_online': block})
            for input_ in ('other', '', None, 3, [], {}):
                with self.subTest(mode=mode, input=input_):
                    block = {**settings(mode), 'input': input_}
                    with self.assertRaisesRegex(ValueError, 'Unsupported GX contract'):
                        gx.normalize(block)
                    with self.assertRaises(ValueError):
                        run.validate({**cfg, 'geometry_online': block})
        for count in (0, 31, 64):
            with self.subTest(count=count), self.assertRaisesRegex(ValueError, '32 viewpoint frames'):
                gx.native_square_518(np.zeros((count, 8, 8, 3), dtype=np.uint8))

    def test_native_switch_does_not_add_keys_to_question_rows(self):
        processor = SimpleNamespace(tokenizer=Tokenizer(), video_processor=SimpleNamespace(merge_size=2))
        row = dict(student_input=dict(frames=[], fps=1., total_num_frames=64, frame_indices=[],
            timestamps=[], question='Question?', options=[]), target='answer')
        with patch('student_pilot.pose_samples.encode_row', return_value=(raw_batch(16), {})), \
             patch.object(gx, 'native_square_518', side_effect=AssertionError('question geometry')):
            batch, targets, _ = data.encode(processor, row, {}, 'vqa',
                                           geometry_online={**settings(), 'input': gx.NATIVE_INPUT})
        self.assertIsNone(targets)
        self.assertNotIn('aux_g3t_images', batch)
        self.assertNotIn('aux_g3t_coords', batch)

    def test_pose_converter_and_disagreement(self):
        gx.source_import(gx.VENDOR)
        from vggt.utils.pose_enc import pose_encoding_to_extri_intri
        from vggt.utils.rotation import mat_to_quat, quat_to_mat
        from student_pilot.camera_targets import encode_cameras
        torch.manual_seed(8)
        local = torch.cat([F.normalize(torch.randn(32, 4), dim=-1), torch.rand(32, 2)*2+.2], -1)
        global_ = torch.cat([torch.randn(32, 3), F.normalize(torch.randn(32, 2), dim=-1)], -1)
        coords = torch.tensor([0., 137., 1024., 887.]).repeat(32, 1)
        normalized, raw = gx.pose9(local, global_, coords)
        a, intr = pose_encoding_to_extri_intri(local[None].double(), (518, 518), 'noT_quaR_FoV')
        b, _ = pose_encoding_to_extri_intri(global_[None].double(), (518, 518), 'absT_quaRy_noFoV', False)
        def lift(x):
            return torch.cat([x, torch.tensor([0., 0., 0., 1.]).to(x).expand(1, 32, 1, 4)], -2)
        world = (lift(a) @ lift(b))[0]
        c2w = torch.linalg.inv(world).numpy()
        box = coords.double().numpy()*518/1024
        intr = intr[0].double().numpy()
        intr[:, 0, 2] -= box[:, 0]; intr[:, 1, 2] -= box[:, 1]
        hw = np.stack([box[:, 3]-box[:, 1], box[:, 2]-box[:, 0]], -1)
        reference, mask, _ = encode_cameras(c2w, intr, hw, all_frames=True)
        self.assertTrue(mask.all())
        np.testing.assert_allclose(raw.numpy(), reference, atol=1e-4, rtol=0)
        torch.testing.assert_close(raw[0, :7], torch.tensor([0., 0., 0., 0., 0., 0., 1.]).double(), atol=1e-6, rtol=0)
        self.assertAlmostEqual(float(normalized[1:, :3].norm(dim=-1).mean()), 1., places=6)
        for angle in (-.8, 0., .7):
            c, s = np.cos(.3), np.sin(.3)
            rx = torch.tensor([[1., 0., 0.], [0., c, -s], [0., s, c]])
            c, s = np.cos(.4), np.sin(.4)
            rz = torch.tensor([[c, -s, 0.], [s, c, 0.], [0., 0., 1.]])
            local_rotation = (rx @ rz).T
            c, s = np.cos(angle), np.sin(angle)
            yaw = torch.tensor([[c, 0., s], [0., 1., 0.], [-s, 0., c]])
            q = mat_to_quat(local_rotation @ yaw)
            local_pose = torch.cat([q, torch.ones(2).to(q)])[None]
            self.assertAlmostEqual(float(gx.disagreement(local_pose)), abs(angle), places=6)

    def test_gradients_scope_groups_and_hold_warmup(self):
        for mode in ('frozen', 'finetune'):
            model, batch, target = model_fixture(mode)
            encoder = model.auxiliary_heads.geometry_encoder
            groups = parameter_groups(model, model.recipe)
            model(batch, target)['loss'].backward()
            if mode == 'frozen':
                self.assertTrue(all(not p.requires_grad and p.grad is None for p in encoder.parameters()))
                self.assertNotIn('geometry_encoder', [g['name'] for g in groups])
            else:
                group = next(g for g in groups if g['name'] == 'geometry_encoder')
                self.assertEqual(group['lr'], model.recipe['learning_rate']*.1)
                self.assertTrue(all(p.grad is not None and torch.count_nonzero(p.grad) == 0
                                    for p in encoder.aggregator.parameters() if p.requires_grad))
                self.assertTrue(all(not p.requires_grad for p in encoder.local_camera_head.parameters()))
                self.assertTrue(all(not p.requires_grad for p in encoder.global_camera_head.parameters()))
                model.zero_grad(set_to_none=True)
                torch.nn.init.normal_(model.auxiliary_heads.pose.cam_token_connector.mlp[2].weight, std=.01)
                model(batch, target)['loss'].backward()
                self.assertTrue(any(p.grad is not None and p.grad.abs().sum() > 0 for p in encoder.aggregator.parameters()))
                opt = torch.optim.AdamW(groups)
                for step in (1, 2, 3):
                    run.optimize_step(model, opt, Rows(batch, target), [('pose', [0])], 0, torch.device('cpu'), step)
                    expected = run.learning_rate(step, {**model.recipe, 'learning_rate': group['initial_lr']})
                    ramp = (0., .5, 1.)[step-1]
                    self.assertEqual(group['lr'], expected * ramp)
        encoder = gx.G3TEncoder(settings('finetune', scope='aggregator_blocks'), architecture(), image_size=28)
        self.assertTrue(all(not p.requires_grad for p in encoder.aggregator.patch_embed.parameters()))
        self.assertTrue(encoder.aggregator.camera_token.requires_grad)

    def test_lean_parity_checkpointing_and_repeat_conv_and_dino(self):
        for dino in (False, True):
            with self.subTest(dino=dino):
                torch.manual_seed(99)
                block = settings('finetune')
                encoder = gx.G3TEncoder(block, architecture(dino), image_size=28)
                images = torch.rand(3, 3, 28, 28)
                values = encoder(images)
                self.assertTrue(encoder.verified)
                self.assertTrue(all(torch.equal(a, b) for a, b in zip(values, encoder(images))))
                values[0].square().mean().backward()
                grads = {n: p.grad.clone() for n, p in encoder.named_parameters() if p.grad is not None}
                encoder.zero_grad(set_to_none=True)
                encoder.settings['finetune']['checkpointing'] = True
                observed = []
                original = gx.checkpoint
                def capture(module, *args, **kwargs):
                    observed.append(module)
                    self.assertIs(kwargs['use_reentrant'], False)
                    return original(module, *args, **kwargs)
                with patch.object(gx, 'checkpoint', side_effect=capture):
                    checked = encoder(images)
                    self.assertTrue(all(torch.equal(a, b) for a, b in zip(values, checked)))
                    checked[0].square().mean().backward()
                for name, p in encoder.named_parameters():
                    if name in grads:
                        torch.testing.assert_close(p.grad, grads[name], atol=1e-6, rtol=1e-6)
                expected = list(encoder.aggregator.frame_blocks)+list(encoder.aggregator.global_blocks)
                if dino:
                    expected += list(encoder.aggregator.patch_embed.blocks)
                    self.assertFalse(encoder.aggregator.patch_embed.mask_token.requires_grad)
                self.assertTrue(all(any(m is p for m in observed) for p in expected))
                frozen = gx.G3TEncoder(settings(), architecture(dino), image_size=28)
                frozen.load_state_dict(encoder.state_dict())
                self.assertTrue(all(torch.equal(a, b) for a, b in zip(checked, frozen(images))))
                self.assertTrue(frozen.verified)

    def test_production_meta_header_and_strict_safetensors(self):
        with torch.device('meta'):
            model = gx.G3TEncoder(settings())
        header = load('/scratch/jjyeung/orch_cd/gx_build/work/aws_probe/g3t_header.json')['header']
        expected = {k: v[1] for k, v in header.items()
                    if k.startswith(('aggregator.', 'local_camera_head.', 'global_camera_head.'))}
        self.assertEqual({k: list(v.shape) for k, v in model.state_dict().items()}, expected)
        from safetensors.torch import save_file
        encoder = gx.G3TEncoder(settings(), architecture(), image_size=28)
        state = {k: v.clone() for k, v in encoder.state_dict().items()}
        state['depth_head.fixture'] = torch.ones(2)
        directory = root(); path = directory/'weights.safetensors'
        save_file(state, path)
        encoder.settings['encoder']['weights'] = file_pin(path)
        report = encoder.load_pinned(path, True)
        self.assertEqual(report['tensors'], len(encoder.state_dict()))
        self.assertEqual(report['parameters'], sum(v.numel() for v in encoder.state_dict().values()))
        self.assertTrue(all(p.dtype == torch.float32 for p in encoder.parameters()))
        for change in ('missing', 'prefix', 'shape', 'sha'):
            broken = dict(state)
            key = next(k for k in state if k.startswith('aggregator.'))
            if change == 'missing':
                broken = {k: v for k, v in broken.items() if k != key}
            elif change == 'prefix':
                broken['other.extra'] = torch.ones(1)
            elif change == 'shape':
                broken[key] = torch.ones(1)
            bad = directory/(change+'.safetensors')
            save_file(broken, bad)
            if change == 'sha':
                encoder.settings['encoder']['weights']['sha256'] = '0'*64
            with self.assertRaises(ValueError):
                encoder.load_pinned(bad, change == 'sha')

    @unittest.skipUnless(SOCKETS, 'Local gloo sockets required')
    def test_two_rank_fsdp_replicas_checkpoint_and_exports(self):
        directory = root()
        run_workers(distributed_worker, (str(directory),))
        self.assertEqual(load(directory/'result.json')['status'], 'PASS')

    def test_config_recipe_validation_and_legacy_bytes(self):
        for mode in ('frozen', 'finetune'):
            cfg = configuration(mode)
            cfg['init_artifact'] = dict(artifact=dict(path='/fixture/artifact.json', sha256='c'*64),
                                         lm='full', heads=['pose'])
            run.validate(cfg)
            recipe = recipe_for(cfg)
            self.assertEqual(recipe['milestones'], [0, 2, 12])
            self.assertEqual(recipe['steps'], 12)
            self.assertEqual(recipe['mix'], ['pose']*4)
            self.assertEqual(recipe['world_size'], 8)
            self.assertEqual(recipe['global_batch'], 32)
            if mode == 'finetune':
                self.assertEqual(recipe['geometry_learning_rate'], recipe['learning_rate']*.1)
            for key, value in [('training_mode', 'final'), ('training_mode', 'mixed'),
                               ('frame_layout', 'spread'), ('depth_enabled', True), ('align', {})]:
                with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                    run.validate({**cfg, key: value})
            for block in ({**cfg['geometry_online'], 'unknown': 1},
                          {**cfg['geometry_online'], 'mode': 'other'}):
                with self.assertRaises(ValueError):
                    run.validate({**cfg, 'geometry_online': block})
        with self.assertRaises(ValueError):
            gx.normalize(settings('finetune') | {'finetune': None})
        legacy = dict(training_mode='pose_only', depth_enabled=False, schedule=configuration()['schedule'])
        expected = copy.deepcopy(RECIPE)
        expected.update(mix=['pose']*4)
        expected['weights'].update(vqa=0., pointing=0., depth=0., depth_fov=0.)
        self.assertEqual(json.dumps(recipe_for(legacy), sort_keys=True), json.dumps(expected, sort_keys=True))
        before = {**legacy, 'recipe': expected}
        self.assertEqual(run.identity(before), run.identity({**legacy, 'recipe': recipe_for(legacy)}))
        self.assertEqual(recipe_for(dict(training_mode='mixed')), RECIPE)
        schedule = dict(seed=17, max_own_probability=1., pose_open_deg=45., pose_full_deg=25.,
            fov_open_deg=2., depth_open_absrel=.25, ema_steps=100, force_from_step=0,
            exposure_from_step=None, exposure_probability=0.)
        final = dict(training_mode='final', mix=['pose', 'vqa', 'pointing', 'routing'], world_size=8,
                     scheduled_sampling=schedule)
        expected = copy.deepcopy(RECIPE)
        from student_pilot.carrier_c1_routing import validate_schedule
        expected.update(mix=final['mix'], scheduled_sampling=validate_schedule(schedule))
        expected['weights']['routing'] = 1.
        self.assertEqual(recipe_for(final), expected)
        recipe = configuration()['recipe']
        self.assertEqual(capped_steps(configuration()['schedule'], total_steps=recipe['steps'],
                                      milestones=recipe['milestones']), 12)
        with self.assertRaises(ValueError):
            run.warn({'training_mode': 'pose_only'}, 'mismatch')
        run.warn(configuration(), 'GX mismatch fixture')

    def test_fail_fast_verdict_rank_history_and_resume_refusal(self):
        def ranks(step, loss=1., delta=.1):
            return [dict(step=step, shapes=[dict(gx=dict(delta_ratio=delta))], stream_means=dict(pose=loss))]*2
        history = [ranks(i) for i in range(1, 21)]
        block = dict(step=20, min_delta_ratio=.01, max_loss_ratio=2.)
        self.assertEqual(run.gx_fail_fast(history, block)['verdict'], 'CONTINUE')
        self.assertEqual(run.gx_fail_fast(history, {**block, 'min_delta_ratio': .2})['verdict'], 'STOP')
        self.assertEqual(run.gx_fail_fast(history[:10]+[ranks(i, loss=3.) for i in range(11, 21)], block)['verdict'], 'STOP')
        directory = root()
        with (directory/'metrics_cpu.jsonl').open('x') as handle:
            for i, entry in enumerate(history, 1):
                handle.write(json.dumps(dict(step=i, ranks=entry))+'\n')
        self.assertEqual(run.gx_step_history(directory, 10), history[:10])
        cfg = configuration(); cfg['output'] = str(directory)
        cfg['init_artifact'] = dict(artifact=dict(path='/fixture/artifact.json', sha256='c'*64), lm='full', heads=['pose'])
        write(directory/'gx_fail_fast_cpu.json', dict(verdict='STOP', rule_sha256=run.gx_rule_hash(None)))
        with self.assertRaisesRegex(ValueError, 'cannot resume'):
            run.train(cfg, resume_pin='latest')

    def test_production_optimizer_groups_use_the_gx_recipe(self):
        # train() and dryrun() build groups from the model's own recipe; the default RECIPE has no geometry rate.
        model, _, _ = model_fixture('finetune')
        class Wrapped(torch.nn.Module):
            def __init__(self, module):
                super().__init__()
                self.module = module
        self.assertEqual(run.gx_recipe(Wrapped(model)), {'recipe': model.recipe})
        groups = {g['name']: g for g in parameter_groups(model, **run.gx_recipe(model))}
        self.assertAlmostEqual(groups['geometry_encoder']['lr'], groups['heads']['lr'] * .1)
        with self.assertRaises(KeyError):
            parameter_groups(model)
        frozen, _, _ = model_fixture('frozen')
        self.assertEqual(run.gx_recipe(frozen), {'recipe': frozen.recipe})
        self.assertNotIn('geometry_encoder', {g['name'] for g in parameter_groups(frozen, **run.gx_recipe(frozen))})

    def test_paired_fail_fast_windows_and_normalized_hash(self):
        reference = root()
        block = dict(step=50, min_delta_ratio=.01, max_loss_ratio=1.2, reference=str(reference))
        block['reference_binding'] = reference_pin()
        config = settings(); config['fail_fast'] = block
        self.assertEqual(gx.normalize(config)['fail_fast'], block)
        for value in ('relative/path', None, 123, ''):
            with self.subTest(value=value), self.assertRaises(ValueError):
                gx.normalize({**config, 'fail_fast': {**block, 'reference': value}})
        self.assertEqual(run.gx_rule_hash({**block, 'max_loss_ratio': 2}),
                         run.gx_rule_hash({**block, 'max_loss_ratio': 2.}))
        def ranks(step, losses):
            return [dict(step=step, shapes=[dict(gx=dict(delta_ratio=.1))], stream_means=dict(pose=v))
                    for v in losses]
        # The control has unequal rank counts across steps. Average each step first.
        with (reference/'metrics_ctrl.jsonl').open('x') as handle:
            for step in range(1, 71):
                if step == 65:
                    continue
                values = [2., 4.] if step % 2 else [3.]
                handle.write(json.dumps(dict(step=step, ranks=ranks(step, values)))+'\n')
        history = [ranks(s, [1., 1.] if s <= 10 else [3., 3.2] if s <= 50 else [4., 4.])
                   for s in range(1, 71)]
        # This unit tests the arithmetic; production supplies the authenticated startup snapshot.
        reference_history = run.gx_step_history(reference, 70, by_step=True)
        def check(history, rule, **kwargs):
            return run.gx_fail_fast(history, rule, reference_history=reference_history, **kwargs)
        verdict = check(history[:50], block, end_step=50)
        self.assertEqual(verdict['verdict'], 'CONTINUE')
        self.assertEqual(verdict['rule_sha256'], run.gx_rule_hash(block))
        self.assertEqual((verdict['window_start_step'], verdict['step']), (41, 50))
        self.assertAlmostEqual(verdict['recent_pose_loss'], 3.1)
        self.assertAlmostEqual(verdict['reference_pose_loss'], 3.)
        self.assertEqual(check(history[:60], block, end_step=60)['verdict'], 'STOP')
        missing = check(history, {**block, 'min_delta_ratio': 1.}, end_step=70)
        self.assertEqual(missing['verdict'], 'CONTINUE')
        self.assertEqual(missing['missing_reference_steps'], [65])
        self.assertEqual(missing['reason'], 'missing_reference_steps')
        self.assertIsNone(missing['reference_pose_loss'])
        self.assertEqual(check(history[:50], {**block, 'min_delta_ratio': .2})['verdict'], 'STOP')
        # Equality does not stop; the rule says "exceeds".
        equal = [ranks(s, [3.75]) for s in range(1, 51)]
        self.assertEqual(check(equal, {**block, 'max_loss_ratio': 1.25})['verdict'], 'CONTINUE')
        # Missing own steps must never turn into a shorter comparison window.
        with self.assertRaisesRegex(ValueError, 'window steps'):
            run.gx_fail_fast(history[:43]+history[44:50], block)

    def test_rule_scoped_stop_train_guard_reports_and_ignores_old_stops(self):
        directory = root(); cfg = configuration()
        cfg.update(output=str(directory), init_artifact=dict(
            artifact=dict(path='/fixture/artifact.json', sha256='c'*64), lm='full', heads=['pose']))
        block = dict(step=50, min_delta_ratio=.01, max_loss_ratio=1.2, reference=str(root()))
        block['reference_binding'] = reference_pin()
        cfg['geometry_online']['fail_fast'] = block
        write(directory/'gx_fail_fast_old.json', dict(verdict='STOP', rule_sha256='old-rule'))
        write(directory/'gx_fail_fast_legacy.json', dict(verdict='STOP'))
        ignored = run.gx_resume_verdicts(directory, block)
        self.assertEqual(len(ignored), 2)
        with patch.object(torch.cuda, 'is_available', return_value=False), patch.object(run, 'gx_reference'), \
             patch('sys.stderr', new_callable=io.StringIO) as stderr:
            with self.assertRaisesRegex(ValueError, 'parent-authorized'):
                run.train(cfg, resume_pin='latest')
            self.assertIn('gx_ignored_older_rule_stops', stderr.getvalue())
        write(directory/'gx_fail_fast_new.json', dict(verdict='STOP', rule_sha256=run.gx_rule_hash(block)))
        with self.assertRaisesRegex(ValueError, 'cannot resume under the current rule'):
            run.train(cfg, resume_pin='latest')

    def test_run_loop_rechecks_paired_later_windows_and_retains_each_verdict(self):
        directory, reference = root(), root()
        cfg = configuration(); cfg['steps'] = 30; cfg['milestones'] = []
        cfg['recipe'] = recipe_for(cfg); cfg['output'] = str(directory)
        block = dict(step=10, min_delta_ratio=.01, max_loss_ratio=1.2, reference=str(reference))
        cfg['geometry_online']['fail_fast'] = block
        def ranks(step, loss):
            return [dict(step=step, shapes=[dict(gx=dict(delta_ratio=.1))],
                         stream_means=dict(pose=loss), wall_seconds=0.)]
        with (reference/'metrics_ctrl.jsonl').open('x') as handle:
            for step in range(1, 31):
                handle.write(json.dumps(dict(step=step, ranks=ranks(step, 2.)*8))+'\n')
        from tests.test_gx_s6 import reference_receipts
        reference_receipts(cfg, reference)
        def optimize(*args):
            step = args[6]
            return ranks(step, 2.1 if step <= 20 else 3.)[0], None
        checkpoints = []
        with patch.object(run, 'optimize_step', side_effect=optimize), \
             patch.object(run, 'checkpoint', side_effect=lambda *a, **k: checkpoints.append(a[4])), \
             patch.dict(os.environ, {'SLURM_JOB_ID': 'paired'}):
            report = run.run_steps(None, None, None, None, dict(pose=32), directory, cfg, {},
                                   torch.device('cpu'), distributed=False)
        self.assertEqual(report['last_step'], 30)
        self.assertEqual(report['stop_reason'], 'gx_fail_fast')
        self.assertEqual(checkpoints, [30])
        for step, verdict in ((10, 'CONTINUE'), (20, 'CONTINUE'), (30, 'STOP')):
            self.assertEqual(load(directory/f'gx_fail_fast_paired_step_{step:06d}.json')['verdict'], verdict)
        # An ordinary self-history rule remains a single check.
        cfg['geometry_online']['fail_fast'] = {k: v for k, v in block.items()
                                               if k not in ('reference', 'reference_binding')}
        fresh = root()
        with patch.object(run, 'optimize_step', side_effect=optimize), patch.object(run, 'checkpoint'):
            run.run_steps(None, None, None, None, dict(pose=32), fresh, cfg, {}, torch.device('cpu'), distributed=False)
        self.assertEqual(len(list(fresh.glob('gx_fail_fast*.json'))), 1)

    def test_rule_only_rebind_restores_exact_model_optimizer_rng_and_step(self):
        directory = root()
        cfg = configuration('finetune'); cfg['output'] = str(directory)
        cfg['geometry_online']['fail_fast'] = dict(step=50, min_delta_ratio=.01, max_loss_ratio=1.2)
        cfg['preparation'] = dict(path='/fixture/preparation.json', sha256='c'*64)
        old = dict(config_sha256=run.identity(cfg), preparation=cfg['preparation'], trainer_commit='A', world_size=1)
        run.bind_output(directory, old, cfg=cfg)
        original_binding = (directory/'binding.json').read_bytes()
        # The real shard writer/reader and AdamW, with only collectives mocked.
        model, batch, target = model_fixture('finetune', hold_steps=0, warmup_steps=1)
        optimizer = torch.optim.AdamW(parameter_groups(model, model.recipe))
        rows = Rows(batch, target)
        run.optimize_step(model, optimizer, rows, [('pose', [0])], 0, torch.device('cpu'), 1)
        def gather(out, value):
            out[0] = value
        with collectives(), patch.object(dist, 'all_gather_object', side_effect=gather):
            first = run.checkpoint(directory/'checkpoint_000001', model, optimizer, old, 1)
            run.optimize_step(model, optimizer, rows, [('pose', [0])], 0, torch.device('cpu'), 2)
            pin = run.checkpoint(directory/'checkpoint_000002', model, optimizer, old, 2)
            self.assertEqual(load(pin['path'])['config'], cfg)
            # Checkpoint-only config evidence must suffice without a binding snapshot or attempt receipt.
            snapshot = directory/f'binding_config_{run.digest(old)}.json'
            snapshot.rename(directory/'retained_config_A.json')
            expected_model = copy.deepcopy(model.state_dict())
            expected_opt = copy.deepcopy(optimizer.state_dict())
            expected_rng = (random.random(), np.random.random(), torch.rand(4))
            # Get the ordinary restore as an independent comparison.
            self.assertEqual(run.restore(pin, model, optimizer, old), 2)
            self.assertEqual(random.random(), expected_rng[0])
            self.assertEqual(np.random.random(), expected_rng[1])
            self.assertTrue(torch.equal(torch.rand(4), expected_rng[2]))
            current = copy.deepcopy(cfg)
            current['geometry_online']['fail_fast']['reference'] = str(root())
            current['geometry_online']['fail_fast']['reference_binding'] = reference_pin()
            bound = {**old, 'config_sha256': run.identity(current), 'trainer_commit': 'B'}
            self.assertEqual(run.latest_resume(directory, bound, cfg=current), pin)
            run.optimize_step(model, optimizer, rows, [('pose', [0])], 0, torch.device('cpu'), 3)
            self.assertEqual(run.restore(pin, model, optimizer, bound, cfg=current), 2)
            def equal(left, right):
                if torch.is_tensor(left):
                    self.assertTrue(torch.equal(left, right))
                elif isinstance(left, dict):
                    self.assertEqual(left.keys(), right.keys())
                    for key in left:
                        equal(left[key], right[key])
                elif isinstance(left, (tuple, list)):
                    self.assertEqual(len(left), len(right))
                    for a, b in zip(left, right):
                        equal(a, b)
                else:
                    self.assertEqual(left, right)
            equal(model.state_dict(), expected_model)
            equal(optimizer.state_dict(), expected_opt)
            self.assertEqual(random.random(), expected_rng[0])
            self.assertEqual(np.random.random(), expected_rng[1])
            self.assertTrue(torch.equal(torch.rand(4), expected_rng[2]))
            rebind = run.bind_output(directory, bound, resume=True, cfg=current, resume_pin=pin)
            self.assertEqual(load(rebind['path'])['resume'], pin)
            self.assertEqual((directory/'binding.json').read_bytes(), original_binding)
            self.assertEqual(run.output_bindings(directory)[-1][0], bound)
            # A crash after rebind, before a new checkpoint, can still select A.
            self.assertEqual(run.latest_resume(directory, bound, cfg=current), pin)
            self.assertIsNone(run.bind_output(directory, bound, resume=True, cfg=current, resume_pin=pin))
            second = run.checkpoint(directory/'checkpoint_000003', model, optimizer, bound, 3, rotate=True)
            self.assertEqual(run.latest_resume(directory, bound, cfg=current), second)
            self.assertTrue(Path(first['path']).is_file())
            self.assertTrue(Path(pin['path']).is_file())

    def test_rebind_rejects_foreign_configs_preparation_world_and_missing_evidence(self):
        directory = root(); cfg = configuration()
        cfg['output'] = str(directory)
        cfg['geometry_online']['fail_fast'] = dict(step=50, min_delta_ratio=.01, max_loss_ratio=1.2)
        old = dict(config_sha256=run.identity(cfg), preparation={'sha256': 'prep'}, trainer_commit='A', world_size=1)
        run.bind_output(directory, old, cfg=cfg)
        model = torch.nn.Linear(2, 1); optimizer = torch.optim.AdamW(model.parameters())
        model.trace_program_version = cfg['trace_program_version']
        def gather(out, value):
            out[0] = value
        with collectives(), patch.object(dist, 'all_gather_object', side_effect=gather):
            pin = run.checkpoint(directory/'checkpoint_000002', model, optimizer, old, 2)
            new_cfg = copy.deepcopy(cfg)
            new_cfg['geometry_online']['fail_fast']['reference'] = str(root())
            new_cfg['geometry_online']['fail_fast']['reference_binding'] = reference_pin()
            new = {**old, 'config_sha256': run.identity(new_cfg), 'trainer_commit': 'B'}
            changes = [('preparation', {**new, 'preparation': {'sha256': 'foreign'}}, new_cfg),
                       ('world_size', {**new, 'world_size': 2}, new_cfg)]
            for key, value in [('row_start_step', 1), ('steps', 99), ('skip_unsupervised_lm', True)]:
                bad_cfg = {**new_cfg, key: value}
                changes.append((key, {**new, 'config_sha256': run.identity(bad_cfg)}, bad_cfg))
            bad_cfg = copy.deepcopy(new_cfg)
            bad_cfg['geometry_online']['connector']['rms_scale'] = 2.
            changes.append(('connector', {**new, 'config_sha256': run.identity(bad_cfg)}, bad_cfg))
            for name, bad, bad_cfg in changes:
                with self.subTest(name=name):
                    with self.assertRaises(ValueError):
                        run.latest_resume(directory, bad, cfg=bad_cfg)
                    with self.assertRaises(ValueError):
                        run.restore(pin, model, optimizer, bad, cfg=bad_cfg)
                    with self.assertRaises(ValueError):
                        run.bind_output(directory, bad, resume=True, cfg=bad_cfg, resume_pin=pin)
            with self.assertRaises(ValueError):
                run.latest_resume(directory, new)
        self.assertEqual(len(list(directory.glob('binding_rebind_*.json'))), 0)
        # Legacy evidence: exact original binding plus a full config in an attempt receipt.
        legacy = root(); write(legacy/'binding.json', old)
        write(legacy/'attempt_legacy.json', dict(binding=old, config=cfg))
        self.assertEqual(run.stored_config(legacy, old), cfg)
        missing = root(); write(missing/'binding.json', old)
        write(missing/'attempt_bad.json', dict(binding=old, config={**cfg, 'steps': 999}))
        with self.assertRaisesRegex(ValueError, 'previous config'):
            run.stored_config(missing, old)

    def test_train_rebind_from_legacy_checkpoint_records_attempt_and_resume(self):
        directory = root(); cfg = configuration('finetune')
        cfg.update(output=str(directory), preparation={'fixture': True}, init_artifact=dict(
            artifact=dict(path='/fixture/artifact.json', sha256='c'*64), lm='full', heads=['pose']))
        cfg['geometry_online']['fail_fast'] = dict(step=50, min_delta_ratio=.01, max_loss_ratio=1.2)
        old = dict(config_sha256=run.identity(cfg), preparation=cfg['preparation'], trainer_commit='A', world_size=8)
        write(directory/'binding.json', old)
        model, _, _ = model_fixture('finetune')
        optimizer = torch.optim.AdamW(parameter_groups(model, model.recipe), weight_decay=RECIPE['weight_decay'])
        with collectives(), patch.object(dist, 'all_gather_object', side_effect=lambda out, value: out.__setitem__(0, value)):
            pin = run.checkpoint(directory/'checkpoint_000002', model, optimizer, old, 2)
        self.assertNotIn('config', load(pin['path']))
        current = copy.deepcopy(cfg)
        current['geometry_online']['fail_fast']['reference'] = str(root())
        current['geometry_online']['fail_fast']['reference_binding'] = reference_pin()
        bound = {**old, 'config_sha256': run.identity(current), 'trainer_commit': 'B'}
        with self.assertRaises(ValueError):
            run.latest_resume(directory, bound, cfg=current)
        # The old attempt provides the full previous config and exact original binding.
        write(directory/'attempt_A.json', dict(binding=old, config=cfg))
        self.assertEqual(run.latest_resume(directory, bound, cfg=current), pin)
        write(directory/'gx_fail_fast_A.json', dict(verdict='STOP'))
        write(directory/'authorization.json', dict(config_sha256=run.identity(current), new_gpus=8,
                                                   job_id='B', verdict='GO'))
        current['authorization'] = file_pin(directory/'authorization.json')
        with ExitStack() as stack:
            stack.enter_context(collectives())
            stack.enter_context(patch.object(dist, 'all_gather_object', side_effect=lambda out, value: out.__setitem__(0, value)))
            stack.enter_context(patch.dict(os.environ, WORLD_SIZE='8', RANK='0', LOCAL_RANK='0', SLURM_JOB_ID='B', C1_EXPECT_FLA='0'))
            stack.enter_context(patch.object(torch.cuda, 'is_available', return_value=True))
            for name in ('set_device', 'reset_peak_memory_stats'):
                stack.enter_context(patch.object(torch.cuda, name))
            for name in ('init_process_group', 'destroy_process_group', 'new_group'):
                stack.enter_context(patch.object(dist, name))
            for name, value in [('prepared', ({'streams': {'pose': {'count': 32}}}, {})),
                                ('gx_reference', None),
                                ('authenticate', 'B'), ('processor_for_receipt', None),
                                ('network_preflight', {'fixture': True}), ('agree', None),
                                ('load_model', model), ('wrap_model', model),
                                ('Rows', SimpleNamespace(close=lambda: None))]:
                stack.enter_context(patch.object(run, name, return_value=value))
            loop = stack.enter_context(patch.object(run, 'run_steps'))
            run.train(current, resume_pin='latest')
        self.assertEqual(loop.call_args.args[10], 2)
        attempt = load(directory/'attempt_B.json')
        self.assertEqual(attempt['binding'], bound)
        self.assertEqual(attempt['resume'], pin)
        self.assertEqual(attempt['first_step'], 3)
        self.assertEqual(load(attempt['rebind']['path'])['binding'], bound)
        self.assertEqual(len(attempt['ignored_older_rule_stops']), 1)
        self.assertEqual(load(directory/'binding.json'), old)

    def test_world_four_fallback_keeps_rows_and_batch_per_update(self):
        from student_pilot.carrier_c1_data import mixed_indices
        eight, four = configuration(), {**configuration(), 'world_size': 4}
        four['recipe'] = recipe_for(four)
        self.assertEqual((four['recipe']['world_size'], four['recipe']['mix'], four['recipe']['global_batch']),
                         (4, ['pose']*8, 32))
        self.assertEqual({k: v for k, v in four['recipe'].items() if k not in ('world_size', 'mix')},
                         {k: v for k, v in eight['recipe'].items() if k not in ('world_size', 'mix')})
        with self.assertRaises(ValueError):
            recipe_for({k: v for k, v in four.items() if k != 'geometry_online'} | {'world_size': 4})
        flat = lambda plans: [[i for _, rows in plan for i in rows] for plan in plans]
        a = flat(mixed_indices({'pose': 997}, 40, start_step=30, training_mode='pose_only', mix=['pose']*4, world=8))
        b = flat(mixed_indices({'pose': 997}, 40, start_step=30, training_mode='pose_only', mix=['pose']*8, world=4))
        self.assertEqual(a, b)
        self.assertEqual(flat(mixed_indices({'pose': 997}, 3, training_mode='pose_only', world=8)),
                         flat(mixed_indices({'pose': 997}, 3, training_mode='pose_only', mix=['pose']*4, world=8)))

    def test_nonfinite_features_raise(self):
        class Invalid:
            def __call__(self, images, coords):
                return torch.full((32, 2048), float('nan')), \
                    torch.tensor([0., 0., 0., 1., 1., 1.]).repeat(32, 1), \
                    torch.tensor([0., 0., 0., 0., 1.]).repeat(32, 1)
        with self.assertRaisesRegex(ValueError, '^Nonfinite G3T feature$'):
            gx.features(Invalid(), None, torch.tensor([0., 0., 1024., 1024.]).repeat(32, 1))

    def test_run_loop_m0_custom_budget_and_fail_fast_checkpoint(self):
        model, batch, target = model_fixture('finetune')
        cfg = configuration('finetune')
        cfg['geometry_online']['fail_fast'] = dict(step=2, min_delta_ratio=1e9, max_loss_ratio=100.)
        directory = root(); cfg['output'] = str(directory)
        optimizer = torch.optim.AdamW(parameter_groups(model, model.recipe))
        exports, checkpoints = [], []
        def publish(path, wrapped, live, config, step, *, optimizer, disk_guard):
            self.assertIsNotNone(optimizer)
            self.assertIsNotNone(disk_guard)
            exports.append(step)
            if step == 0:
                self.assertEqual(int(torch.count_nonzero(live.auxiliary_heads.pose.cam_token_connector.mlp[2].weight)), 0)
        def checkpoint(path, wrapped, opt, bound, step, **kwargs):
            checkpoints.append(step)
        with patch.object(run, 'export', side_effect=publish), patch.object(run, 'checkpoint', side_effect=checkpoint):
            report = run.run_steps(model, model, optimizer, Rows(batch, target), dict(pose=32),
                directory, cfg, {}, torch.device('cpu'), distributed=False)
        self.assertEqual(exports, [0, 2])
        self.assertEqual(checkpoints, [2])
        self.assertEqual(report['last_step'], 2)
        self.assertEqual(report['stop_reason'], 'gx_fail_fast')
        self.assertEqual(load(directory/'gx_fail_fast_cpu_step_000002.json')['verdict'], 'STOP')
        self.assertEqual(len(run.gx_step_history(directory, 2)), 2)

    def test_load_model_asset_pins_rms_and_export_geometry_binding(self):
        from transformers import Qwen3_5ForConditionalGeneration
        from safetensors.torch import save_file
        donor, batch, target = model_fixture()
        directory = root()
        block = settings('finetune')
        encoder = TinyEncoder(block)
        save_file(encoder.state_dict(), directory/'g3t.safetensors')
        write(directory/'g3t_config.json', dict(embed_dim=1024, enable_depth=True,
            enable_gravity_camera_heads=True, enable_point=True, img_size=518, patch_size=14))
        block['encoder']['weights'] = file_pin(directory/'g3t.safetensors')
        block['encoder']['config'] = file_pin(directory/'g3t_config.json')
        receipt = dict(camera=donor.auxiliary_heads.pose.settings, depth={}, carrier_placement=C1_A, trace_program_version='3.13',
            training_mode='pose_only', depth_enabled=False, recipe=configuration('finetune')['recipe'],
            frame_layout='duplicate', geometry_online=block)
        processor = SimpleNamespace(tokenizer=Tokenizer(), video_processor=SimpleNamespace(
            image_mean=[.5]*3, image_std=[.25]*3))
        def fresh(*args, **kwargs):
            return Qwen3_5ForConditionalGeneration(copy.deepcopy(donor.config))
        with patch.object(Qwen3_5ForConditionalGeneration, 'from_pretrained', side_effect=fresh), \
             patch.object(gx, 'G3TEncoder', TinyEncoder):
            model = run.load_model(dict(root=str(directory), files={}), receipt, processor)
        rms = model.auxiliary_heads.pose.tokens[1].detach().square().mean().sqrt()
        self.assertEqual(model.gx_report['rms_cam'], float(rms))
        self.assertEqual(model.gx_report['mode'], 'finetune')
        self.assertGreater(model.gx_report['trainable_params'], 0)
        for k, v in encoder.state_dict().items():
            self.assertTrue(torch.equal(v, model.auxiliary_heads.geometry_encoder.state_dict()[k]))
        optimizer = torch.optim.AdamW(parameter_groups(model, model.recipe))
        run.optimize_step(model, optimizer, Rows(batch, target), [('pose', [0])], 0, torch.device('cpu'), 1)
        artifact_path = directory/'export'
        with collectives(), patch('student_pilot.fsdp_training.publication_state', return_value=model.state_dict()):
            run.export(artifact_path, model, model, {'base_identity': 'fixture', 'trace_program_version': '3.13'}, 1)
        artifact = load(artifact_path/'artifact.json')
        self.assertEqual(artifact['geometry_online'], block)
        self.assertEqual(artifact['gx']['rms_cam'], float(rms))
        with patch.object(full_ft, 'load_export'):
            run.load_artifact(model, file_pin(artifact_path/'artifact.json'))
        with self.assertRaisesRegex(ValueError, 'geometry_online'):
            run.load_artifact(donor, file_pin(artifact_path/'artifact.json'))
        model.geometry_online = {**block, 'mode': 'frozen'}
        with self.assertRaisesRegex(ValueError, 'geometry_online'):
            run.load_artifact(model, file_pin(artifact_path/'artifact.json'))

    def test_native_checkpoint_preserves_geometry_adamw_without_transport(self):
        model, batch, target = model_fixture('finetune', hold_steps=0, warmup_steps=1)
        optimizer = torch.optim.AdamW(parameter_groups(model, model.recipe))
        rows = Rows(batch, target)
        run.optimize_step(model, optimizer, rows, [('pose', [0])], 0, torch.device('cpu'), 1)
        run.optimize_step(model, optimizer, rows, [('pose', [0])], 0, torch.device('cpu'), 2)
        encoder = model.auxiliary_heads.geometry_encoder
        expected = {k: v.clone() for k, v in encoder.state_dict().items()}
        moments = {n: copy.deepcopy(optimizer.state[p]) for n, p in encoder.named_parameters() if p.requires_grad}
        directory = root()
        def gather(out, value):
            out[0] = value
        with collectives(), patch.object(dist, 'all_gather_object', side_effect=gather):
            pin = run.checkpoint(directory/'checkpoint', model, optimizer, {}, 2)
            run.optimize_step(model, optimizer, rows, [('pose', [0])], 0, torch.device('cpu'), 3)
            self.assertEqual(run.restore(pin, model, optimizer, {}), 2)
        for name, p in encoder.named_parameters():
            self.assertTrue(torch.equal(p, expected[name]), name)
            if p.requires_grad:
                for key, value in moments[name].items():
                    self.assertTrue(torch.equal(optimizer.state[p][key], value), (name, key))

    def test_prepared_freezes_config_geometry_init_and_recipe(self):
        directory = root()
        write(directory/'database.json', {})
        write(directory/'indices.json', [0])
        write(directory/'model.json', dict(root='/fixture'))
        stream = dict(schema='c1-paired-prefix-v2', database=file_pin(directory/'database.json'),
                      count=1, dense_count=1, dense_indices=file_pin(directory/'indices.json'))
        write(directory/'stream.json', stream)
        cfg = configuration('finetune')
        cfg['streams'] = dict(pose=file_pin(directory/'stream.json'))
        write(directory/'code.json', dict(commit='new'))
        cfg['code'] = file_pin(directory/'code.json')
        cfg['trace_program_version'] = '3.13'
        cfg['init_artifact'] = dict(artifact=dict(path='/fixture/artifact.json', sha256='c'*64),
                                   lm='full', heads=['pose'])
        receipt = dict(schema='c1-preparation-v1', config_sha256='old', trainer_commit='old',
            streams=dict(pose=dict(receipt=cfg['streams']['pose'], database=stream['database'],
                                   count=1, indices=stream['dense_indices'])),
            carrier_placement=C1_A, training_mode='pose_only', frame_layout='duplicate',
            depth_enabled=False, recipe=RECIPE, camera={}, model=file_pin(directory/'model.json'))
        write(directory/'preparation.json', receipt)
        cfg['preparation'] = file_pin(directory/'preparation.json')
        with patch.object(run, 'authenticate', return_value='new'), patch.object(run, 'paired_prefix'):
            result, _ = run.prepared(cfg)
        for key in ('geometry_online', 'init_artifact', 'recipe'):
            self.assertEqual(result[key], cfg[key])


def fusion_settings(align_steps=2):
    return dict(pool='roi_area_merged_grid_v1', projector='layernorm_linear_gelu_linear_zero_out_v1',
                hidden=1024, align_steps=align_steps)


def patch_distributed_worker(rank, directory, port):
    torch.set_num_threads(1)
    dist.init_process_group('gloo', init_method=f'tcp://127.0.0.1:{port}', rank=rank, world_size=2)
    try:
        for mode in ('frozen', 'finetune'):
            model, batch, target = model_fixture(mode, patch_fusion=fusion_settings())
            batch['pixel_values_videos'] += rank * .13
            wrapped = run.wrap_model(model, torch.device('cpu'), mixed_precision=False)
            optimizer = torch.optim.AdamW(parameter_groups(wrapped, model.recipe))
            info, _ = run.optimize_step(wrapped, optimizer, Rows(batch, target), [('pose', [0, 1])],
                                        rank, torch.device('cpu'), 1, True)
            assert np.isfinite(info['components']['pose'])
            assert model.auxiliary_heads.patch_fusion.fc2.weight.grad.norm() > 0
            assert not model.model.visual._forward_hooks
            for p in model.auxiliary_heads.patch_fusion.parameters():
                other = p.detach().clone()
                dist.broadcast(other, src=0)
                assert torch.equal(p, other)
        if rank == 0:
            write(Path(directory)/'result.json', dict(status='PASS'))
    finally:
        dist.destroy_process_group()


class GXPTests(unittest.TestCase):
    def test_normalization_is_opt_in_and_validates_exact_contract(self):
        for mode in ('frozen', 'finetune'):
            block = settings(mode)
            self.assertEqual(json.dumps(gx.normalize(block)), json.dumps(block))
            self.assertNotIn('patch_fusion', gx.normalize(block))
            block['patch_fusion'] = fusion_settings(0)
            self.assertEqual(gx.normalize(block), block)
            for key, value in [('pool', 'other'), ('projector', 'other'), ('hidden', 512),
                               ('hidden', 1024.), ('align_steps', -1), ('align_steps', True),
                               ('align_steps', 1.), ('extra', 1)]:
                bad = copy.deepcopy(block)
                bad['patch_fusion'][key] = value
                with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                    gx.normalize(bad)
            for bad in (None, {}, {**fusion_settings(), 'hidden': True}):
                with self.assertRaises(ValueError):
                    gx.normalize({**block, 'patch_fusion': bad})
            cfg = configuration(mode)
            cfg['geometry_online'] = block
            cfg['init_artifact'] = dict(artifact=dict(path='/fixture/artifact.json', sha256='c'*64),
                                        lm='full', heads=['pose'])
            run.validate(cfg)

    def test_native_patch_halves_parity_checkpointing_and_gradients(self):
        for mode in ('frozen', 'finetune'):
            block = {**settings(mode), 'patch_fusion': fusion_settings()}
            encoder = gx.G3TEncoder(block, architecture(), image_size=28)
            images = torch.rand(3, 3, 28, 28)
            actual = encoder(images)
            with torch.no_grad():
                native, start = encoder.aggregator(images[None])
            self.assertEqual(start, 5)
            self.assertTrue(encoder.parity['bitwise'])
            self.assertTrue(torch.equal(actual[0], native[-1][0, :, 0]))
            self.assertTrue(torch.equal(actual[3], native[-1][0, :, 5:]))
            self.assertEqual(actual[3].shape, (3, 4, 64))
            self.assertEqual(actual[3].requires_grad, mode == 'finetune')
            if mode == 'finetune':
                actual[3].square().mean().backward()
                gradients = {n: p.grad.clone() for n, p in encoder.named_parameters() if p.grad is not None}
                encoder.zero_grad(set_to_none=True)
                encoder.settings['finetune']['checkpointing'] = True
                checked = encoder(images)
                self.assertTrue(torch.equal(checked[3], actual[3]))
                checked[3].square().mean().backward()
                for name, p in encoder.named_parameters():
                    if name in gradients:
                        torch.testing.assert_close(p.grad, gradients[name], atol=1e-6, rtol=1e-6)
                self.assertGreater(float(encoder.aggregator.frame_blocks[-1].attn.qkv.weight.grad.norm()), 0.)

    def test_fp32_roi_pooling_matches_reference_order_and_is_differentiable(self):
        from student_pilot.c1r_ref import pool_patches
        from student_pilot.g3t_online import pool_patches_online
        torch.manual_seed(11)
        for gh, gw in ((2, 2), (4, 8), (8, 4)):
            tokens = torch.randn(32, 37*37, 7, requires_grad=True)
            start = torch.rand(32, 2) * 200
            end = 824 + torch.rand(32, 2) * 200
            coords = torch.cat([start, end], -1)
            grid = torch.tensor([32, gh, gw])
            mapping = np.repeat(np.arange(32), 2)
            expected = pool_patches_online(tokens, coords, grid.numpy(), mapping, dtype=torch.float32)
            with torch.autocast('cpu', dtype=torch.bfloat16):
                actual = gx.pool_patch_features(tokens, coords, grid)
            self.assertEqual(actual.dtype, torch.float32)
            self.assertTrue(torch.equal(actual, expected.reshape(-1, 7)))
            self.assertTrue(torch.equal(actual.half(), pool_patches(tokens, coords, grid, mapping).reshape(-1, 7)))
            actual.square().mean().backward()
            self.assertTrue(torch.isfinite(tokens.grad).all())
            self.assertGreater(float(tokens.grad.abs().sum()), 0.)
        ids = torch.arange(32.).reshape(32, 1, 1).expand(-1, 37*37, 1)
        values = gx.pool_patch_features(ids, torch.tensor([0., 0., 1024., 1024.]).repeat(32, 1), [32, 4, 6])
        torch.testing.assert_close(values.reshape(32, 2, 3)[..., 0, 0], torch.arange(32.))
        for coords, grid in ((torch.zeros(32, 4), [32, 2, 2]),
                             (torch.ones(32, 4), [31, 2, 2])):
            with self.assertRaises(ValueError):
                gx.pool_patch_features(ids, coords, grid)

    def test_step_zero_bitwise_hidden_loss_readout_and_generate(self):
        plain, batch, target = model_fixture()
        plain.eval()
        with torch.no_grad():
            hidden, loss, pose = plain.hidden(batch), plain(batch, target)['loss'], plain.pose_readout(batch)
            generated = plain.generate(batch, max_new_tokens=2, do_sample=False, pad_token_id=0, eos_token_id=1)
        for mode in ('frozen', 'finetune'):
            gxc, _, _ = model_fixture(mode)
            model, _, _ = model_fixture(mode, patch_fusion=fusion_settings())
            model.eval(); gxc.eval()
            projector = model.auxiliary_heads.patch_fusion
            self.assertEqual(projector.norm.normalized_shape, (2048,))
            self.assertEqual(projector.fc1.out_features, 1024)
            self.assertEqual(projector.fc2.out_features, model.config.vision_config.out_hidden_size)
            with torch.no_grad():
                self.assertTrue(torch.equal(model.hidden(batch), hidden))
                self.assertTrue(torch.equal(model.hidden(batch), gxc.hidden(batch)))
                self.assertTrue(torch.equal(model(batch, target)['loss'], loss))
                self.assertTrue(torch.equal(model(batch, target)['loss'], gxc(batch, target)['loss']))
                self.assertTrue(np.array_equal(model.pose_readout(batch), pose))
                self.assertTrue(np.array_equal(model.pose_readout(batch), gxc.pose_readout(batch)))
                self.assertEqual(model.gx_metrics['patch_delta_ratio'], 0.)
                self.assertTrue(torch.equal(model.generate(batch, max_new_tokens=2, do_sample=False,
                    pad_token_id=0, eos_token_id=1), generated))
            self.assertFalse(model.model.visual._forward_hooks)

    def test_native_multivideo_features_follow_each_merged_grid(self):
        model, batch, _ = model_fixture('frozen', patch_fusion=fusion_settings())
        model.geometry_online['input'] = gx.NATIVE_INPUT
        grids = torch.tensor([[32, 4, 6], [32, 6, 4]])
        coords = torch.tensor([0., 128., 1024., 896.]).expand(2, 32, -1)
        images = torch.zeros(1).expand(2, 32, 3, 518, 518)
        batch = {**batch, 'input_ids': batch['input_ids'].repeat(2, 1), 'video_grid_thw': grids,
                 'aux_g3t_images': images, 'aux_g3t_coords': coords}
        calls = []
        def fake(encoder, image, box):
            index = len(calls)
            calls.append((image, box))
            tokens = (torch.arange(32.) + index * 100)[:, None, None].expand(-1, 37*37, 2048)
            return torch.full((32, 2058), float(index+1)), tokens
        with patch.object(gx, 'features', side_effect=fake), \
             patch.object(gx, 'student_frames', side_effect=AssertionError('native input was inverted')):
            camera, patches = model.geometry_features(batch)
            self.assertEqual(camera.shape, (2, 32, 2058))
            self.assertTrue(torch.equal(camera[:, 0, 0], torch.tensor([1., 2.])))
            expected = torch.cat([torch.arange(32.).repeat_interleave(6),
                                  (torch.arange(32.)+100).repeat_interleave(6)])
            self.assertEqual(patches.shape, (2*32*6, 2048))
            torch.testing.assert_close(patches[:, 0], expected)
            for i, (image, box) in enumerate(calls):
                self.assertTrue(torch.equal(image, images[i]))
                self.assertTrue(torch.equal(box, coords[i]))
            model.gx_zero_feature = True
            camera, patches = model.geometry_features(batch)
            self.assertEqual(torch.count_nonzero(camera), 0)
            self.assertEqual(torch.count_nonzero(patches), 0)
            with self.assertRaisesRegex(ValueError, 'one video grid'):
                model.geometry_features({**batch, 'video_grid_thw': grids[:1]})

    def test_hook_video_only_exact_delta_once_and_cleanup(self):
        from transformers.modeling_outputs import BaseModelOutputWithPooling
        class Visual(torch.nn.Module):
            def forward(self, tokens, grid_thw):
                return BaseModelOutputWithPooling(last_hidden_state=tokens, pooler_output=tokens.clone())
        projector = gx.PatchFusion(8)
        torch.nn.init.normal_(projector.fc2.weight, std=.01)
        visual, metrics = Visual(), {}
        grid, image_grid = torch.tensor([[32, 2, 2]]), torch.tensor([[32, 2, 2]])
        features, tokens = torch.randn(32, 2048), torch.randn(32, 8)
        expected = tokens + projector(features)
        with projector.inject(visual, features, grid, metrics):
            image = visual(tokens, image_grid)
            self.assertTrue(torch.equal(image.pooler_output, tokens))
            result = visual(tokens, grid).pooler_output
            self.assertTrue(torch.equal(result, expected))
            self.assertAlmostEqual(metrics['patch_delta_ratio'], float(projector(features).detach().square().mean().sqrt() /
                tokens.square().mean().sqrt()))
            with self.assertRaisesRegex(ValueError, 'consumed twice'):
                visual(tokens, grid)
        self.assertFalse(visual._forward_hooks)
        self.assertTrue(torch.equal(visual(tokens, grid).pooler_output, tokens))
        for values in (features[:-1], features[:, :-1]):
            with self.assertRaisesRegex(ValueError, 'token count'):
                with projector.inject(visual, values, grid, metrics):
                    visual(tokens, grid)
            self.assertFalse(visual._forward_hooks)
        with self.assertRaisesRegex(ValueError, 'not consumed'):
            with projector.inject(visual, features, grid, metrics):
                pass
        with self.assertRaisesRegex(RuntimeError, 'interrupted'):
            with projector.inject(visual, features, grid, metrics):
                raise RuntimeError('interrupted')
        self.assertFalse(visual._forward_hooks)
        class TupleVisual(torch.nn.Module):
            def forward(self, tokens, grid_thw):
                return (tokens, tokens.clone(), 'retained')
        visual = TupleVisual()
        with projector.inject(visual, features, grid, metrics):
            result = visual(tokens, grid)
            self.assertTrue(torch.equal(result[0], tokens))
            self.assertTrue(torch.equal(result[1], expected))
            self.assertEqual(result[2], 'retained')

    def test_hidden_and_generation_prefill_add_nonzero_delta(self):
        model, batch, _ = model_fixture('frozen', patch_fusion=fusion_settings())
        model.eval()
        embedding_hooks = dict(model.get_input_embeddings()._forward_hooks)
        projector = model.auxiliary_heads.patch_fusion
        torch.nn.init.normal_(projector.fc2.weight, std=.02)
        with torch.no_grad():
            _, features = model.geometry_features(batch)
            delta = projector(features)
            base = model.model.visual(batch['pixel_values_videos'], grid_thw=batch['video_grid_thw']).pooler_output
            expected = base + delta
            seen = []
            original = projector.inject
            from contextlib import contextmanager
            @contextmanager
            def capture(*args):
                with original(*args):
                    hook = model.model.visual.register_forward_hook(
                        lambda m, a, k, o: seen.append(o.pooler_output.clone()), with_kwargs=True)
                    try:
                        yield
                    finally:
                        hook.remove()
            with patch.object(projector, 'inject', side_effect=capture):
                model.hidden(batch)
                model.hidden(batch, carriers=False)
                model.generate(batch, max_new_tokens=2, do_sample=False, pad_token_id=0, eos_token_id=1)
            self.assertEqual(len(seen), 3)
            for value in seen:
                self.assertTrue(torch.equal(value, expected))
            self.assertGreater(model.gx_metrics['patch_delta_ratio'], 0.)
            self.assertFalse(model.model.visual._forward_hooks)
            with patch.object(model.model, 'forward', side_effect=RuntimeError('failed')):
                with self.assertRaisesRegex(RuntimeError, 'failed'):
                    model.hidden(batch)
            self.assertFalse(model.model.visual._forward_hooks)
            self.assertEqual(dict(model.get_input_embeddings()._forward_hooks), embedding_hooks)

    def test_patch_only_gradients_frozen_and_finetuned_encoder(self):
        for mode in ('frozen', 'finetune'):
            model, batch, target = model_fixture(mode, patch_fusion=fusion_settings(0))
            encoder = model.auxiliary_heads.geometry_encoder
            projector = model.auxiliary_heads.patch_fusion
            torch.nn.init.normal_(projector.fc2.weight, std=.02)
            # Detach CAM geometry so only the patch path can train the aggregator.
            original = model.carrier_embeddings
            with patch.object(model, 'carrier_embeddings', side_effect=lambda output, pos, g3t:
                              original(output, pos, g3t.detach())):
                model(batch, target)['loss'].backward()
            self.assertGreater(float(projector.fc1.weight.grad.norm()), 0.)
            self.assertGreater(float(projector.fc2.weight.grad.norm()), 0.)
            if mode == 'frozen':
                self.assertTrue(all(p.grad is None for p in encoder.parameters()))
            else:
                self.assertTrue(any(p.grad is not None and p.grad.norm() > 0
                                    for p in encoder.aggregator.parameters()))
                self.assertTrue(all(p.grad is None for p in encoder.local_camera_head.parameters()))

    def test_alignment_lr_boundary_parameter_updates_and_original_g3t_clock(self):
        for scale in (1., .25):
            model, batch, target = model_fixture('finetune', patch_fusion=fusion_settings(2),
                                                hold_steps=1, warmup_steps=4)
            groups = parameter_groups(model, model.recipe, pose_lr_scale=scale)
            heads = next(g for g in groups if g['name'] == 'heads')
            self.assertTrue(all(any(p is q for q in heads['params'])
                                for p in model.auxiliary_heads.patch_fusion.parameters()))
            optimizer = torch.optim.AdamW(groups, weight_decay=.01)
            aligned = {id(p) for g in groups if g['gx_alignment'] for p in g['params']}
            for step in (1, 2, 3):
                before = {n: p.clone() for n, p in model.named_parameters() if p.requires_grad}
                run.optimize_step(model, optimizer, Rows(batch, target), [('pose', [0])],
                                  0, torch.device('cpu'), step)
                for group in optimizer.param_groups:
                    expected = run.learning_rate(step, {**model.recipe, 'learning_rate': group['initial_lr']})
                    if group['name'] == 'geometry_encoder':
                        expected *= gx.learning_rate_ramp(model.geometry_online, step)
                    if step <= 2 and not group['gx_alignment']:
                        expected = 0.
                    self.assertEqual(group['lr'], expected)
                if step <= 2:
                    for name, p in model.named_parameters():
                        if p.requires_grad and id(p) not in aligned:
                            self.assertTrue(torch.equal(p, before[name]), name)
                else:
                    for prefix in ('model.language_model.', 'auxiliary_heads.pose.head.',
                                   'auxiliary_heads.geometry_encoder.aggregator.'):
                        self.assertTrue(any(not torch.equal(p, before[n]) for n, p in model.named_parameters()
                                            if p.requires_grad and n.startswith(prefix)), prefix)

    def test_planned_warmstart_export_and_strict_reload(self):
        donor, _, _ = model_fixture()
        directory = root()/'donor'
        with collectives(), patch('student_pilot.fsdp_training.publication_state', return_value=donor.state_dict()):
            run.export(directory, donor, donor, {'base_identity': 'fixture', 'trace_program_version': '3.13'}, 0)
        model, _, _ = model_fixture('frozen', patch_fusion=fusion_settings())
        spec = dict(artifact=file_pin(directory/'artifact.json'), lm='base', heads=['pose'])
        report = run.init_from_artifact(model, spec)
        expected = sorted(k for k in model.auxiliary_heads.state_dict()
                          if k.startswith(('pose.cam_token_connector.', 'patch_fusion.')))
        self.assertEqual(report['planned_init'], expected)
        torch.nn.init.normal_(model.auxiliary_heads.patch_fusion.fc2.weight, std=.01)
        exported = root()/'export'
        with collectives(), patch('student_pilot.fsdp_training.publication_state', return_value=model.state_dict()):
            run.export(exported, model, model, {'base_identity': 'fixture', 'trace_program_version': '3.13'}, 1)
        state = torch.load(exported/'heads.pt', weights_only=True)
        self.assertTrue(all(torch.equal(state['patch_fusion.'+k], v)
                            for k, v in model.auxiliary_heads.patch_fusion.state_dict().items()))
        with patch.object(full_ft, 'load_export'):
            run.load_artifact(model, file_pin(exported/'artifact.json'))
            missing = {k: v for k, v in state.items() if k != 'patch_fusion.fc2.weight'}
            bad = root()
            torch.save(missing, bad/'heads.pt')
            artifact = load(exported/'artifact.json')
            artifact['heads'] = file_pin(bad/'heads.pt')
            write(bad/'artifact.json', artifact)
            with self.assertRaisesRegex(RuntimeError, 'Missing key'):
                run.load_artifact(model, file_pin(bad/'artifact.json'))

    @unittest.skipUnless(SOCKETS, 'Local gloo sockets required')
    def test_two_rank_gxp_first_batch_forward_backward(self):
        directory = root()
        run_workers(patch_distributed_worker, (str(directory),))
        self.assertEqual(load(directory/'result.json')['status'], 'PASS')


if __name__ == '__main__':
    unittest.main()
