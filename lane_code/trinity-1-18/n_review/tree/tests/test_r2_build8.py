"""Bounded native producers and readers for build-eight CPU branches."""
import copy
import hashlib
import json
import os
from pathlib import Path
import sqlite3
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import numpy as np
import torch
from student_pilot.p3_provenance import file_pin, load, write
from tests import test_r2_data_path as D
from tests import test_r2_build7 as B7


def folder(name):
    # Native producers require fresh scratch products. The harness overwrites
    # these temporary products with hash receipts after each test.
    return D.directory()


def inputs(root):
    value=B7.settings()
    base=Path(os.environ['R2_PROOFS'])/'input_pins';base.mkdir(exist_ok=True)
    p=base/'pinned_input';p.write_bytes(b'CPU boundary input metadata')
    for pin in [value['init']]+sum(value['row_stores'].values(),[]):
        pin.update(location=str(p),sha256=file_pin(p)['sha256'])
    return value


class InputReaders(unittest.TestCase):
    def test_host_reader_refuses_unbound_manifests(self):
        from launch_r2 import host
        p=folder('host_binding');pins=[];manifests=[]
        for i in range(2):
            source=p/f'pose{i}.json';source.write_text(json.dumps({'source':i}));pin=file_pin(source);pins.append(pin)
            m=p/f'm{i}.json';m.write_text(json.dumps(dict(stream='pose',pose_source_sha256=pin['sha256'])))
            manifests.append(file_pin(m))
        cfg=p/'config.json';cfg.write_text(json.dumps({'b7_inputs':inputs(p)}))
        packet=dict(pose_sources=pins,manifests=manifests,configuration=file_pin(cfg),
                    pose_template=pins[0],real_proof=pins[0],counts=pins[0],output='out')
        with self.assertRaisesRegex(ValueError,'manifest_bindings_missing'):
            host.execute_packet(p,packet,host.Guard(p),full=False)

    def test_native_wrapper_publishes_rank_stop_poll_path(self):
        import importlib.util,sys
        from student_pilot.stop_control import requested
        p=folder('wrapper');wrapper=Path(__file__).parents[1]/'launch_s1/b/w.py'
        spec=importlib.util.spec_from_file_location('coverage_b8_wrapper',wrapper)
        module=importlib.util.module_from_spec(spec)
        with patch.object(sys,'path',[str(wrapper.parent),*sys.path]):spec.loader.exec_module(module)
        env={k:v for k,v in os.environ.items() if k not in ('K3','R1_STOP_FILE')}
        with patch.dict(os.environ,env,clear=True):
            with self.assertRaises(FileNotFoundError):module.main(p,'t','0')
            self.assertEqual(os.environ['K3'],os.environ['R1_STOP_FILE'])
            self.assertFalse(requested(False,{},1))
            stop=Path(os.environ['K3']);stop.parent.mkdir(parents=True,exist_ok=True);stop.write_text('USR1\n')
            self.assertTrue(requested(False,{},1))

    def test_runtime_staging_and_complete_begin_checks(self):
        from tests.test_r2_build5_host_order import fixture
        from launch_r2 import host, staging
        import sys
        root,packet,cfg,entries,executable=fixture()
        with patch.object(staging,'P',str(root)),patch.object(sys,'executable',str(executable)):
            checks=host.begin_checks(root,packet)
        self.assertIsInstance(checks.cfg,dict)
        self.assertTrue(all(file_pin(root/name)['sha256']==entry['sha256'] for name,entry in entries.items()))

    def test_manifest_policy_reaches_real_intake_and_program_reader(self):
        from student_pilot.r2_intake import intake
        from student_pilot import r2_grammar
        p=folder('intake');row=D.fixture(p,stream='routing')
        row['answer_form']='routed';row['response_heads']=['pose']
        manifest=D.manifest(p/'source',[row],'routing')
        value=load(manifest);value.update(routing_policy='both-path-20261116',artifact_heads=['pose'])
        manifest.write_text(json.dumps(value))
        admitted,report=intake(manifest)
        self.assertEqual(len(admitted),1,report)
        checked=admitted[0]['row']
        self.assertEqual(r2_grammar.validate_program(checked)[0],row['target'])
        bad=copy.deepcopy(checked);bad['question_type']='object_size_estimation'
        with self.assertRaisesRegex(ValueError,'no_head_grammar'):
            r2_grammar.validate_program(bad)
        (p/'RESULT.json').write_text(json.dumps(report,indent=2))

    def test_bound_input_validation_and_cache_configuration(self):
        from student_pilot import carrier_c1_run as R,r2_contract as C,r2_config as N
        from student_pilot.carrier_c1_sweep import recipe_for
        p=folder('config');bound=inputs(p)
        cfg=dict(schema='carrier-c1-run-v1',training_mode='final',depth_fov_source='pose_head',
            carrier_placement=R.data.C1_A,init='base',parallel='fsdp',all_frames=True,
            streams={k:{} for k in ('pose','vqa','pointing','routing')},frame_layout='duplicate',
            mix=['pose','vqa','pointing','routing'],world_size=4,
            b7_inputs=bound,h1=dict(faithful_own_camera_rows=False))
        cfg['scheduled_sampling']=dict(seed=17,max_own_probability=0.,pose_open_deg=45.,pose_full_deg=25.,
            fov_open_deg=2.,depth_open_absrel=.25,ema_steps=100,force_from_step=None,
            exposure_from_step=None,exposure_probability=0.)
        cfg['recipe']=recipe_for(cfg);R.validate(cfg)
        self.assertIsNone(C.preparation({'b7_inputs':bound}))
        from tests.test_gf1_cache import settings
        cfg=dict(geometry_connector='gf1',steps=2,milestones=[2],r2_stage=dict(stage=1,init='zero',learning_rate=1e-4),
                 b7_inputs=dict(gf1_cache_option=dict(enabled=True,dtype='float32',root=str(p/'bank'))))
        value=N.apply_native(cfg,settings())
        self.assertEqual(value['geometry_online']['gf1']['cached_bank'],dict(dtype='float32',root=str(p/'bank')))
        cfg['b7_inputs']['gf1_cache_option']['dtype']='bfloat16'
        with self.assertRaisesRegex(ValueError,'bf16_cache_gradient_parity_unqualified'):N.apply_native(cfg,settings())

    def test_real_materializer_rows_and_frame_loader_refusals(self):
        from student_pilot.r2_materialize import materialize
        from student_pilot import carrier_c1_run as R,carrier_c1_data as data
        p=folder('rows');row=D.fixture(p);manifest=D.manifest(p/'source',[row])
        with patch.dict(os.environ,STUDENT_FRAME_ROOT_MAP=json.dumps({'/logical/r2':str(p/'frames')})):
            report=materialize([manifest],p/'store')
            native=load(report['receipt']['path'])
            reader=R.Rows.__new__(R.Rows)
            reader.indices={};reader.b7_inputs=inputs(p);reader.r2_admission=None
            reader.connections={'vqa':sqlite3.connect(native['streams']['vqa']['database']['path'])}
            try:
                actual,_=reader.row('vqa',0)
                self.assertEqual(actual['qid'],row['qid'])
            finally:reader.connections['vqa'].close()
            processor=D.TinyProcessor();processor._b7_layout=B7.settings();processor.tokenizer._c1_frame_count=32
            encoded,audit=data.encode_layout_row(processor,actual,'duplicate',None)
            self.assertEqual(encoded['video_grid_thw'][0,0],32)
            bad=copy.deepcopy(actual);bad['student_input']['frames']=bad['student_input']['frames'][:-1]
            with self.assertRaisesRegex(ValueError,'row_training_frame_count_mismatch'):
                data.encode_layout_row(processor,bad,'duplicate',None)

    def test_processor_loader_binds_layout(self):
        from student_pilot import carrier_c1_run as R
        processor=D.TinyProcessor()
        with patch.object(R,'processor_for',return_value=processor):
            got=R.processor_for_receipt({'root':'tiny pretrained processor boundary'},{'b7_inputs':B7.settings(),'frame_count':64})
        self.assertIs(got,processor);self.assertEqual(got.tokenizer._c1_frame_count,64)
        self.assertEqual(got._b7_layout['frame_count'],32)

    def test_native_readout_refuses_incomplete_frames_and_depth_slots(self):
        from tests.test_carrier_c1 import fixture
        from student_pilot.carrier_c1_decode import HeadState
        model,batch,target=fixture(training_mode='final')
        bad=copy.deepcopy(batch);bad['aux_camera_positions'][0,-1]=-1
        with self.assertRaisesRegex(ValueError,'every configured frame'):model.pose_readout(bad)
        with self.assertRaisesRegex(ValueError,'configured visible frames'):model.readout(batch,np.zeros((3,1,2)))
        with self.assertRaisesRegex(ValueError,'every configured frame'):
            HeadState(model,bad,torch.zeros(1,bad['input_ids'].shape[1],32))

    def test_pose_and_response_refusals(self):
        from student_pilot.pose_samples import encode_sample
        from student_pilot import response_spec as S
        with self.assertRaisesRegex(ValueError,'supported pinned frame count'):
            encode_sample(np.repeat(np.eye(4)[None],4,axis=0),np.repeat(np.eye(3)[None],4,axis=0),(8,8),list(range(4)),max_groups=16,all_frames=True)
        text='<tool_response>\ndistance 1.50 m\n</tool_response>'
        self.assertEqual(S.format_response(S.parse(text)),text)
        from trace_format.ground_v313 import Session
        from trace_format import room_v314
        from tests.test_room_v314 import Sensor
        body=Session(None,Sensor(),None,program_version='3.14').execute(room_v314.CALL)
        text='<tool_response>\n'+body+'\n</tool_response>'
        self.assertEqual(S.format_response(S.parse(text)),text)


