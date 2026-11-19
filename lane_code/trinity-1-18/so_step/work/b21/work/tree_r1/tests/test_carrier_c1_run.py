"""CPU dryrun, actual FSDP/Gloo updates, rank shards and artifact reload."""
import copy
from contextlib import ExitStack, nullcontext
import json
import os
from pathlib import Path
import tempfile
import time
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import torch
import torch.distributed as dist

from student_pilot import carrier_c1_run as run, full_ft
from student_pilot.carrier_c1 import RECIPE, parameter_groups
from student_pilot.carrier_c1_data import mixed_indices, C1_A
from student_pilot.p3_provenance import file_pin, load, write
from tests.test_carrier_c1 import fixture
from tests.test_fsdp import SOCKETS
from tests.retained_workers import run_workers


class FixtureRows:
    def __init__(self, receipt=None, processor=None):
        _,self.batch,self.targets=fixture(4)

    def get(self,stream,index):
        return self.batch,self.targets if stream=='pose' else None,{}

    def close(self):
        pass


def worker(rank, root, port):
    torch.set_num_threads(1)
    dist.init_process_group('gloo',init_method=f'tcp://127.0.0.1:{port}',rank=rank,world_size=2)
    try:
        model,_,_=fixture(4)
        wrapped=run.wrap_model(model,torch.device('cpu'),mixed_precision=False)
        optimizer=torch.optim.AdamW(parameter_groups(wrapped),weight_decay=.01)
        rows=FixtureRows();plans=list(mixed_indices(dict(pose=9,vqa=9,pointing=9),2))
        info,_=run.optimize_step(wrapped,optimizer,rows,plans[0],rank,torch.device('cpu'),1,True)
        pin=run.checkpoint(Path(root)/'checkpoint',wrapped,optimizer,{'fixture':True},1)
        run.optimize_step(wrapped,optimizer,rows,plans[1],rank,torch.device('cpu'),2,True)
        expected={n:p.detach().clone() for n,p in full_ft.named_trainable(wrapped)}
        step=run.restore(pin,wrapped,optimizer,{'fixture':True})
        assert step==1
        run.optimize_step(wrapped,optimizer,rows,plans[1],rank,torch.device('cpu'),2,True)
        for name,p in full_ft.named_trainable(wrapped):
            torch.testing.assert_close(p,expected[name],rtol=0,atol=0)
        cfg=dict(base_identity='fixture', trace_program_version='3.13')
        run.export(Path(root)/'m2',wrapped,model,cfg,2)
        # Readout runs after the FSDP allocation, on an ordinary native model.
        if rank==0:
            fresh,batch,target=fixture(4)
            artifact=run.load_artifact(fresh,file_pin(Path(root)/'m2/artifact.json'))
            assert artifact['anchors']==list(range(1,33))
            probe=fresh.eval().probe(batch,target)
            assert probe['finite'] and probe['valid_frames']==8
            (Path(root)/'result.json').write_text(json.dumps(dict(status='PASS',step=info,probe=probe,
                                                               resume_exact=True)))
    finally:
        dist.destroy_process_group()


