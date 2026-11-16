import copy
import itertools
import json
import importlib.util
import os
import shlex
import subprocess
import sys
import types
from pathlib import Path
import time
import unittest
import uuid
from unittest.mock import Mock, patch

import torch

import student_pilot
from student_pilot.decoupled_v import (VisionOnly, features, target_tensors, export_heads,
                                      load_heads, learning_rate, readout, head_settings,
                                      base_manifest, load_vision, RECIPE)
from student_pilot.p3_provenance import file_pin, load, write

CONSUMER = Path(os.environ.get('P3_CONSUMER', '/scratch/jjyeung/orch_cd/p3_build/work/p3'))
ROOT = Path(os.environ['B9_TEST_OUTPUT'])


class DecoupledTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        package = types.ModuleType('p3_consumer')
        package.__path__ = [str(CONSUMER/'student_pilot')]
        sys.modules['p3_consumer'] = package
        from p3_consumer.p3_smoke import tiny
        from p3_consumer.p3_heads import PrefixCapture
        cls.tiny = staticmethod(tiny)
        cls.capture = PrefixCapture

    def pair(self):
        model, tk, batch = self.tiny(grid=4)
        for p in model.model.visual.parameters():p.data=p.data.to(torch.bfloat16)
        # A native full forward requires a common BF16 base dtype, with FP32 heads.
        model.model.language_model.to(torch.bfloat16); model.lm_head.to(torch.bfloat16)
        fingerprints = model.frozen_fingerprints()
        model.config.p3.update(feature_encoder_sha256=fingerprints['vision'],
                               frozen_fingerprints=fingerprints, depth_convention='optical_axis_metric')
        stage = VisionOnly(copy.deepcopy(model.config), copy.deepcopy(model.model.visual))
        stage.auxiliary_heads.load_state_dict(model.auxiliary_heads.state_dict())
        return model.eval(), stage.eval(), batch

    def test_native_prefix_exact_states_grids_and_readout(self):
        model, stage, batch = self.pair()
        with torch.no_grad(), self.capture(model, batch) as expected:
            model(**batch, use_cache=False)
            expected.finish()
        got = features(stage, batch)
        torch.testing.assert_close(got.states, expected.states, rtol=0, atol=0)
        self.assertEqual(got.states.dtype, torch.bfloat16)
        for a, b in zip(got.grids, expected.grids):
            torch.testing.assert_close(a, b, rtol=0, atol=0)
        for a, b in zip(got.vits[0], expected.vits[0]):
            torch.testing.assert_close(a, b, rtol=0, atol=0)
        points = [[[100., 200.], [900., 700.]]]*16
        actual = readout(stage, batch, points)
        geometry = expected.geometry()
        self.assertEqual(actual['point_depth'], [geometry.depth_fn(k, p).tolist() for k, p in zip(range(2,33,2), points)])

    def test_only_heads_update_and_short_groups_mask(self):
        _, stage, batch = self.pair()
        stage.train()
        snapshot = {n: p.clone() for n, p in stage.model.named_parameters()}
        camera = [[0., 0., 0., 0., 0., 0., 1., 1., 1.]]*16
        record = dict(camera=camera, camera_mask=[True]*4+[False]*12, trajectory_scale=1.,
                      gravity=[0., -1., 0.], gravity_mask=True,
                      point_depth=dict(uv=[[[500.,500.],[200.,300.]]]*16, depth=[[2.,3.]]*16,
                                       mask=[[True,True]]*4+[[False,False]]*12))
        short = {**batch, 'video_grid_thw': torch.tensor([[4,4,4]]),
                 'pixel_values_videos': batch['pixel_values_videos'][:64]}
        optimizer = torch.optim.AdamW(stage.auxiliary_heads.parameters(), lr=.001)
        loss = stage(short, target_tensors(record)).mean()
        self.assertTrue(torch.isfinite(loss)); loss.backward()
        for n,p in stage.auxiliary_heads.named_parameters():
            self.assertIsNotNone(p.grad, n)
            self.assertTrue(torch.isfinite(p.grad).all(), n)
        self.assertTrue(any(p.grad.abs().sum()>0 for p in stage.auxiliary_heads.camera.point_depth.parameters()))
        optimizer.step()
        for n,p in stage.model.named_parameters():
            self.assertIsNone(p.grad); self.assertTrue(torch.equal(p, snapshot[n]), n)
        with self.assertRaises(ValueError):
            features(stage, short)

    def test_export_loads_unchanged_in_native_p3(self):
        model, stage, batch = self.pair()
        out = ROOT/uuid.uuid4().hex
        pin = export_heads(stage, out, 200, {'synthetic':True})
        model.load_heads(pin)
        load_heads(stage, pin)
        for key,value in stage.auxiliary_heads.state_dict().items():
            self.assertTrue(torch.equal(value, model.auxiliary_heads.state_dict()[key]), key)
        bad = load(pin['path']); bad['start']='f17'
        write(out/'bad.json', bad)
        with self.assertRaises(ValueError): model.load_heads(file_pin(out/'bad.json'))

    def test_schedule_and_unsupported_all_frame_queries(self):
        self.assertEqual(learning_rate(48), 1e-4)
        self.assertEqual(learning_rate(1600), 0.)
        _, stage, batch = self.pair()
        stage.config.p3['anchors'] = list(range(1,33))
        with self.assertRaises(ValueError): features(stage,batch)

    def test_measured_native_vision_only_load_and_consumer_schema(self):
        from safetensors.torch import save_file
        from p3_consumer.p3_heads import P3Heads as ConsumerHeads
        model, stage, batch = self.pair()
        out = ROOT/uuid.uuid4().hex
        out.mkdir()
        model.config.to_json_file(out/'config.json')
        save_file({'model.visual.'+k: v for k,v in model.model.visual.state_dict().items()}, str(out/'model.safetensors'))
        spec = {'snapshot':out, 'config_sha256':file_pin(out/'config.json')['sha256']}
        with patch('student_pilot.students.get_student',return_value=spec):
            manifest = base_manifest(out, 'synthetic')
        settings = head_settings({**model.config.p3['camera'], 'freeze_modules':['point_depth'], 'max_groups':16},
                                 'synthetic',manifest['feature_encoder_sha256'])
        config = copy.deepcopy(model.config); config.p3=settings
        ConsumerHeads(config)  # Rejects trainer-only keys if they leak into the artifact.
        loaded = load_vision(manifest, settings)
        self.assertFalse(any('language' in n for n,_ in loaded.named_parameters()))
        self.assertEqual(loaded.model.visual.rotary_pos_emb.inv_freq.dtype,torch.float32)
        torch.testing.assert_close(features(loaded,batch).states, features(stage,batch).states,rtol=0,atol=0)
        loaded.config.p3['start']='f17'
        with self.assertRaises(ValueError):load_vision(manifest,loaded.config.p3)

    def test_real_bank_cpu_preparation_and_frame_rejection(self):
        from student_pilot import decoupled_v_run as run
        from student_pilot.compact_label_bank import load_bank_for_rows
        from student_pilot.camera_config import CAMBRIAN_P_ROUTING
        source = ROOT.parents[2]
        out = ROOT/uuid.uuid4().hex; out.mkdir()
        with (source/'aws_run1/kit/in/7ab418d2.jsonl').open() as f:
            rows=[json.loads(x) for x in itertools.islice(f,16)]
        rowfile=out/'rows.jsonl';rowfile.write_text(''.join(json.dumps(r)+'\n' for r in rows))
        model,stage,batch=self.pair()
        write(out/'camera.json', {'camera':model.config.p3['camera']})
        cfg=dict(schema='decoupled-v-run-v1',mode='decoupled_v',init_heads=None,recipe=RECIPE,
                 base_identity='synthetic',base_root='/not-opened',preparation_output=str(out/'prep'),
                 rows=file_pin(rowfile),division=file_pin(source/'aws_run1/kit/in/b627c840.json'),
                 bank=file_pin(source/'h2/bank/51f013139e77.npz'),camera_source=file_pin(out/'camera.json'),
                 preparation=None,admission=None)
        manifest=dict(root='/not-opened',base_identity='synthetic',feature_encoder_sha256='a'*64)
        with patch.object(run,'base_manifest',return_value=manifest),patch('student_pilot.common.binding'), \
             patch.object(run,'processor_for',return_value=None),patch.object(run,'encode',return_value=batch):
            receipt=run.prepare(cfg)
        self.assertEqual(receipt['count'],16)
        self.assertGreater(receipt['audit']['depth_rows'],0)
        cfg['preparation']=file_pin(out/'prep/receipt.json')
        run.prepared(cfg)
        rows[0]['student_input']['frame_indices'][0]+=1
        with self.assertRaises(ValueError):
            load_bank_for_rows(cfg['bank']['path'], rows[:1],
                              {**receipt['settings']['camera'],'row_routing':CAMBRIAN_P_ROUTING})

    def test_exact_kit_bound_run_layout_and_reuse_refusal_before_cuda(self):
        from student_pilot import decoupled_v_run as run
        source = ROOT.parents[2]
        kit = source/'aws_v'
        cfg = load(kit/'kit/k/2.json')
        names = load(kit/'HEXES.json')
        out = ROOT/uuid.uuid4().hex; out.mkdir()
        script = (kit/'kit/b/c.sh').read_text()
        function = script[script.index('tk_bwrap() {'):script.index('tk_env() {')]
        dispatch = (kit/'kit/b/r.sh').read_text()
        run_bind = next(line for line in dispatch.splitlines() if ' tk_bwrap' in line)
        self.assertEqual(run_bind, 'RUNS="'+names['run']+'" tk_bwrap')
        harness = '\n'.join(['set -euo pipefail', 'X='+shlex.quote(str(out/'kit')),
            'S='+shlex.quote(str(out/'stage')), 'P='+shlex.quote(str(out/'mount')),
            'RR=runs/aws128p_20261025', 'EPOCHS='+shlex.quote(str(out/'epochs')),
            'tk_current() { printf "/bin/true %s\\n" "$(sha256sum /bin/true | cut -d\' \' -f1)"; }',
            function, run_bind, 'printf "%s\\n" "${BW[@]}"'])
        result = subprocess.run(['bash','-c',harness],capture_output=True,text=True,check=True)
        bound = out/'kit/runs'/names['run']
        self.assertTrue(bound.is_dir())
        self.assertIn(str(bound),result.stdout.splitlines())
        cfg['output'] = str(out/'kit'/Path(cfg['output']).relative_to(load(kit/'DESTINATIONS.json')['root']))
        output = Path(cfg['output'])/'train'
        self.assertEqual(output.parent,bound)
        self.assertFalse(output.exists())
        env = dict(RANK='0',WORLD_SIZE='8',LOCAL_RANK='0',SLURM_JOB_ID='cpu-fixture')
        # Stop at the first device call: directory ownership is exercised without CUDA/DDP.
        with patch.dict(os.environ,env), patch.object(run,'prepared',return_value=({},{})), \
             patch.object(torch.cuda,'set_device',side_effect=RuntimeError('CPU fixture stops before CUDA')) as device, \
             patch('torch.distributed.init_process_group') as init:
            with self.assertRaisesRegex(RuntimeError,'CPU fixture stops before CUDA'):
                run.train(cfg)
            self.assertEqual(load(output/'run.json'),cfg)
            marker = output/'retained'; marker.write_text('existing run')
            device.reset_mock()
            with self.assertRaises(FileExistsError):
                run.train(cfg)
            device.assert_not_called(); init.assert_not_called()
            self.assertEqual(marker.read_text(),'existing run')

    def test_real_heldout_bank_gate_reports_and_masked_depth(self):
        self.check_heldout_bank_gate_reports(synthetic_masks=False)

    def test_heldout_bank_with_synthetic_masks_ignores_unlabelled_depth(self):
        self.check_heldout_bank_gate_reports(synthetic_masks=True)

    def check_heldout_bank_gate_reports(self, synthetic_masks):
        import numpy as np
        from student_pilot import decoupled_v_run as run
        from student_pilot.compact_label_bank import read_bank
        from student_pilot.gate_eval import evaluate as scorer
        source = ROOT.parents[2]
        inputs = source/'aws_run1/kit/in'
        out = ROOT/uuid.uuid4().hex; out.mkdir()
        cfg = load(source/'aws_v/kit/k/2.json')
        held = cfg['readout']
        # Preserve the deployed authority's digest while resolving its exact local mirror.
        held['bank']['path'] = str(inputs/'689136d4.npz')
        self.assertEqual(file_pin(held['bank']['path']),held['bank'])
        bank = read_bank(held['bank']['path'])
        if synthetic_masks:
            # The pinned real bank currently labels every point. A separate, clearly
            # synthetic mask fixture also tests future partially labelled banks.
            bank['point_depth_mask'] = bank['point_depth_mask'].copy()
            bank['point_depth_mask'][0] = False
            bank['point_depth_mask'][1,0] = False
            bank['point_depth_mask'][1,1,::2] = False
            np.savez(out/'synthetic_masks.npz',**bank)
            held['bank'] = file_pin(out/'synthetic_masks.npz')
        held['training_scenes']['path'] = str(inputs/'2e94d318.json')
        self.assertEqual(file_pin(held['training_scenes']['path']),held['training_scenes'])
        inventory = load(inputs/'30c516bf.json')
        for pin in inventory['files']:
            pin['path'] = str(inputs/'ce7286a1'/Path(pin['path']).name)
            self.assertEqual(file_pin(pin['path']),pin)
        write(out/'inventory.json',inventory)
        held['rows_inventory'] = file_pin(out/'inventory.json')
        cfg['readout_output'] = str(out/'readout')
        lookup = {tuple(key): i for i,key in enumerate(zip(bank['dataset_tokens'],bank['scene_tokens']))}
        self.assertEqual(len(lookup),38)
        if synthetic_masks:
            self.assertTrue((~bank['point_depth_mask']).any())
            self.assertTrue((~bank['point_depth_mask'].any(axis=-1)).any())
        artifact_pins = []
        for step in (200,400,800):
            write(out/f'heads_{step}.json',{'step':step,'weights':{'synthetic':True}})
            artifact_pins.append(file_pin(out/f'heads_{step}.json'))
        model = Mock()
        model.to.return_value = model
        model.auxiliary_heads.camera.has_gravity = True
        model.auxiliary_heads.camera.has_scale = True
        model.auxiliary_heads.camera.point_depth = object()
        active = {}
        def load_artifact(model,pin):
            artifact = load(pin['path'])
            active.update(artifact)
            return artifact
        def encode_row(processor,row):
            active['scene'] = row['dataset'],row['scene']
            return {'fixture':Mock()}
        def predict(model,batch,uv):
            i = lookup[active['scene']]
            depth = bank['point_depth_gt'][i].astype('float64')
            depth[~bank['point_depth_mask'][i]] = -1000. if active['step']==200 else 9999.
            if active['step']==800:
                depth[bank['point_depth_mask'][i]] *= 2
            return dict(raw_pose=bank['camera'][i].astype('float64').tolist(),
                        gravity_up=bank['gravity'][i].astype('float64').tolist(),
                        trajectory_step_m=float(bank['trajectory_scale'][i]),point_depth=depth.tolist())
        with patch.object(run,'prepared',return_value=({'settings':{}},{'root':'/unused'})), \
             patch.object(run,'processor_for'),patch.object(run,'load_vision',return_value=model), \
             patch.object(run,'load_heads',side_effect=load_artifact),patch.object(run,'encode',side_effect=encode_row), \
             patch.object(run,'readout',side_effect=predict), \
             patch('student_pilot.gate_eval.evaluate',wraps=scorer) as score:
            run.evaluate(cfg,artifact_pins)
        self.assertEqual(score.call_count,3)
        outputs = [load(out/f'readout/{step}.json') for step in (200,400,800)]
        reports = [load(run.pinned(value['report'])) for value in outputs]
        for value,report in zip(outputs,reports):
            summary = value['gate_report_summary']
            self.assertEqual(summary,report['report']['heads'])
            self.assertEqual(summary['checks'],report['detail']['gate']['checks'])
            self.assertEqual(summary['summary'],report['detail']['overall'])
            self.assertEqual(summary['summary']['num_scenes'],38)
            self.assertEqual(summary['summary']['depth_points'],int(bank['point_depth_mask'].sum()))
            self.assertEqual(len(value['scene_first_session']),38)
            self.assertEqual(report['depth_semantics']['bank'],held['bank'])
            self.assertEqual(report['detail']['heads'],['depth','gravity','pose','scale'])
        self.assertTrue(outputs[0]['gate_report_summary']['passed'])
        self.assertEqual(outputs[0]['gate_report_summary'],outputs[1]['gate_report_summary'])
        self.assertFalse(outputs[2]['gate_report_summary']['passed'])
        self.assertAlmostEqual(outputs[2]['gate_report_summary']['summary']['depth_abs_rel'],1.)
        self.assertFalse(outputs[2]['gate_report_summary']['checks']['depth_abs_rel'])
        # The retained masked predictions differ, while every scored quantity is identical.
        if synthetic_masks:
            key = next('/'.join(key) for key,i in lookup.items() if (~bank['point_depth_mask'][i]).any())
            i = lookup[tuple(key.split('/'))]
            for value,fill in zip(outputs[:2],(-1000.,9999.)):
                session = value['scene_first_session'][key]
                self.assertTrue((np.asarray(session['point_depth'])[~bank['point_depth_mask'][i]]==fill).all())


if __name__ == '__main__':
    unittest.main()