class PreparationReaders(unittest.TestCase):
    def test_native_own_camera_forward_and_sqlite_reader(self):
        from tests.coverage_b8_rows import camera_row
        from tests.test_carrier_c1 import fixture
        from student_pilot import carrier_c1_run as R,carrier_c1_routing as C
        p=folder('own_camera');source=D.fixture(p)
        raw=camera_row(source['student_input']['frames'],kind='camera_rotation')
        rgb=dict(frames=[dict(f,source_index=i) for f,i in zip(source['student_input']['frames'],source['student_input']['frame_indices'])],fps=10,total_num_frames=64)
        row=C.c1_row(raw,rgb)
        database=p/'rows.sqlite'
        with sqlite3.connect(database) as conn:
            conn.execute('CREATE TABLE rows (i INTEGER,row TEXT,target TEXT)')
            conn.execute('INSERT INTO rows VALUES (0,?,?)',(json.dumps(row),'{}'))
        processor=D.TinyProcessor()
        rows=R.Rows(dict(streams={'routing':dict(count=1,database=file_pin(database))},
                        h1={'faithful_own_camera_rows':True}),processor)
        model,batch,_=fixture(training_mode='final',depth_enabled=False)
        # Tiny head weights stand in at the unavailable trained-model boundary.
        # The real forward computes identity cameras with a horizontal heading.
        with torch.no_grad():
            pose=model.auxiliary_heads.pose.head.pose_branch.fc2
            pose.weight.zero_();pose.bias.zero_();pose.bias[6]=1
            gravity=model.auxiliary_heads.pose.head.gravity_branch.fc2
            gravity.weight.zero_();gravity.bias.copy_(torch.tensor([0.,-1.,0.]))
        batch['aux_suffix_start']=torch.tensor([batch['input_ids'].shape[1]-2])
        try:
            changed,audit=R.own_values(model.eval(),rows,batch,{},0,(False,True),torch.device('cpu'))
            self.assertEqual(audit['h1']['values'],'own',audit)
            self.assertNotEqual(changed['input_ids'].shape,batch['input_ids'].shape)
            row['routing']['events']=[e for e in row['routing']['events'] if e['kind']!='tool_response']
            rows.connections['routing'].close()
            with sqlite3.connect(database) as conn:conn.execute('UPDATE rows SET row=?',(json.dumps(row),))
            rows.connections['routing']=sqlite3.connect(database)
            unchanged,audit=R.own_values(model.eval(),rows,batch,{},0,(False,True),torch.device('cpu'))
            self.assertEqual(audit['h1']['values'],'gt')
            self.assertIn('no_head_calls',audit['h1']['refused'])
        finally:rows.close()

    def test_materializer_render_consistency_refuses_corrupted_bytes(self):
        from tests.coverage_b8_rows import camera_row
        from student_pilot import h1_faithful as H,carrier_c1_routing as R
        row=camera_row();result,target,_,_=H.faithful(row,R.RecordedGeometry(row))
        H.require_render_identity(result,target)
        corrupt=json.loads(json.dumps(result));corrupt['target']+='corrupted fixture'
        with self.assertRaisesRegex(H.MaterializeRefusal,'faithful_render_mismatch'):
            H.require_render_identity(corrupt,target)

    def test_native_preparation_pins_identity_and_own_readout(self):
        from tests.coverage_b8_preparation import PreparationProof
        from student_pilot import carrier_c1_run as R
        from tests.test_carrier_c1 import fixture
        cfg,receipt,faithful_receipt=PreparationProof().prepare_native()
        root=Path(cfg['preparation_output']).parent
        with patch.dict(os.environ,S1_CPU_REHEARSAL='1',STUDENT_FRAME_ROOT_MAP=json.dumps({'/logical/r2':str(root/'frames')})):
            actual,_=R.prepared(cfg)
            self.assertEqual(actual['h1'],cfg['h1'])
            self.assertTrue(faithful_receipt['h1_faithful_identity']['passes'])
            changed=copy.deepcopy(cfg);changed['b7_inputs']['frame_count']=64
            with self.assertRaisesRegex(ValueError,'Preparation pinned kit inputs differ'):R.prepared(changed)
            with self.assertRaisesRegex(ValueError,'faithful identity'):
                R.prepared({**cfg,'h1':{'faithful_own_camera_rows':True}})
            processor=D.TinyProcessor()
            reader=R.Rows(receipt,processor)
            try:pose,_=reader.row('pose',0)
            finally:reader.close()
            batch,audit=R.data.encode_layout_row(processor,pose,'duplicate',None)
            self.assertTrue(torch.isfinite(batch['pixel_values_videos']).all())
            self.assertEqual(batch['video_grid_thw'][0,0],len(pose['student_input']['frames']))
            proof=Path(os.environ['R2_PROOFS'])/'PREPARATION.json'
            proof.write_text(json.dumps(dict(identity=faithful_receipt['h1_faithful_identity'],
                real_functions=['prepare','prepared','Rows.row','encode_layout_row','check_sample'],
                stand_ins=['tiny native LM and pose head weights','tiny pretrained processor and model metadata']),default=str,indent=2))

    def test_native_legacy_producer_and_reader_with_both_policy(self):
        from tests.coverage_b8_rows import camera_row
        from student_pilot import carrier_c1_routing as R
        from student_pilot import decoupled_v_run
        p=folder('legacy_builder');fixture=D.fixture(p)
        fixture['student_input']['frames']=[file_pin(p/'frames'/Path(f['path']).name) for f in fixture['student_input']['frames']]
        frames=[dict(f,source_index=i) for f,i in zip(fixture['student_input']['frames'],fixture['student_input']['frame_indices'])]
        rgb=p/'rgb.json';rgb.write_text(json.dumps(dict(frames=frames,fps=10,total_num_frames=64)))
        raw=camera_row(fixture['student_input']['frames']);raw['provenance']['rgb_manifest']=file_pin(rgb)
        raw['provenance']['source_row_sha256']=hashlib.sha256(b'synthetic explicit geometry').hexdigest()
        raw['head_layout']='per_frame'
        source=p/'source.jsonl';source.write_text(json.dumps(raw)+'\n'+json.dumps(raw)+'\n')
        index=p/'index.json';index.write_text(json.dumps(dict(manifests={file_pin(rgb)['sha256']:str(rgb)})))
        division=p/'division.json';division.write_text(json.dumps(dict(schema='diagnostic-whole-scene-division-v1',training_only=True,
            train_scenes=[raw['provenance']['alias']],heldout_scenes=[])))
        # The tokenizer is the only unavailable pretrained boundary.
        processor=D.TinyProcessor()
        processor.tokenizer.add_special_tokens=lambda value:0
        processor.tokenizer.special=dict(processor.tokenizer.special)
        processor.tokenizer.get_vocab=lambda:dict(processor.tokenizer.special)
        def add_tokens(values):
            for token in values:processor.tokenizer.special[str(token)]=500+len(processor.tokenizer.special)
        processor.tokenizer.add_tokens=add_tokens
        with patch.object(decoupled_v_run,'processor_for',return_value=processor),patch.dict(os.environ,STUDENT_FRAME_ROOT_MAP=''):
            result=R.build_routing_stream(file_pin(source),file_pin(index),file_pin(division),p/'out','fixture',
                policy='both-path-20261116',exclusions=file_pin(D.RECORDS/D.SOURCES['benchmark']))
        self.assertEqual(result['count'],1,result)
        self.assertEqual(result['refused']['duplicate_qid'],1)
        with sqlite3.connect(p/'out/rows.sqlite') as conn:
            row=json.loads(conn.execute('SELECT row FROM rows').fetchone()[0])
        self.assertEqual(row['answer_form'],'routed')
        self.assertEqual(R.render(row['routing']['events'],row['routing']['answer'])[0],row['target'])


