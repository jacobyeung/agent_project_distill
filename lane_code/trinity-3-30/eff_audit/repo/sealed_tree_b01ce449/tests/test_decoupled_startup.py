"""Native CPU startup fixtures; CUDA/DDP are mocked only for smoke-loop coverage."""
import copy
from contextlib import ExitStack, nullcontext
import json
import os
from pathlib import Path
import random
import sqlite3
import unittest
import uuid
from unittest.mock import patch

import torch
from safetensors.torch import save_file
from PIL import Image
from tests import test_decoupled_v as fixtures
from student_pilot import decoupled_v_run as run
from student_pilot.decoupled_v import base_manifest, head_settings, RECIPE
from student_pilot.decoupled_vc import VC_RECIPE
from student_pilot.p3_provenance import write, load, file_pin

ROOT = Path(os.environ['LANE_TEST_OUTPUT'])


class TinyProcessor:
    """CPU env has no torchvision; retain actual RGB decode and tensor encoding."""
    def __init__(self, tokenizer):
        from types import SimpleNamespace
        self.tokenizer = tokenizer
        self.video_token_id = 4
        self.video_processor = SimpleNamespace(temporal_patch_size=2, merge_size=2)

    def apply_chat_template(self, messages, **kwargs):
        prompt = '<|vision_start|><|video_pad|><|vision_end|>question\n'
        if len(messages) == 1:
            return prompt
        return prompt+messages[-1]['content']+self.tokenizer.eos_token+'\n'

    def __call__(self, text, videos, video_metadata, **kwargs):
        pixels = torch.from_numpy(videos[0].copy()).float()/255
        pixels = pixels.reshape(16,2,4,16,4,16,3).permute(0,2,4,6,1,3,5).reshape(256,1536)
        meta = video_metadata[0]
        stamps = ''.join(f'<{(meta.frames_indices[i]+meta.frames_indices[i+1])/2/meta.fps:.1f} seconds>' for i in range(0,32,2))
        ids = torch.tensor([self.tokenizer.encode(stamps+text[0].replace('<|video_pad|>', '<|video_pad|>'*64),
                                                add_special_tokens=False)])
        return dict(input_ids=ids, attention_mask=torch.ones_like(ids), pixel_values_videos=pixels,
                    video_grid_thw=torch.tensor([[16,4,4]]))


class StartupTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        fixtures.DecoupledTests.setUpClass()

    def fixture(self, mode, fixed=False, all_frames=False):
        out = ROOT/uuid.uuid4().hex
        out.mkdir()
        model, tk, batch = fixtures.DecoupledTests.tiny(grid=4)
        model.model.visual.to(torch.bfloat16)
        self.processor = TinyProcessor(tk)
        model.config.to_json_file(out/'config.json')
        save_file({'model.visual.'+k:v for k,v in model.model.visual.state_dict().items()}, str(out/'model.safetensors'))
        with patch('student_pilot.students.get_student', return_value={
                'snapshot':out, 'config_sha256':file_pin(out/'config.json')['sha256']}):
            manifest = base_manifest(out, 'fixture')
        write(out/'model.json', manifest)
        Image.new('RGB', (64,64), color=(30,70,110)).save(out/'0.png')
        row = dict(qid='0', category='camera_pose_only', target='ok', student_input=dict(
            question='q', options=[], frames=[file_pin(out/'0.png')]*32, frame_indices=list(range(32)),
            timestamps=[i/30 for i in range(32)], fps=30, total_num_frames=32))
        target = dict(camera=[[0.,0.,0.,0.,0.,0.,1.,1.,1.]]*16, camera_mask=[True]*16,
            trajectory_scale=1., gravity=[0.,-1.,0.], gravity_mask=True,
            point_depth=dict(uv=[[[500.,500.],[200.,300.]]]*16, depth=[[2.,3.]]*16, mask=[[True,True]]*16))
        if all_frames:
            for key in ('camera', 'camera_mask'):
                target[key] = [v for v in target[key] for _ in range(2)]
            target['point_depth'] = {k:[v for v in values for _ in range(2)]
                                     for k,values in target['point_depth'].items()}
        conn=sqlite3.connect(out/'rows.sqlite')
        conn.execute('CREATE TABLE rows (i INTEGER PRIMARY KEY, row TEXT, target TEXT)')
        for i in range(9):
            conn.execute('INSERT INTO rows VALUES (?,?,?)',(i,json.dumps({**row,'qid':str(i)}),json.dumps(target)))
        conn.commit(); conn.close()
        cfg=dict(schema='decoupled-v-run-v1',mode=mode,recipe=RECIPE if mode=='decoupled_v' else VC_RECIPE,
                 init_heads=None,base_identity='fixture',base_root=str(out),output=str(out/'out'),
                 preparation=None,admission=None,gradient_checkpointing=True)
        settings=head_settings(model.config.p3['camera'],'fixture',manifest['feature_encoder_sha256'], all_frames=all_frames)
        if all_frames:
            cfg['all_frames'] = True
        settings['feature_backing']=mode
        if fixed:
            settings['camera'].update(run.FIXED_CAMERA)
        receipt=dict(schema='decoupled-v-preparation-v1',inputs={},model=file_pin(out/'model.json'),
                     database=file_pin(out/'rows.sqlite'),count=9,settings=settings)
        if mode=='decoupled_vc':
            write(out/'source.json',{})
            cfg['reuse_preparation']={'config':file_pin(out/'source.json'),'receipt':file_pin(out/'source.json')}
            receipt['reused_from']=cfg['reuse_preparation']
        receipt['config_sha256']=run.identity(cfg)
        write(out/'receipt.json',receipt);cfg['preparation']=file_pin(out/'receipt.json')
        write(out/'admission.json',dict(verdict='PASS',config_sha256=run.identity(cfg),
                                       preparation=cfg['preparation'],reviewer='fixture'))
        cfg['admission']=file_pin(out/'admission.json')
        return out,cfg,batch,target

    def check_probe(self, probe, groups=16):
        self.assertEqual(probe['valid_groups'],groups)
        self.assertEqual(probe['settings'],run.FIXED_CAMERA)
        self.assertEqual(probe['invalid_fov_frames'],0)
        self.assertGreater(probe['rotation_weight_grad_norm'],0)
        self.assertGreater(probe['fov_weight_grad_norm'],0)
        self.assertIn('rotation_error_median_deg',probe)
        self.assertIn('prediction_magnitude_median_deg',probe)
        self.assertIn('origin_permutation_pose_max_abs',probe)
        self.assertTrue(probe['nonpositive_fov_logits_per_stage'])
        self.assertTrue(probe['component_losses_last_row'])

    def tiny_stop(self, processor):
        return processor.tokenizer.eos_token, processor.tokenizer.eos_token_id

    def test_native_cpu_dryrun_both_modes(self):
        for mode in ('decoupled_v','decoupled_vc'):
            with self.subTest(mode=mode):
                out,cfg,_,_=self.fixture(mode, fixed=True)
                with patch('transformers.AutoProcessor.from_pretrained',return_value=self.processor), \
                     patch('student_pilot.batches.training_stop_token',side_effect=self.tiny_stop):
                    report=run.dryrun(cfg,out/'dry.json')
                self.assertEqual(report['status'],'PASS')
                self.assertTrue(all(report['checks'].values()))
                self.assertEqual(len(report['ranks']),8)
                self.assertFalse((Path(cfg['output'])/'train').exists())
                self.assertEqual(report['dtype_policy']['encoder_compute'],'torch.bfloat16')
                self.assertEqual(report,load(out/'dry.json'))
                self.assertGreater(report['peak_rss_bytes'],0)
                self.check_probe(report['head_probe'])
                self.assertIn('encoder_copy',report['grad_norms']) if mode.endswith('vc') else None

    def test_dryrun_failure_report_and_admission(self):
        out,cfg,_,_=self.fixture('decoupled_v')
        (out/'admission.json').write_text('{}')
        with self.assertRaises(ValueError):run.dryrun(cfg,out/'dry.json')
        self.assertEqual(load(out/'dry.json')['status'],'FAIL')
        self.assertIn('prepared',load(out/'dry.json')['phases_seconds'])
        self.assertFalse((Path(cfg['output'])/'train').exists())

    def test_index_order_matches_original_across_wraps(self):
        for count in (1,9,64,79):
            gen=run.index_batches(count)
            order=list(range(count));epoch=-1;cursor=0
            for _ in range(4):
                indices=[]
                while len(indices)<64:
                    if epoch<0 or cursor==len(order):
                        epoch+=1;cursor=0;random.Random(17+epoch).shuffle(order)
                    take=min(64-len(indices),len(order)-cursor)
                    indices.extend(order[cursor:cursor+take]);cursor+=take
                self.assertEqual(next(gen),indices)

    def test_smoke_real_optimizer_mock_distributed(self):
        self.smoke_case(False)

    def test_all_frame_smoke_probes_and_timings(self):
        self.smoke_case(True)

    def test_worker_failure_fails_smoke_step(self):
        self.smoke_case(True, fail_decode=True)

    def smoke_case(self, all_frames, fail_decode=False):
        out,cfg,batch,target=self.fixture('decoupled_vc', fixed=True, all_frames=all_frames)
        load_real=run.load_vision
        class Wrapped:
            def __init__(self,model,**kwargs):self.model=model
            def __call__(self,*args):return self.model(*args)
            def no_sync(self):return nullcontext()
        def cpu_model(*args):
            m=load_real(*args)
            m.to=lambda *a,**k:m
            return m
        class CpuTensor:
            def __init__(self,value):self.value=value
            def to(self,*args):return self.value
        def gather(dest,value):
            dest[:]=[{**value,'rank':r} for r in range(8)]
        with ExitStack() as stack:
            stack.enter_context(patch.dict(os.environ,dict(RANK='0',WORLD_SIZE='8',LOCAL_RANK='0',SLURM_JOB_ID='123')))
            stack.enter_context(patch.object(run,'load_vision',side_effect=cpu_model))
            stack.enter_context(patch.object(run,'processor_for',return_value=None))
            stack.enter_context(patch.object(run,'encode',
                side_effect=ValueError('fixture decode failure') if fail_decode else None,
                return_value={k:CpuTensor(v) for k,v in batch.items()}))
            real_targets=run.target_tensors
            stack.enter_context(patch.object(run,'target_tensors',side_effect=lambda r,d,**kw:
                {k:CpuTensor(v) for k,v in real_targets(r,'cpu',**kw).items()}))
            stack.enter_context(patch('torch.nn.parallel.DistributedDataParallel',Wrapped))
            for name in ('set_device','synchronize','reset_peak_memory_stats'):
                stack.enter_context(patch.object(torch.cuda,name))
            for name in ('max_memory_allocated','max_memory_reserved'):
                stack.enter_context(patch.object(torch.cuda,name,return_value=0))
            for name in ('init_process_group','destroy_process_group','barrier','all_reduce'):
                stack.enter_context(patch('torch.distributed.'+name))
            stack.enter_context(patch('torch.distributed.all_gather_object',side_effect=gather))
            exported=stack.enter_context(patch.object(run,'export_heads'))
            # A milestone inside the smoke must still not export.
            stack.enter_context(patch.dict(run.RECIPE, milestones=[1,2]))
            # Patch recipe identity consistently after changing milestones.
            stack.enter_context(patch.object(run,'prepared',return_value=(load(out/'receipt.json'),load(out/'model.json'))))
            path=Path(cfg['output'])/'smoke/123/smoke.json'
            if fail_decode:
                with self.assertRaisesRegex(ValueError, 'fixture decode failure'):
                    run.train(cfg,3)
                self.assertEqual(load(path)['status'], 'FAIL')
                self.assertEqual(load(path)['steps'], [])
                self.assertFalse((path.parent/'metrics.jsonl').exists())
                exported.assert_not_called()
                return
            run.train(cfg,3)
            report=load(path)
            self.assertEqual(report['status'],'PASS')
            self.assertEqual(len(report['steps']),3)
            self.assertEqual(len(report['per_rank_peak_cuda_memory']),8)
            for step in report['steps']:
                self.assertGreater(step['wall_seconds'],0)
                self.assertEqual(len(step['ranks']),8)
                self.assertGreater(step['ranks'][0]['data_wait_seconds'],0)
                self.assertGreater(step['ranks'][0]['wall_seconds'],0)
                self.assertGreater(step['ranks'][0]['compute_seconds'],0)
            self.assertEqual([p['step'] for p in report['head_probes']], [1,3])
            self.assertEqual(len({p['row_index'] for p in report['head_probes']}), 1)
            for probe in report['head_probes']:
                self.check_probe(probe, 32 if all_frames else 16)
                self.assertEqual(probe['rank'],0)
            exported.assert_not_called()
            self.assertFalse((Path(cfg['output'])/'train').exists())
            before=path.read_bytes()
            with self.assertRaises(FileExistsError):run.train(cfg,3)
            self.assertEqual(path.read_bytes(),before)
            for bad in (0,11,-1,True):
                with self.assertRaises(ValueError):run.train(cfg,bad)


if __name__=='__main__':unittest.main()