class RunnerTests(unittest.TestCase):
    def setUp(self):
        from tests.so_helpers import reset_switches
        reset_switches(self)

    def root(self):
        return Path(tempfile.mkdtemp(prefix='c1_',dir=os.environ['LANE_TEST_OUTPUT']))

    def local_collectives(self):
        context = ExitStack()
        for name, value in [('get_rank', 0), ('get_world_size', 1), ('get_backend', 'gloo')]:
            context.enter_context(patch.object(dist, name, return_value=value))
        for name in ('barrier', 'broadcast', 'broadcast_object_list'):
            context.enter_context(patch.object(dist, name))
        context.enter_context(patch.object(dist, 'all_gather_object', side_effect=lambda out, value, **kw: out.__setitem__(0, value)))
        return context

    def test_train_enables_native_decoder_checkpointing_after_eval_load(self):
        root = self.root()
        model, batch, target = fixture(4)
        model.eval()  # from_pretrained returns the native base in eval mode.
        receipt = {'streams': {k: {'count': 9} for k in ('pose', 'vqa', 'pointing')}}
        cfg = dict(output=str(root), preparation={'fixture': True}, trace_program_version='3.13')
        write(root/'authorization.json', dict(config_sha256=run.identity(cfg), new_gpus=8, job_id='test', verdict='GO'))
        cfg['authorization'] = file_pin(root/'authorization.json')
        def loop(*args, **kwargs):
            self.assertTrue(model.training)
            self.assertFalse(model.model.visual.training)
            layers = model.model.language_model.layers
            with ExitStack() as stack:
                spies = [stack.enter_context(patch.object(layer, '_gradient_checkpointing_func',
                           wraps=layer._gradient_checkpointing_func)) for layer in layers]
                self.assertTrue(all(layer.training and layer.gradient_checkpointing for layer in layers))
                model(batch, target)['loss'].backward()
                self.assertTrue(all(spy.call_count > 0 for spy in spies))
            self.assertTrue(any(p.grad is not None for p in model.model.language_model.parameters()))
        with ExitStack() as stack:
            stack.enter_context(patch.dict(os.environ, WORLD_SIZE='8', RANK='0', LOCAL_RANK='0', SLURM_JOB_ID='test'))
            for name in ('set_device', 'reset_peak_memory_stats'):
                stack.enter_context(patch.object(torch.cuda, name))
            stack.enter_context(patch.object(torch.cuda, 'is_available', return_value=True))
            stack.enter_context(self.local_collectives())
            # CP1 added a separate startup group; this CPU test mocks all transport.
            # e6456bc itself fails here if new_group reaches the native runtime.
            for name in ('init_process_group', 'destroy_process_group', 'new_group'):
                stack.enter_context(patch.object(dist, name))
            for name, value in [('validate', None), ('prepared', (receipt, {'root': '/fixture'})),
                                ('authenticate', 'fixture'), ('processor_for', SimpleNamespace(tokenizer=SimpleNamespace())),
                                ('load_model', model), ('wrap_model', model), ('run_lock', nullcontext())]:
                stack.enter_context(patch.object(run, name, return_value=value))
            stack.enter_context(patch.object(run, 'Rows', FixtureRows))
            native_loop = stack.enter_context(patch.object(run, 'run_steps', side_effect=loop))
            run.train(cfg, smoke_steps=1)
            native_loop.assert_called_once()

    def test_fresh_binding_reuses_identical_early_crash_and_refuses_mismatch_or_complete_state(self):
        root = self.root(); bound = {'fixture': 'early_crash'}
        run.bind_output(root, bound)
        binding = root/'binding.json'
        before = binding.read_bytes(), binding.stat().st_mtime_ns
        run.bind_output(root, bound)
        write(root/'checkpoint_000001/complete.json', {'incomplete': True})
        run.bind_output(root, bound)
        self.assertEqual((binding.read_bytes(), binding.stat().st_mtime_ns), before)
        for resume in (False, True):
            with self.assertRaisesRegex(ValueError, 'another run'):
                run.bind_output(root, {'fixture': 'different'}, resume=resume)
        model, _, _ = fixture(4)
        optimizer = torch.optim.AdamW(parameter_groups(model))
        with self.local_collectives():
            run.checkpoint(root/'checkpoint_000002', model, optimizer, bound, 2)
        with self.assertRaisesRegex(ValueError, 'resume instead'):
            run.bind_output(root, bound)
        run.bind_output(root, bound, resume=True)
        self.assertEqual((binding.read_bytes(), binding.stat().st_mtime_ns), before)

    def test_resume_rotation_ignores_interrupted_save_and_preserves_exports(self):
        root = self.root(); bound = {'fixture': 'rotation'}
        write(root/'binding.json', bound)
        write(root/'m100/artifact.json', {'weights_only': True})
        model, batch, target = fixture(4)
        optimizer = torch.optim.AdamW(parameter_groups(model))
        model(batch, target)['loss'].backward(); optimizer.step()
        durations = []
        def save(step):
            tick = time.perf_counter()
            pin = run.checkpoint(root/f'checkpoint_{step:06d}', model, optimizer, bound, step, rotate=True)
            durations.append(time.perf_counter()-tick)
            return pin
        with self.local_collectives():
            first, second = save(1), save(2)
            self.assertEqual(run.latest_resume(root, bound), second)
            # A real shard is written, then RNG serialization is interrupted.
            original = full_ft._write_payload
            def interrupted(path, payload):
                if path.name.startswith('rng'):
                    raise OSError('interrupted fixture save')
                return original(path, payload)
            with patch.object(full_ft, '_write_payload', side_effect=interrupted):
                with self.assertRaisesRegex(OSError, 'interrupted'):
                    save(3)
            self.assertTrue(Path(first['path']).is_file())
            self.assertTrue(Path(second['path']).is_file())
            self.assertEqual(run.latest_resume(root, bound), second)
            partial = next(p for p in root.glob('checkpoint_000003_*'))
            self.assertFalse((partial/'complete.json').exists())
            # A truncated completion marker must also be ignored.
            (partial/'complete.json').write_text('{"schema":')
            self.assertEqual(run.latest_resume(root, bound), second)
            real_write = run.write
            def observed_write(path, value):
                if path.name == 'complete.json':
                    self.assertTrue(Path(first['path']).is_file())
                    self.assertTrue(Path(second['path']).is_file())
                    self.assertEqual(dist.barrier.call_count, 2)
                return real_write(path, value)
            dist.barrier.reset_mock()
            with patch.object(run, 'write', side_effect=observed_write):
                third = save(3)
            self.assertFalse(Path(first['path']).exists())
            self.assertTrue(Path(second['path']).is_file())
            self.assertEqual(run.latest_resume(root, bound), third)
            self.assertEqual(run.restore(third, model, optimizer, bound), 3)
            self.assertEqual(len(run.complete_states(root, bound)), 2)
            self.assertTrue(partial.is_dir())
            self.assertEqual(load(root/'m100/artifact.json'), {'weights_only': True})
        state = load(third['path'])
        measurement = dict(save_seconds=durations, payload_bytes=sum(p['bytes'] for p in state['files'].values()),
                           fixture='tiny native C1 with initialized AdamW; one CPU rank; mocked collectives')
        write(root/'save_timing.json', measurement)
        print('C1_SAVE_TIMING ' + json.dumps({**measurement, 'receipt': str(root/'save_timing.json')}), flush=True)

    def test_timed_saves_canary_and_unchanged_gate_and_lr_horizon(self):
        root = self.root()
        cfg = {'recipe': {**RECIPE, 'resume_every_seconds': 10}}
        clock = [0.]
        def update(*args):
            clock[0] += 4.
            return {'wall_seconds': 4.}, None
        with patch.object(run, 'optimize_step', side_effect=update), \
             patch.object(run.time, 'monotonic', side_effect=lambda: clock[0]), \
             patch.object(run, 'checkpoint') as save, patch.object(run, 'export') as publish:
            report = run.run_steps(None, None, None, None, dict(pose=9,vqa=9,pointing=9),
                                   root, cfg, {}, torch.device('cpu'), start_step=98, distributed=False)
        self.assertEqual(report['last_step'], 400)
        self.assertEqual(report['stop_reason'], 'm400_gate')
        saved_steps = [call.args[-1] for call in save.call_args_list]
        self.assertEqual(saved_steps[:3], [101, 104, 107])
        self.assertNotIn(100, saved_steps)
        self.assertEqual(saved_steps[-1], 400)
        self.assertEqual([call.args[-1] for call in publish.call_args_list], [100, 200, 400])
        self.assertEqual([call.args[0].name for call in publish.call_args_list], ['m100', 'm200', 'm400'])
        self.assertEqual(run.recipe_for(cfg)['steps'], 800)
        from student_pilot.decoupled_v import learning_rate
        for step in (1, 100, 400, 800):
            self.assertEqual(learning_rate(step, run.recipe_for(cfg)), learning_rate(step, RECIPE))
        with patch.object(run, 'optimize_step', side_effect=lambda *args: ({'wall_seconds': 0.}, None)), \
             patch.object(run, 'checkpoint') as save, patch.object(run, 'export') as publish:
            report = run.run_steps(None, None, None, None, dict(pose=9,vqa=9,pointing=9),
                                   self.root(), {}, {}, torch.device('cpu'), start_step=799, distributed=False)
        self.assertEqual(report['last_step'], 800)
        self.assertEqual(publish.call_args.args[-1], 800)
        self.assertEqual(save.call_args.args[-1], 800)

    def test_resume_replays_complete_canary_without_overwriting_weights(self):
        root = self.root(); cfg = dict(base_identity='fixture', trace_program_version='3.13')
        model, _, _ = fixture(4)
        with self.local_collectives(), \
             patch('student_pilot.fsdp_training.publication_state', return_value=model.state_dict()):
            run.export(root/'m100', model, model, cfg, 100)
        original = file_pin(root/'m100/artifact.json')
        self.assertTrue(run.existing_export(root/'m100', cfg, 100))
        with patch.object(run, 'optimize_step', side_effect=lambda *args: ({'wall_seconds': 0.}, None)), \
             patch.object(run, 'checkpoint'), patch.object(run, 'export') as publish:
            report = run.run_steps(None, None, None, None, dict(pose=9,vqa=9,pointing=9),
                                   root, cfg, {}, torch.device('cpu'), start_step=99, distributed=False)
        self.assertTrue(report['steps'][0][0]['export_reused'])
        self.assertEqual([call.args[-1] for call in publish.call_args_list], [200, 400])
        self.assertEqual(original, file_pin(root/'m100/artifact.json'))
        with self.assertRaisesRegex(ValueError, 'another C1 run'):
            run.existing_export(root/'m100', {**cfg, 'base_identity': 'changed'}, 100)
        (root/'m800').mkdir()
        with self.assertRaises(FileNotFoundError):
            run.existing_export(root/'m800', cfg, 800)

    def test_signal_and_exhausted_startup_save_once_without_export(self):
        for signal_stop in (True, False):
            with self.subTest(signal_stop=signal_stop), \
                 patch.object(run, 'checkpoint') as save, patch.object(run, 'export') as publish:
                cfg = {} if signal_stop else dict(training_mode='pose_only', depth_enabled=False,
                    schedule=dict(startup_seconds=1, p95_step_seconds=1, checkpoint_seconds=1, export_seconds=1))
                counts = dict(pose=1, vqa=1, pointing=1) if signal_stop else {'pose': 1}
                report = run.run_steps(None, None, None, None, counts, self.root(), cfg, {},
                    torch.device('cpu'), start_step=50, stop=[signal_stop],
                    started=time.monotonic()-20000 if not signal_stop else None, distributed=False)
                self.assertEqual(report['last_step'], 50)
                save.assert_called_once()
                self.assertEqual(save.call_args.args[-1], 50)
                self.assertTrue(save.call_args.kwargs['rotate'])
                publish.assert_not_called()

    def test_fsdp_does_not_downcast_geometry_targets(self):
        from types import SimpleNamespace
        from torch.distributed.fsdp import MixedPrecision
        model,_,_=fixture(4)
        wrapped=SimpleNamespace(mixed_precision=MixedPrecision(param_dtype=torch.bfloat16,reduce_dtype=torch.float32))
        with patch.object(full_ft,'wrap_full_model',return_value=wrapped):
            actual=run.wrap_model(model,torch.device('cpu'))
        self.assertFalse(actual.mixed_precision.cast_root_forward_inputs)
        self.assertEqual(actual.mixed_precision.param_dtype,torch.bfloat16)
        self.assertEqual(actual.mixed_precision.reduce_dtype,torch.float32)

    def test_native_cpu_dryrun_reports_steps_memory_and_probes(self):
        root=self.root();model,_,_=fixture(4)
        receipt={'streams':{k:{'count':9} for k in ('pose','vqa','pointing')}}
        with patch.object(run,'prepared',return_value=(receipt,{'root':'/fixture'})), \
             patch.object(run,'processor_for'),patch.object(run,'load_model',return_value=model), \
             patch.object(run,'Rows',FixtureRows):
            report=run.dryrun({},root/'dryrun.json')
        self.assertEqual(report['status'],'PASS')
        self.assertTrue(all(report['checks'].values()))
        self.assertEqual(len(report['rank_shapes']),32)
        self.assertGreater(report['step']['wall_seconds'],0)
        self.assertGreater(report['peak_rss_bytes'],0)
        self.assertFalse(report['gpu_fit_measured'])

    @unittest.skipUnless(SOCKETS, 'Local sockets are unavailable; parent CPU job must run Gloo')
    def test_actual_fsdp_gloo_resume_and_export(self):
        root=self.root()
        run_workers(worker, (str(root),), start_method='fork')
        result=load(root/'result.json')
        self.assertEqual(result['status'],'PASS')
        self.assertTrue(result['resume_exact'])

    def test_native_single_rank_shard_resume_without_collective_transport(self):
        root=self.root();model,_,_=fixture(4)
        optimizer=torch.optim.AdamW(parameter_groups(model),weight_decay=.01)
        rows=FixtureRows();plans=list(mixed_indices(dict(pose=9,vqa=9,pointing=9),2))
        run.optimize_step(model,optimizer,rows,plans[0],0,torch.device('cpu'),1)
        def gather(out,value,*args,**kwargs):
            out[0]=value
        with patch.object(dist,'get_rank',return_value=0),patch.object(dist,'get_world_size',return_value=1), \
             patch.object(dist,'barrier'),patch.object(dist,'all_gather_object',side_effect=gather), \
             patch.object(dist,'broadcast'),patch.object(dist,'broadcast_object_list'), \
             patch.object(dist,'get_backend',return_value='gloo'):
            pin=run.checkpoint(root/'checkpoint',model,optimizer,{'fixture':'no_transport'},1)
            run.optimize_step(model,optimizer,rows,plans[1],0,torch.device('cpu'),2)
            expected={n:p.detach().clone() for n,p in full_ft.named_trainable(model)}
            self.assertEqual(run.restore(pin,model,optimizer,{'fixture':'no_transport'}),1)
            run.optimize_step(model,optimizer,rows,plans[1],0,torch.device('cpu'),2)
            for name,p in full_ft.named_trainable(model):
                torch.testing.assert_close(p,expected[name],rtol=0,atol=0)
            with self.assertRaisesRegex(ValueError,'binding'):
                run.restore(pin,model,optimizer,{'fixture':'changed'})
            with patch('student_pilot.fsdp_training.publication_state',return_value=model.state_dict()):
                run.export(root/'m2',model,model,{'base_identity':'fixture','trace_program_version':'3.13'},2)
        fresh,batch,target=fixture(4)
        run.load_artifact(fresh,file_pin(root/'m2/artifact.json'))
        self.assertTrue(fresh.eval().probe(batch,target)['finite'])

    def test_recipe_admission_and_resume_binding_fail_closed(self):
        cfg=dict(schema='carrier-c1-run-v1',trace_program_version='3.13',recipe=RECIPE,init='base',parallel='fsdp',all_frames=True,
                 streams=dict(pose={},vqa={},pointing={}),carrier_placement=C1_A)
        run.validate(cfg)
        custom = {**cfg, 'recipe': {**RECIPE, 'resume_every_seconds': 90}}
        run.validate(custom)
        self.assertEqual(run.recipe_for(custom)['resume_every_seconds'], 90)
        self.assertNotEqual(run.identity(cfg), run.identity(custom))
        for interval in (0, -1, True, float('inf'), float('nan')):
            with self.assertRaisesRegex(ValueError, 'resume_every_seconds'):
                run.validate({**cfg, 'recipe': {**RECIPE, 'resume_every_seconds': interval}})
        for bad in ({**cfg,'init':'warm_start'},{**cfg,'streams':{'pose':{}}},
                    {**cfg,'recipe':{**RECIPE,'world_size':1}}):
            with self.assertRaises(ValueError):
                run.validate(bad)
        with self.assertRaisesRegex(ValueError,'eight-GPU'):
            run.train(cfg)
        for key in ('admission','preparation','authorization'):
            self.assertEqual(run.identity(cfg),run.identity({**cfg,key:{'fixture':True}}))
        self.assertNotEqual(run.identity(cfg),run.identity({**cfg,'streams':{}}))

    def test_native_smoke_stops_without_checkpoint_or_export_and_reports_memory(self):
        root=self.root();model,_,_=fixture(4)
        optimizer=torch.optim.AdamW(parameter_groups(model))
        with patch.object(run,'checkpoint',side_effect=AssertionError('No smoke checkpoint')), \
             patch.object(run,'export',side_effect=AssertionError('No smoke export')):
            report=run.run_steps(model,model,optimizer,FixtureRows(),dict(pose=9,vqa=9,pointing=9),
                root,{}, {},torch.device('cpu'),smoke_steps=3,distributed=False)
        self.assertEqual(report['last_step'],3)
        self.assertEqual(len(report['steps']),3)
        self.assertFalse(report['gpu_fit_measured'])
        for step in report['steps']:
            self.assertGreater(step[0]['wall_seconds'],0)
            self.assertIn('peak_allocated_bytes',step[0])
            self.assertIn('peak_reserved_bytes',step[0])
        self.assertTrue((root/'smoke.json').is_file())

    def test_m400_stops_for_three_gates_and_bad_preservation_refuses(self):
        root=self.root();model,_,_=fixture(4)
        optimizer=torch.optim.AdamW(parameter_groups(model))
        with patch.object(run,'checkpoint') as save,patch.object(run,'export') as publish:
            report=run.run_steps(model,model,optimizer,FixtureRows(),dict(pose=9,vqa=9,pointing=9),
                root,{}, {},torch.device('cpu'),start_step=399,distributed=False)
        self.assertEqual(report['last_step'],400)
        self.assertEqual(report['stop_reason'],'m400_gate')
        self.assertEqual(save.call_count,1)
        self.assertEqual(publish.call_count,1)
        from student_pilot.p3_provenance import write
        write(root/'clips.json',{'fixture':True})
        cfg=dict(output=str(root),readout={'contiguous_clips':file_pin(root/'clips.json')})
        write(root/'m400/artifact.json',{'fixture':True})
        report_pin=file_pin(root/'m400/artifact.json')
        from student_pilot.carrier_c1_clip import PROTOCOL, METRICS
        pose_report=dict(schema='c1-readout-v2',artifact=report_pin,step=400,config_sha256=run.identity(cfg),
            contiguous_clips=cfg['readout']['contiguous_clips'],readout_sha256=run.readout_identity(cfg),
            detail=dict(protocol='head_acc_origin_metric_v1',all_frames={'all':dict(scenes=38,rot_deg={'median':38.})}),
            contiguous_clip=dict(protocol=PROTOCOL,scenes=38,clips=38,frames_per_clip=32,raw_stride=3,
                                 mean={k:.1 for k in METRICS}))
        write(root/'pose.json',pose_report)
        gate=dict(schema='c1-m400-gate-v1',verdict='PASS',reviewer='fixture',step=400,
            config_sha256=run.identity(cfg),artifact=report_pin,
            reports=dict(pose=file_pin(root/'pose.json'),pointing=report_pin,vsi500=report_pin),
            metrics=dict(pose_scenes=38,vsi500_n=500,pose_statistic='head_acc_median',rotation_deg=38.,
                         pointing_inside_fraction=.677,vsi500_base_accuracy=.5,vsi500_accuracy=.48))
        write(root/'gate.json',gate)
        run.milestone_gate({**cfg,'milestone_gate':file_pin(root/'gate.json')})
        for index,change in enumerate(({'rotation_deg':40.},{'pointing_inside_fraction':.676},
                                       {'vsi500_accuracy':.478},{'pose_scenes':37})):
            write(root/f'bad{index}.json',{**gate,'metrics':{**gate['metrics'],**change}})
            with self.assertRaises(ValueError):
                run.milestone_gate({**cfg,'milestone_gate':file_pin(root/f'bad{index}.json')})


if __name__=='__main__':
    unittest.main()