class CacheReaders(unittest.TestCase):
    def test_native_shuffle_guard_refuses_corrupt_assignment(self):
        from student_pilot import gf1_cache as C
        units=[dict(clip_key=k,dataset='fixture',grid=[32,4,4]) for k in ('a','b','c')]
        plan=C.shuffled_bank_plan(units,17)
        donor={p['clip_key']:p['donor_clip_key'] for p in plan['pairs']}
        expected={v['clip_key']:v for v in units}
        C.require_derangement(donor,expected)
        donor['a']='a'
        with self.assertRaisesRegex(AssertionError,'not a derangement'):C.require_derangement(donor,expected)

    def test_native_shared_bank_and_malformed_tower_boundaries(self):
        from student_pilot import gf1_cache as C,gf1,g3t_online as G
        from tests.test_gf1_cache import settings,write_clip_frames,model_for,text_batch,online_geometry
        p=folder('shared');row=write_clip_frames(p,'frames',14)
        model=model_for(settings());model.eval()
        batch=text_batch();batch.update(online_geometry(row));batch['aux_gf1_rowbanks']=C.RowBanks([None])
        encoder=model.auxiliary_heads.geometry_encoder
        with torch.no_grad():cameras,bank=G.features(encoder,batch['aux_g3t_images'][0],batch['aux_g3t_coords'][0])
        shared=gf1.SharedHeadFeatures(encoder,model.geometry_online['gf1']['layers'],cameras,bank)
        batch['aux_gf1_shared']=shared
        _,clips=C.rowbank_features(model,batch)
        self.assertEqual(clips[0][0].shape[:2],(3,32))
        with torch.no_grad():self.assertTrue(torch.isfinite(model.hidden(batch)).all())
        for layers,broken in (([23],bank),(shared.layers,bank[:,:,:15])):
            batch['aux_gf1_cache']=gf1.ClipCache()
            batch['aux_gf1_shared']=gf1.SharedHeadFeatures(encoder,layers,cameras,broken)
            with self.assertRaisesRegex(ValueError,'different owner|not square'):C.rowbank_features(model,batch)
        donor=C.RowBank('dense',torch.arange(0,64,2),images=batch['aux_g3t_images'][0,:63],coords=batch['aux_g3t_coords'][0,:63])
        batch['aux_gf1_rowbanks']=C.RowBanks([donor]);batch['aux_gf1_cache']=gf1.ClipCache()
        with self.assertRaisesRegex(ValueError,'donor frames'):C.rowbank_features(model,batch)

    def test_native_cache_corruption_refusals(self):
        from student_pilot import gf1_cache as C,g3t_online as G
        from tests.test_gf1_cache import Tiny,settings,write_clip_frames,small_square,GRID
        p=folder('cache_corruption');row=write_clip_frames(p,'frames',8)
        torch.manual_seed(8);encoder=Tiny(settings()).eval()
        with patch.object(G,'native_square_518',small_square):
            record=C.write_clip(encoder,row,p/'bank',grid=list(GRID),dtype='float32')
            key=record['clip_key'];pin=p/'bank'/(key+'.json');tensor=p/'bank'/(key+'.safetensors')
            self.assertEqual(C.load_cached(dict(root=str(p/'bank'),dtype='float32'),key,record['anchor_slots']).tensor.shape,tuple(record['shape']))
            wrong=copy.deepcopy(record);wrong['shape'][-1]+=1;pin.write_text(json.dumps(wrong))
            with self.assertRaisesRegex(ValueError,'dtype or shape'):C.load_cached(dict(root=str(p/'bank'),dtype='float32'),key,record['anchor_slots'])
            with self.assertRaisesRegex(ValueError,'rewrite differs'):C.write_clip(encoder,row,p/'bank',grid=list(GRID),dtype='float32')
            orphan=p/'orphan';orphan.mkdir();(orphan/tensor.name).write_bytes(b'orphan fixture, no tensor copied')
            with self.assertRaisesRegex(ValueError,'without its identity record'):C.write_clip(encoder,row,orphan,grid=list(GRID),dtype='float32')
        (p/'RESULT.json').write_text(json.dumps(dict(real_functions=['write_clip','load_cached'],
            stand_ins=['seeded tiny registered frozen tower','tiny square raster at tower boundary'],
            tensor_sha256=record['tensor']['sha256'])))

    def test_dense_membership_invalid_shuffle_and_missing_block(self):
        from student_pilot import gf1_cache as C,dense_eval as E
        from tests.test_gf1_cache import settings,write_clip_frames
        p=folder('dense');row=write_clip_frames(p,'frames',9);row['video_id']='clip'
        with self.assertRaisesRegex(ValueError,'Shuffled-bank option'):
            E.prepare_membership([row],{'clip':row['student_input']['geometry_dense']},settings()['gf1'],p/'out',shuffle={'unknown':1})
        geometry={k:v for k,v in settings().items() if k!='gf1'}
        cfg=p/'config.json';cfg.write_text(json.dumps({'geometry_online':geometry}))
        import sys
        with patch.object(sys,'argv',['cache','--run-config',str(cfg),'--rows',str(cfg),'--root',str(p/'bank'),'--device','cpu','--dtype','float32']):
            with self.assertRaisesRegex(ValueError,'no GF1 block'):C.main()
