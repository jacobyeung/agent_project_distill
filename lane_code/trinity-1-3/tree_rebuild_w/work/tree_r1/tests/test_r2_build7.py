"""CPU producer/reader proofs for launch pins and native model boundaries."""
from collections import Counter
from copy import deepcopy
import hashlib
import io
import json
import os
from pathlib import Path
import tarfile
import unittest
from unittest.mock import patch

import torch
from student_pilot import b7_inputs as I


def root(name):
    p=Path(os.environ.get('R2_PROOFS',os.environ['TMPDIR']))/name
    p.mkdir(parents=True,exist_ok=True)
    return p


def settings():
    p=dict(artifact_id='4af43b40',sha256='a'*64,location='/project/inputs/a')
    return dict(schema=I.SCHEMA,training_objective='sft',max_pixels=147456,min_pixels=16384,
        frame_count=32,frame_layout='duplicate',frame_markers=True,weight_scale=1.,minority_count=2,
        init=dict(p,selected_by='NEXT_LEG_INIT_RULE_20261116'),
        row_stores={s:[dict(p,family='d0_v5'),dict(p,artifact_id='new',family='a0')]
                    for s in ('vqa','routing')})


class InputTests(unittest.TestCase):
    def test_init_stores_and_layout_refusals(self):
        cfg=settings();I.validate(cfg,'a0')
        for change in ({'sha256':'bad'},{'location':'/tmp/input'},{'selected_by':'other'}):
            bad=deepcopy(cfg);bad['init'].update(change)
            with self.assertRaises(ValueError):I.validate(bad,'a0')
        p=root('pins')/'input';p.write_bytes(b'pin fixture')
        item=dict(artifact_id='fixture',sha256=hashlib.sha256(p.read_bytes()).hexdigest(),location=str(p))
        I.pin(item,verify=True)
        with self.assertRaisesRegex(ValueError,'sha_mismatch'):I.pin(dict(item,sha256='b'*64),verify=True)
        for prefix in I.SEALED_STORES:
            bad=deepcopy(cfg);bad['row_stores']['vqa'][0]['artifact_id']=prefix
            with self.assertRaisesRegex(ValueError,'sealed'):I.row_stores(bad['row_stores'],'a0')
        with self.assertRaisesRegex(ValueError,'dense'):I.validate(cfg,'a2')
        for key,value in [('frame_count',64),('max_pixels',100000),('min_pixels',100),('frame_markers',False),('frame_layout','spread')]:
            with self.assertRaises(ValueError):I.reader_layout(cfg,{**cfg,key:value})
        I.reader_layout(cfg,cfg)
        with self.assertRaisesRegex(ValueError,'weight_scale'):I.validate({**cfg,'weight_scale':0},'a0')
        with self.assertRaisesRegex(ValueError,'bf16_cache'):
            I.validate({**cfg,'gf1_cache_option':dict(enabled=True,dtype='bfloat16')},'a0')
        self.assertEqual(I.claim_reader(),'harness_served')
        from student_pilot.p3_provenance import file_pin
        p=root('claims')/'eat.json'
        p.write_text(json.dumps(dict(schema='eat1-report-v1',mode='dynamic',overall='PASS',artifact_sha256='c'*64,
            clauses={c:{'status':'PASS'} for c in ('A1','A2','A3','A4','A5')})))
        self.assertEqual(I.claim_reader(file_pin(p),'c'*64),'model_served')
        with self.assertRaisesRegex(ValueError,'artifact_binding'):
            I.claim_reader(file_pin(p),'d'*64)
        p.write_text('{}')
        with self.assertRaises(ValueError):I.claim_reader(file_pin(p))

    def test_sources_pass_absent_sha_and_member_refusal(self):
        from launch_r2.input_check import sources
        p=root('staging');raw=b'member bytes';h=hashlib.sha256(raw).hexdigest()
        archive=p/'a.tar'
        with tarfile.open(archive,'w') as f:
            info=tarfile.TarInfo('member');info.size=len(raw);f.addfile(info,io.BytesIO(raw))
        spec=dict(parts=[str(archive)],sha256=hashlib.sha256(archive.read_bytes()).hexdigest(),inventory={'member':h})
        plan=dict(entries={'u/one':dict(archive=spec,member='member',sha256=h)})
        self.assertEqual(sources(plan)['status'],'PASS')
        for bad in (dict(plan,entries={'u/one':dict(required_parameter='init')}),
                    dict(entries={'u/one':dict(parts=[str(p/'absent')],sha256=h)}),
                    dict(entries={'u/one':dict(parts=[str(archive)],sha256='a'*64)}),
                    dict(entries={'u/one':dict(archive=spec,member='member',sha256='a'*64)})):
            with self.assertRaises((ValueError,FileNotFoundError)):sources(bad)

    def test_r0_all_alias_families_and_streams(self):
        from student_pilot.r0_exclusion import Reserve,aliases
        reserve=Reserve()
        captures=json.loads(Path(__import__('student_pilot.r0_exclusion',fromlist=['x']).__file__).with_name('r0_scenes.json').read_text())['captures']
        for ds in ('scannet','scannetpp'):
            capture=next(k for k in captures if k.startswith(ds+'/'))
            for name in aliases(*capture.split('/',1)):
                for stream in ('pose','vqa','routing','pointing','rasters','depth','dense_frames','cache'):
                    with self.assertRaisesRegex(ValueError,'r0_room_refused'):reserve.check({'canonical':name},stream)
        reserve.check({'dataset':'d1','scene':'fixture_clean'},'pose')
        with self.assertRaisesRegex(ValueError,'rule_only'):
            from student_pilot.row_text_audit import check
            check({'target':'heading unavailable'},'camera')

    def test_both_gate_and_sampler(self):
        from student_pilot.carrier_c1_routing import POLICIES
        from student_pilot.routing_type_gate import refusal,sample,validate
        policy=POLICIES['both-path-20261116']
        from student_pilot.carrier_c1_run import routed_type
        item=dict(question_type='object_counting')
        cfg=dict(route_table={'object_counting':'route'})
        self.assertTrue(routed_type(item,cfg))
        self.assertFalse(routed_type(item,{**cfg,'routing_policy':'both-path-20261116'}))
        self.assertIsNone(refusal('object_counting','routed',policy))
        self.assertIsNone(refusal('object_counting','direct',policy))
        self.assertEqual(refusal('object_size_estimation','routed',policy),'no_head_grammar')
        self.assertEqual(refusal('object_rel_direction_easy','routed',policy),'no_head_grammar')
        self.assertEqual(refusal('room_size_estimation','routed',policy),'program_type_not_admitted')
        self.assertEqual(refusal('camera_rotation','direct',policy),'direct_type_not_admitted')
        rows=[dict(qid=f'{form}{i}',question_type='object_counting',answer_form=form,response_heads=['pose'])
              for form in ('direct','routed') for i in range(10)]
        for r in rows:validate(r,policy,['pose'])
        with self.assertRaisesRegex(ValueError,'outside_artifact'):validate(rows[-1],policy,[])
        got=sample(rows,policy,{'object_counting':'direct'},{'object_counting':8},minority_count=2)
        self.assertEqual(Counter(r['answer_form'] for r in got),dict(direct=6,routed=2))
        with self.assertRaisesRegex(ValueError,'missing_minority'):sample(rows[:10],policy,{'object_counting':'direct'},{'object_counting':8},2)

    def test_store_manifest_binding(self):
        from student_pilot.p3_provenance import file_pin
        cfg=settings();paths=[]
        for stream,entries in cfg['row_stores'].items():
            for entry in entries:
                p=root('stores')/(stream+'_'+entry['family']+'.json')
                p.write_text(json.dumps(dict(schema='r2-family-manifest-v1',stream=stream,family=entry['family'])))
                entry['manifests']=[file_pin(p)];paths.append(p)
        self.assertEqual(len(I.bound_manifests(cfg,paths,'a0')),4)
        with self.assertRaisesRegex(ValueError,'selected_row_store_manifest_missing'):
            I.bound_manifests(cfg,paths[:-1],'a0')
        bad=root('stores')/'unbound.json';bad.write_text(json.dumps(dict(stream='vqa',family='wrong')))
        with self.assertRaisesRegex(ValueError,'unbound_row_store_manifest'):
            I.bound_manifests(cfg,[*paths,bad],'a0')

    def test_scale_loss_and_trainable_inventory(self):
        from tests.test_carrier_c1 import fixture
        model,batch,target=fixture(training_mode='final')
        import numpy as np
        from student_pilot.pose_samples import encode_sample
        poses=np.repeat(np.eye(4)[None],32,axis=0)
        poses[:,0,3]=np.arange(32)*.2
        intrinsics=np.repeat(np.array([[80.,0.,56.],[0.,80.,40.],[0.,0.,1.]])[None],32,axis=0)
        camera,mask,scale,gravity=encode_sample(poses,intrinsics,(80,112),list(range(32)),max_groups=32,all_frames=True)
        target['aux_camera_target']=torch.tensor(camera,dtype=torch.float32)[None]
        target['aux_camera_mask']=torch.tensor(mask)[None]
        target['aux_camera_scale']=torch.tensor([scale],dtype=torch.float32)
        target['aux_gravity_target']=torch.tensor(gravity,dtype=torch.float32)[None]
        model.auxiliary_heads.pose.settings['weight_scale']=1.
        result=model(batch,target,stream='pose')
        self.assertTrue(torch.isfinite(result['loss']))
        self.assertGreater(result['metrics']['pose_parts']['scale'],0.)
        result['loss'].backward()
        names=[(n,p) for n,p in model.named_parameters() if 'scale' in n and p.grad is not None]
        self.assertTrue(any(torch.isfinite(p.grad).all() and p.grad.abs().sum()>0 for n,p in names))
        inventory=I.module_trainability(model,dict(pose_lr_scale=.6,lm_lr_scale=.6))
        self.assertTrue(inventory['base_vit'])
        self.assertFalse(any(p['trainable'] for p in inventory['base_vit']+inventory['merger']))
        I.assert_modules(model,dict(pose_lr_scale=.6,lm_lr_scale=.6),inventory)
        (root('scale')/'RESULT.json').write_text(json.dumps(dict(loss=float(result['loss'].detach()),
            gt_trajectory_scale=float(scale),gt_log_scale=float(torch.log(target['aux_camera_scale'])[0]),
            scale_gradient_parameters=[n for n,p in names],components={k:str(v) for k,v in result.items() if k!='loss'},
            trainable=inventory),indent=2))

    def test_real_export_manifest_and_reader(self):
        from tests.test_carrier_c1 import fixture
        from student_pilot import carrier_c1_run as run
        from student_pilot.p3_provenance import file_pin
        model,batch,target=fixture(4)
        cfg=dict(base_identity='tiny-fixture',trace_program_version='3.13',b7_inputs=settings(),
                 max_pixels=147456,min_pixels=16384,frame_count=32,frame_markers=True,
                 camera_overrides={'weight_scale':1.})
        # Export's collective/FSDP collection boundary is replaced by one CPU rank.
        directory=root('export')/'slot'
        if not directory.exists():
            with patch.object(run.dist,'get_rank',return_value=0),patch.object(run.dist,'get_world_size',return_value=1), \
                 patch.object(run.dist,'barrier'),patch('student_pilot.fsdp_training.publication_state',return_value=model.state_dict()):
                run.export(directory,model,model,cfg,1)
        manifest=json.loads((directory/'eat1-artifact.json').read_text())
        self.assertEqual(manifest['schema'],'eat1-artifact-v1')
        self.assertIn('auxiliary_heads.pose',manifest['modules'])
        for name,entry in manifest['files'].items():
            self.assertEqual(hashlib.sha256((directory/name).read_bytes()).hexdigest(),entry['sha256'])
        fresh,_,_=fixture(4)
        run.load_artifact(fresh,file_pin(directory/'artifact.json'))
        self.assertTrue(fresh.probe(batch,target)['finite'])

    def test_faithful_identity_gate(self):
        from student_pilot import h1_faithful as h
        cfg=dict(h1={'faithful_own_camera_rows':True},streams={'routing':{'path':'bound','sha256':'a'*64}},
                 scheduled_sampling={'max_own_probability':.5,'force_from_step':1})
        h.validate(cfg)
        value=dict(h1_faithful_identity=dict(source_receipt=cfg['streams']['routing'],rows=100,identity_rate=.95,passes=True))
        h.require_identity(value,cfg)
        for rate in (None,.94):
            value['h1_faithful_identity']['identity_rate']=rate
            with self.assertRaisesRegex(ValueError,'95%'):h.require_identity(value,cfg)
        h.require_identity({},dict(h1={'faithful_own_camera_rows':False}))
        with self.assertRaises(ValueError):h.validate(dict(h1={'faithful_own_camera_rows':'yes'}))

    def test_gf1_export_declares_tower(self):
        from tests.test_gf1 import fixture
        from student_pilot import carrier_c1_run as run
        from student_pilot.p3_provenance import file_pin
        model,batch,cfg=fixture()
        p=root('gf1_export')
        weights=p/'tiny_tower.pt'
        torch.save(model.auxiliary_heads.geometry_encoder.state_dict(),weights)
        config=p/'tiny_config.json';config.write_text(json.dumps({'fixture':'native tiny G3T'}))
        model.geometry_online['encoder']['weights']=file_pin(weights)
        model.geometry_online['encoder']['config']=file_pin(config)
        cfg.update(base_identity='tiny-fixture',b7_inputs=settings(),max_pixels=147456,min_pixels=16384,
                   frame_count=32,frame_markers=True,camera_overrides={'weight_scale':1.})
        directory=p/'slot'
        if not directory.exists():
            with patch.object(run.dist,'get_rank',return_value=0),patch.object(run.dist,'get_world_size',return_value=1), \
                 patch.object(run.dist,'barrier'),patch('student_pilot.fsdp_training.publication_state',return_value=model.state_dict()):
                run.export(directory,model,model,cfg,1)
        manifest=json.loads((directory/'eat1-artifact.json').read_text())
        self.assertEqual(manifest['modules']['auxiliary_heads.geometry_encoder'],dict(role='tower',name='g3t'))
        self.assertTrue(any(e['role']=='tower' and e['sha256']==file_pin(weights)['sha256'] for e in manifest['files'].values()))
        for path in manifest['modules']:self.assertIsInstance(model.get_submodule(path),torch.nn.Module)

    def test_native_frame_capacity(self):
        from tests.test_carrier_c1 import fixture,Tokenizer
        from student_pilot.carrier_c1_data import insert_frame_carriers
        from student_pilot.carrier_c1 import CarrierC1
        from student_pilot.carrier_c1_decode import parse_head
        from transformers import Qwen3_5ForConditionalGeneration
        original,_,_=fixture(depth_enabled=False)
        measurements=[]
        for count in (32,64):
            tok=Tokenizer();tok._c1_frame_count=count
            ids=torch.tensor([[2]+[v for _ in range(count) for v in (62,61,63)]+[10,11]])
            batch=dict(input_ids=ids,attention_mask=torch.ones_like(ids),labels=torch.full_like(ids,-100),
                mm_token_type_ids=torch.where(ids==61,2,0),video_grid_thw=torch.tensor([[count,2,2]]),
                pixel_values_videos=torch.randn(count*4,24))
            batch=insert_frame_carriers(batch,tok,frame_layout='duplicate')
            base=Qwen3_5ForConditionalGeneration(original.config).float()
            model=CarrierC1(base,dict(embed_dim=64,num_heads=4,trunk_depth=4,refine_iterations=4,
                weight_gravity=1.,weight_scale=1.,supervision={'path':'/fixture','sha256':'a'*64}),{},5,
                training_mode='final',depth_enabled=False,frame_layout='duplicate',frame_count=count)
            with torch.no_grad():output=model.pose_readout(batch)
            self.assertEqual(output.shape,(count,9))
            self.assertEqual(parse_head(f'<pose frame={count}>',count)['frame'],count)
            measurements.append(dict(frame_count=count,visual_tokens=int((ids==61).sum()),carriers=batch['aux_camera_positions'].shape[1]))
        (root('frames')/'TOKENS.json').write_text(json.dumps(measurements,indent=2))

    def test_response_spec_and_stop_fallback(self):
        from student_pilot.response_spec import check,format_response
        for text in ('<tool_response>turn = +45 deg</tool_response>',
                     '<tool_response>\ndistance 1.50 m\n</tool_response>',
                     '<tool_response>dx = +1.00 m, dy = -2.00 m, dz = +0.00 m, distance = 2.24 m</tool_response>'):
            self.assertEqual(format_response(check(text)),text)
        with self.assertRaises(ValueError):check('<tool_response>distance 1.5 m</tool_response>')
        from student_pilot.stop_control import requested
        with patch.dict(os.environ,{'K3':str(root('stop')/'absent'),'R1_STOP_FILE':''}):
            self.assertFalse(requested(False,{'stop_after_step':3},2))
            self.assertTrue(requested(False,{'stop_after_step':3},3))
            p=root('stop')/'stop';p.write_text('USR1\n');os.environ['K3']=str(p)
            self.assertTrue(requested(False,{},2))

    def test_reader_preserves_answer_text(self):
        from evalpath.runtime import generate
        expected=dict(text='<answer>1.2300 metres</answer>',tokens=[1,2],calls=[])
        with patch('student_pilot.carrier_c1_decode.generate',return_value=expected):
            self.assertIs(generate(None,None,{},'routed'),expected)

    def test_portrait_and_landscape_mask_audit(self):
        import numpy as np
        from student_pilot.routed_features import resize
        from student_pilot.response_spec import check
        from tests.test_carrier_c1_routing import FixedLayerConventions
        proof=[]
        for shape in ((80,40),(40,80)):
            mask=np.zeros(shape,bool)
            h,w=shape;mask[h//2-5:h//2+5,w//2-5:w//2+5]=True
            actual=resize(mask,(240,320));ys,xs=np.where(actual)
            proof.append(dict(input_shape=shape,output_shape=actual.shape,
                aspect_distorted=(240/shape[0] != 320/shape[1]),
                square_output_extent=[int(ys.max()-ys.min()+1),int(xs.max()-xs.min()+1)]))
            self.assertEqual(actual.shape,(240,320))
        (root('portrait')/'RESULT.json').write_text(json.dumps(proof,indent=2))
        fixture=FixedLayerConventions();fixture.setUp()
        for body in (fixture.own.pose_text(2),fixture.own.move_text(2,8),fixture.own.turn_text(2,8)):
            check('<tool_response>'+body+'</tool_response>')
