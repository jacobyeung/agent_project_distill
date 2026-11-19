"""Retained CPU regressions for GX readout and authenticated recovery."""
import copy
import json
import gzip
import os
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import numpy as np
import torch

from student_pilot import carrier_c1_run as run, carrier_c1_data as data, g3t_online as gx
from student_pilot.p3_provenance import write, load, file_pin
from tests.test_gx_carrier import configuration, root, collectives, model_fixture
from tests.test_carrier_c1 import Tokenizer
from tests.test_carrier_c1_layout import raw_batch


def ranks(step, loss=2., world=8):
    return [dict(step=step, shapes=[dict(gx=dict(delta_ratio=.1))],
                 stream_means=dict(pose=loss), wall_seconds=0.) for _ in range(world)]


def metric_file(directory, name, steps, loss=2., world=8, tail=''):
    records = [dict(step=s, ranks=ranks(s, loss, world)) for s in steps]
    (directory/f'metrics_{name}.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in records)+tail)
    return records


def reference_receipts(cfg, directory, *, full_config=False, world=8):
    """Write the native B0 legacy receipt shapes, without inventing a config receipt."""
    ref = copy.deepcopy(cfg)
    ref.pop('geometry_online', None)
    ref['recipe'].pop('geometry_learning_rate', None)
    ref['recipe'].update(world_size=world, mix=['pose']*(32//world))
    ref['output'] = str(directory)
    prep = dict(schema='c1-preparation-v1', training_mode='pose_only', recipe=ref['recipe'],
                row_start_step=ref.get('row_start_step', 0), streams={'pose': {'count': 97}})
    write(directory/'preparation.json', prep)
    cfg['preparation'] = ref['preparation'] = file_pin(directory/'preparation.json')
    bound = dict(config_sha256=run.identity(ref), preparation=ref['preparation'],
                 trainer_commit='CTRL-B0', world_size=world)
    write(directory/'binding.json', bound)
    cfg['geometry_online']['fail_fast']['reference_binding'] = dict(
        sha256=file_pin(directory/'binding.json')['sha256'], config_sha256=bound['config_sha256'],
        trainer_commit=bound['trainer_commit'])
    attempt = dict(binding=bound, resume=None, first_step=1, network=None, init=None, export_of=None)
    if full_config:
        attempt['config'] = ref
    write(directory/'attempt_ctrl.json', attempt)
    return ref, bound


def paired_cfg(directory, reference, steps=70):
    cfg = configuration('finetune')
    cfg.update(output=str(directory), steps=steps, milestones=[])
    cfg['recipe'] = run.recipe_for(cfg)
    cfg['geometry_online']['fail_fast'] = dict(step=70, min_delta_ratio=.01, max_loss_ratio=1.2,
                                             reference=str(reference))
    return cfg


def completed(directory, name, bound, records, resume=None):
    first = load(resume['path'])['step']+1 if resume else 1
    write(directory/f'attempt_{name}.json', dict(binding=bound, resume=resume, first_step=first, export_of=None))
    write(directory/f'run_{name}.json', dict(schema='c1-run-v1', status='PASS', first_step=first,
          last_step=records[-1]['step'], world_size=bound['world_size'], binding=bound,
          steps=[r['ranks'] for r in records]))


class S6RecoveryTests(unittest.TestCase):
    def test_every_byte_prefix_of_metrics_write_is_recoverable(self):
        directory = root(); path = directory/'metrics_cpu.jsonl'
        first = json.dumps(dict(step=1, ranks=ranks(1, world=1)))+'\n'
        second = json.dumps(dict(step=2, ranks=[{**ranks(2, world=1)[0],
                            'text': 'snowman \u2603', 'nullable': None, 'flag': True, 'tiny': -1.23e-12}]))
        for cut in range(len(second)):
            path.write_text(first+second[:cut])
            with self.subTest(cut=cut):
                self.assertEqual(len(run.gx_step_history(directory, 2)), 1)

    def test_metrics_partial_tail_and_corrupt_middle_in_both_histories(self):
        for tail in ('{"step": 71, "ranks": [', '{"step": 71, "ranks": [{"stream_means": "par'):
            directory = root()
            metric_file(directory, 'ctrl', range(1, 71), tail=tail)
            self.assertEqual(len(run.gx_step_history(directory, 70)), 70)
            cfg = paired_cfg(root(), directory)
            reference_receipts(cfg, directory)
            self.assertEqual(len(run.gx_reference(cfg, 70)), 70)
        for broken in ('{bad}\n', '{bad}', '{"step": 71, "ranks": [\n',
                       '{"step": 2, "step": 3, "ranks": []}\n',
                       '{"step": 2, "ranks": [{"step": 2, "loss": NaN}]}\n',
                       '{"step": 71, "ranks": [\n'+json.dumps(dict(step=72, ranks=ranks(72)))+'\n'):
            directory = root()
            metric_file(directory, 'ctrl', [1], tail=broken)
            cfg = paired_cfg(root(), directory)
            reference_receipts(cfg, directory)
            with self.subTest(broken=broken):
                with self.assertRaises((ValueError, json.JSONDecodeError)):
                    run.gx_step_history(directory, 1)
                with self.assertRaises((ValueError, json.JSONDecodeError)):
                    run.gx_reference(cfg, 1)
        # A writer may finish its last line between two reader calls. Read only
        # the opening byte extent so its continuation cannot become a corrupt middle line.
        directory = root(); path = directory/'metrics_live.jsonl'
        next_record = json.dumps(dict(step=2, ranks=ranks(2)))+'\n'
        cut = len(next_record)//2
        metric_file(directory, 'live', [1], tail=next_record[:cut])
        original_open = Path.open
        class LiveReader:
            def __init__(self, handle):
                self.handle = handle
            def __enter__(self):
                return self
            def __exit__(self, *args):
                self.handle.close()
            def fileno(self):
                return self.handle.fileno()
            def readline(self, *args):
                line = self.handle.readline(*args)
                newline = b'\n' if isinstance(line, bytes) else '\n'
                if line and not line.endswith(newline):
                    with original_open(path, 'a') as writer:
                        writer.write(next_record[cut:])
                return line
        def opening(target, *args, **kwargs):
            handle = original_open(target, *args, **kwargs)
            return LiveReader(handle) if target == path else handle
        with patch.object(Path, 'open', opening):
            self.assertEqual(len(run.gx_step_history(directory, 2)), 1)
        self.assertEqual(len(run.gx_step_history(directory, 2)), 2)

    def test_crash_after_complete_checkpoint_recovers_window_without_metrics(self):
        directory, reference = root(), root()
        cfg = paired_cfg(directory, reference)
        reference_receipts(cfg, reference)
        metric_file(reference, 'ctrl', range(1, 71))
        bound = dict(config_sha256=run.identity(cfg), preparation=cfg['preparation'], trainer_commit='S6', world_size=1)
        run.bind_output(directory, bound, cfg=cfg)
        model = torch.nn.Linear(2, 1)
        model.trace_program_version = cfg['trace_program_version']
        optimizer = torch.optim.AdamW(model.parameters())
        stop = [False]
        def optimize(*args):
            step = args[6]
            if step == 65:
                stop[0] = True
            return ranks(step, world=1)[0], None
        original_open = Path.open
        def interrupted(path, *args, **kwargs):
            if path.name == 'metrics_crash.jsonl':
                raise OSError('simulated crash after complete checkpoint')
            return original_open(path, *args, **kwargs)
        with collectives(), patch.object(run.dist, 'all_gather_object', side_effect=lambda out, v: out.__setitem__(0, v)), \
             patch.object(run, 'optimize_step', side_effect=optimize), patch.dict(os.environ, SLURM_JOB_ID='crash'):
            with patch.object(Path, 'open', interrupted), self.assertRaisesRegex(OSError, 'simulated crash'):
                run.run_steps(model, model, optimizer, None, {'pose': 97}, directory, cfg, bound,
                              torch.device('cpu'), start_step=64, stop=stop, distributed=False,
                              resume_history=[ranks(s, world=1) for s in range(1, 65)])
            pin = run.latest_resume(directory, bound, cfg=cfg)
            saved = load(pin['path'])
            self.assertEqual(saved['step'], 65)
            self.assertEqual(saved['gx_attempt'], 'crash')
            self.assertEqual(len(saved['gx_history']), 65)
            self.assertFalse((directory/'metrics_crash.jsonl').exists())
            self.assertEqual(run.restore(pin, model, optimizer, bound), 65)
            with patch.dict(os.environ, SLURM_JOB_ID='resume'):
                report = run.run_steps(model, model, optimizer, None, {'pose': 97}, directory, cfg, bound,
                                      torch.device('cpu'), start_step=65, distributed=False,
                                      resume_history=saved['gx_history'])
            self.assertEqual(report['last_step'], 70)
            self.assertEqual(load(directory/'gx_fail_fast_resume_step_000070.json')['verdict'], 'CONTINUE')
            self.assertEqual(len(load(run.latest_resume(directory, bound, cfg=cfg)['path'])['gx_history']), 70)

    def test_rebind_chain_replays_authenticated_milestones_and_records_code_pins(self):
        directory = root()
        cfg = configuration(); cfg.update(output=str(directory), code={'path': '/seal/A', 'sha256': 'a'*64})
        cfg['geometry_online']['fail_fast'] = dict(step=50, min_delta_ratio=.01, max_loss_ratio=2.)
        old = dict(config_sha256=run.identity(cfg), preparation={'fixture': True}, trainer_commit='A', world_size=1)
        run.bind_output(directory, old, cfg=cfg)
        model = torch.nn.Linear(2, 1); optimizer = torch.optim.AdamW(model.parameters())
        model.trace_program_version = cfg['trace_program_version']
        with collectives(), patch.object(run.dist, 'all_gather_object', side_effect=lambda out, v: out.__setitem__(0, v)):
            pin = run.checkpoint(directory/'checkpoint_000002', model, optimizer, old, 2)
        identities = [run.identity(cfg)]
        for commit in ('B', 'C'):
            new = copy.deepcopy(cfg)
            new['code'] = dict(path='/seal/'+commit, sha256=commit.lower()*64)
            new['geometry_online']['fail_fast']['max_loss_ratio'] += .1
            bound = {**old, 'trainer_commit': commit, 'config_sha256': run.identity(new)}
            rebind = run.bind_output(directory, bound, resume=True, cfg=new, resume_pin=pin)
            record = load(rebind['path'])
            self.assertEqual(record['previous_code'], cfg['code'])
            self.assertEqual(record['code'], new['code'])
            cfg = new; identities.append(run.identity(cfg))
        for i, config_sha in enumerate(identities+['foreign']):
            target = directory/f'm{i}'
            write(target/'weights.json', {'fixture': True}); write(target/'heads.json', {'fixture': True})
            write(target/'artifact.json', dict(schema='carrier-c1-artifact-v1', step=i, config_sha256=config_sha,
                  full_weights=file_pin(target/'weights.json'), heads=file_pin(target/'heads.json')))
            if config_sha == 'foreign':
                with self.assertRaises(ValueError):
                    run.existing_export(target, cfg, i)
            else:
                self.assertTrue(run.existing_export(target, cfg, i))
        other = {**cfg, 'row_start_step': 1}
        with self.assertRaises(ValueError):
            run.gx_rule_rebind(old, {**old, 'trainer_commit': 'C', 'config_sha256': run.identity(other)}, other,
                               run.stored_config(directory, old))

    def test_code_transition_requires_commit_change(self):
        cfg = configuration(); cfg['code'] = {'path': '/A', 'sha256': 'a'*64}
        old = dict(config_sha256=run.identity(cfg), preparation={}, trainer_commit='A', world_size=8)
        for commit, change_rule, accepted in [('A', True, False), ('B', False, True), ('B', True, True)]:
            current = copy.deepcopy(cfg); current['code'] = {'path': '/B', 'sha256': 'b'*64}
            if change_rule:
                current['geometry_online']['fail_fast'] = dict(step=50, min_delta_ratio=.1, max_loss_ratio=2.)
            bound = {**old, 'trainer_commit': commit, 'config_sha256': run.identity(current)}
            if accepted:
                run.gx_rule_rebind(old, bound, current, cfg)
            else:
                with self.assertRaises(ValueError):
                    run.gx_rule_rebind(old, bound, current, cfg)

    def test_reference_row_schedule_and_prep_mismatches_refuse_before_cuda(self):
        for key in ('row_start_step', 'seed', 'mix', 'global_batch', 'streams', 'preparation'):
            reference = root(); cfg = paired_cfg(root(), reference)
            ref, bound = reference_receipts(cfg, reference, full_config=True)
            metric_file(reference, 'ctrl', [1])
            if key == 'row_start_step':
                ref[key] = 800
            elif key == 'streams':
                ref[key] = {'pose': {'foreign': True}}
            elif key == 'preparation':
                cfg[key] = {'path': '/foreign', 'sha256': 'f'*64}
            else:
                ref['recipe'][key] = {'seed': 18, 'mix': ['pose']*3+['vqa'], 'global_batch': 16}[key]
            bound['config_sha256'] = run.identity(ref)
            (reference/'binding.json').write_text(json.dumps(bound))
            (reference/'attempt_ctrl.json').write_text(json.dumps(dict(binding=bound, config=ref, resume=None, first_step=1)))
            # Validate only the fixture's full training schema; CUDA must never be queried.
            with self.subTest(key=key), patch.object(run, 'validate'), \
                 patch.object(torch.cuda, 'is_available', side_effect=AssertionError('CUDA startup reached')):
                with self.assertRaises(ValueError):
                    run.train(cfg)

    def test_reference_world_microstep_equivalence_and_completed_legacy_receipts(self):
        reference = root(); cfg = paired_cfg(root(), reference)
        _, bound = reference_receipts(cfg, reference)
        records = metric_file(reference, 'ctrl', range(1, 4))
        write(reference/'run_ctrl.json', dict(schema='c1-run-v1', status='PASS', first_step=1, last_step=3,
              world_size=8, binding=bound, steps=[r['ranks'] for r in records]))
        before = run.identity(cfg), copy.deepcopy(cfg['recipe'])
        self.assertEqual(len(run.gx_reference(cfg, 3)), 3)
        cfg['world_size'] = 4; cfg['recipe'] = run.recipe_for(cfg)
        self.assertEqual(len(run.gx_reference(cfg, 3)), 3)
        eight = list(data.mixed_indices({'pose': 97}, 3, mix=['pose']*4, world=8, training_mode='pose_only'))
        four = list(data.mixed_indices({'pose': 97}, 3, mix=['pose']*8, world=4, training_mode='pose_only'))
        self.assertEqual([[i for _, ids in plan for i in ids] for plan in eight],
                         [[i for _, ids in plan for i in ids] for plan in four])
        cfg.pop('world_size'); cfg['recipe'] = run.recipe_for(cfg)
        self.assertEqual((run.identity(cfg), cfg['recipe']), before)

    def test_reference_duplicates_follow_resume_pin_not_mtime_and_reject_forks(self):
        reference = root(); cfg = paired_cfg(root(), reference)
        _, bound = reference_receipts(cfg, reference)
        # Retain the fixture root receipt under its native name.
        original = metric_file(reference, 'ctrl', range(1, 5), loss=1.)
        write(reference/'run_ctrl.json', dict(schema='c1-run-v1', status='PASS', first_step=1, last_step=4,
              world_size=8, binding=bound, steps=[r['ranks'] for r in original]))
        checkpoint = reference/'checkpoint_000002'/'complete.json'
        write(checkpoint, dict(schema='c1-checkpoint-v1', binding=bound, step=2))
        newer = metric_file(reference, 'resumed', range(3, 7), loss=3.)
        completed(reference, 'resumed', bound, newer, file_pin(checkpoint))
        os.utime(reference/'metrics_ctrl.jsonl', (2_000_000_000, 2_000_000_000))
        history = run.gx_reference(cfg, 6)
        self.assertEqual(history[2][0]['stream_means']['pose'], 1.)
        self.assertEqual(history[3][0]['stream_means']['pose'], 3.)
        write(reference/'attempt_fork.json', dict(binding=bound, resume=file_pin(checkpoint), first_step=3))
        with self.assertRaisesRegex(ValueError, 'forked'):
            run.gx_reference(cfg, 6)

    def test_reference_rejects_unreceipted_metrics_and_changed_completed_records(self):
        with self.assertRaisesRegex(ValueError, 'authenticated reference snapshot'):
            run.gx_fail_fast([ranks(s) for s in range(1, 11)],
                            dict(step=10, min_delta_ratio=.01, max_loss_ratio=1.2, reference=str(root())))
        for failure in ('unreceipted', 'changed', 'foreign_attempt', 'wrong_world', 'changed_config'):
            reference = root(); cfg = paired_cfg(root(), reference)
            _, bound = reference_receipts(cfg, reference)
            records = metric_file(reference, 'ctrl', [1])
            write(reference/'run_ctrl.json', dict(schema='c1-run-v1', status='PASS', first_step=1, last_step=1,
                  world_size=8, binding=bound, steps=[records[0]['ranks']]))
            if failure == 'unreceipted':
                metric_file(reference, 'foreign', [1])
            elif failure == 'changed':
                metric_file(reference, 'ctrl', [1], loss=99.)
            elif failure == 'wrong_world':
                metric_file(reference, 'ctrl', [1], world=4)
            elif failure == 'changed_config':
                (reference/'attempt_ctrl.json').write_text(json.dumps(dict(
                    binding=bound, config={'row_start_step': 800}, first_step=1, resume=None)))
            else:
                (reference/'attempt_ctrl.json').write_text(json.dumps(dict(
                    binding={**bound, 'trainer_commit': 'foreign'}, first_step=1, resume=None)))
            with self.subTest(failure=failure), self.assertRaises(ValueError):
                run.gx_reference(cfg, 1)


class S6NativeReadoutTests(unittest.TestCase):
    def test_unlabeled_vqa_mode_x_native_readout_and_default_tensor_bytes(self):
        model, _, _ = model_fixture('frozen')
        model.eval(); model.geometry_online['input'] = gx.NATIVE_INPUT
        processor = SimpleNamespace(tokenizer=Tokenizer(), video_processor=SimpleNamespace(merge_size=2))
        inputs = dict(frames=[dict(path='/fixture/rgb', sha256='a'*64)]*32, frame_indices=list(range(0, 128, 4)),
                      timestamps=[i/10 for i in range(0, 128, 4)], fps=10., total_num_frames=400,
                      question='Pose?', options=[], recording_id='recording')
        images = torch.zeros(32, 3, 518, 518, dtype=torch.float16)
        coords = torch.zeros(32, 4)
        for layout in ('duplicate', 'paired'):
            model.frame_layout = layout
            source = np.arange((32 if layout == 'duplicate' else 64)*6*8*3,
                               dtype=np.int64).astype(np.uint8).reshape(-1, 6, 8, 3)
            row = dict(qid='readout', student_input=copy.deepcopy(inputs), target=data.READOUT_TARGET)
            if layout == 'paired':
                row['student_input']['partner_frames'] = [dict(path='/fixture/pair', sha256='b'*64,
                    frame_index=i+1, timestamp=(i+1)/10, recording_id='recording') for i in inputs['frame_indices']]
            options = dict(frame_layout=layout, frame_pair_gap_seconds=.1 if layout == 'paired' else None)
            raw = raw_batch(32)
            with patch('student_pilot.pose_samples.load_frames', return_value=source), \
                 patch('student_pilot.pose_samples.encode_frames', side_effect=lambda *a: (copy.deepcopy(raw), {'fixed': True})), \
                 patch('student_pilot.pose_samples.augment', side_effect=AssertionError('unlabeled augmentation')), \
                 patch.object(gx, 'native_square_518', return_value=(images, coords)) as native:
                legacy, _, audit = data.encode(processor, row, {}, 'vqa', **options)
                default, _, default_audit = data.encode(processor, row, {}, 'vqa',
                                                       geometry_online={**model.geometry_online, 'input': gx.INPUT}, **options)
                native.assert_not_called()
                batch, targets, native_audit = data.encode(processor, row, {}, 'vqa',
                                                          geometry_online=model.geometry_online, **options)
                np.testing.assert_array_equal(native.call_args.args[0], source[::2] if layout == 'paired' else source)
                # The production processor also carries the native readout setting for callers
                # that use the mode-x encode(..., {}, 'vqa', ...) signature unchanged.
                with patch.object(run, 'processor_for', return_value=processor):
                    bound_processor = run.processor_for_receipt({'root': '/fixture'},
                        {'geometry_online': model.geometry_online})
                implicit, _, _ = data.encode(bound_processor, row, {}, 'vqa', **options)
                for key in batch:
                    self.assertTrue(torch.equal(batch[key], implicit[key]))
                del processor._c1_readout_geometry_online
            self.assertIsNone(targets)
            self.assertEqual(audit, default_audit); self.assertEqual(audit, native_audit)
            self.assertEqual(set(batch)-set(legacy), {'aux_g3t_images', 'aux_g3t_coords'})
            for key in legacy:
                self.assertEqual(legacy[key].numpy().tobytes(), default[key].numpy().tobytes())
                self.assertEqual(legacy[key].numpy().tobytes(), batch[key].numpy().tobytes())
            # This is the mode-x sequence: encode an unlabeled VQA prefix, then real model.readout.
            with patch.object(model.auxiliary_heads.geometry_encoder, 'forward',
                              return_value=(torch.ones(32, 2048), torch.ones(32, 6), torch.ones(32, 5))), \
                 patch.object(gx, 'pose9', return_value=(torch.ones(32, 9), None)), \
                 patch.object(gx, 'disagreement', return_value=torch.ones(32, 1)), torch.no_grad():
                self.assertEqual(np.shape(model.readout(batch, np.zeros((32, 1, 2)))['raw_pose']), (32, 9))

    def test_evaluate_sparse_and_contiguous_pass_native_config_and_probe_retains_it(self):
        from student_pilot.compact_label_bank import frame_set_sha256
        from student_pilot import carrier_c1_clip as clip
        from tests.test_carrier_c1_clip import ClipTests
        from unittest.mock import Mock
        directory, clip_cfg, scenes = ClipTests().fixture()
        document = clip.build_clips(clip_cfg)
        with gzip.open(directory/'rows.gz', 'wt') as handle:
            for row in document['clips']:
                handle.write(json.dumps(row)+'\n')
        write(directory/'inventory.json', dict(files=[file_pin(directory/'rows.gz')]))
        write(directory/'bank.json', {'fixture': True})
        cfg = configuration(); cfg['geometry_online']['input'] = gx.NATIVE_INPUT
        cfg.update(output=str(directory), readout=dict(bank=file_pin(directory/'bank.json'),
                   rows_inventory=file_pin(directory/'inventory.json'), training_scenes=clip_cfg['training_scenes'],
                   contiguous_clips=file_pin(directory/'clips.json')))
        bank = dict(dataset_tokens=np.array(['d']*38), scene_tokens=np.array([str(i) for i in range(38)]),
            frame_set_sha256=np.array([frame_set_sha256(list(range(0, 94, 3)))]*38), camera=np.zeros((38, 32, 9)),
            camera_mask=np.ones((38, 32), bool), gravity=np.zeros((38, 3)), gravity_mask=np.ones(38, bool),
            trajectory_scale=np.ones(38), point_depth_uv=np.zeros((38, 32, 1, 2)), point_depth_gt=np.zeros((38, 32, 1)),
            point_depth_mask=np.zeros((38, 32, 1), bool), depth_anchor_frames=np.arange(32))
        batch = {'aux_g3t_images': torch.zeros(1), 'aux_g3t_coords': torch.zeros(1)}
        def encode(*args, **kwargs):
            self.assertEqual(kwargs['geometry_online'], cfg['geometry_online'])
            self.assertEqual(args[1]['target'], data.READOUT_TARGET)
            self.assertEqual(args[3], 'vqa')
            return batch, None, {}
        model = Mock(); model.auxiliary_heads = object()
        model.readout.return_value = dict(raw_pose=np.zeros((32, 9)).tolist(), gravity_up=None, trajectory_step_m=None,
                                         point_depth=None, invalid_fov_frames=[], geometry_error=None)
        with patch.object(run, 'inference', return_value=(model, None, {}, {'step': 70})), \
             patch('student_pilot.all_frame_bank.read_bank', return_value=bank), \
             patch('student_pilot.all_frame_readout.evaluate', return_value={}), \
             patch.object(data, 'encode', side_effect=encode) as encoder, \
             patch.object(clip, 'pose_vectors_to_c2w', return_value=np.zeros((32, 4, 4))), \
             patch.object(clip, 'trajectory_metrics', return_value={}), patch.object(clip, 'summarize', return_value={}):
            with self.assertRaisesRegex(ValueError,'no authenticated R2 bank adapter'):
                run.evaluate(cfg, {}, directory/'native_readout.json')
            encoder.assert_not_called()
            model.readout.assert_not_called()
            model.pose_readout.assert_not_called()
        receipt = dict(streams={'pose': {'count': 1}}, geometry_online=cfg['geometry_online'])
        rows = SimpleNamespace(get=lambda *a: (batch, {}, {}), close=lambda: None)
        model.probe.return_value = {'finite': True}
        with patch.object(run, 'inference', return_value=(model, None, receipt, {'step': 70})), \
             patch.object(run, 'Rows', return_value=rows) as reader:
            with self.assertRaisesRegex(ValueError,'no authenticated R2 bank adapter'):
                run.probe(cfg, {}, directory/'native_probe.json')
            reader.assert_not_called()
            model.probe.assert_not_called()


if __name__ == '__main__':
    unittest.main()
