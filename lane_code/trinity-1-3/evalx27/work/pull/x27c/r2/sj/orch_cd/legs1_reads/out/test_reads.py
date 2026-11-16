"""CPU tests retain every fixture under work/tests; they never remove files."""
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import struct
import sys
import unittest
import uuid

sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parent.parent
for key,value in dict(CUDA_VISIBLE_DEVICES='',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1',HF_HUB_OFFLINE='1',
    TRANSFORMERS_OFFLINE='1',TOKENIZERS_PARALLELISM='false',HF_HOME=str(ROOT/'work/cache/hf'),
    XDG_CACHE_HOME=str(ROOT/'work/cache'),TMPDIR=str(ROOT/'work/tmp')).items():os.environ[key]=value
(ROOT/'work/tmp').mkdir(parents=True,exist_ok=True)
sys.path.insert(0,str(ROOT/'out'))
from common import *
import decision as D
import export_check as E
import direct
import routed

def fresh(name):
    p=ROOT/'work/tests'/(name+'_'+uuid.uuid4().hex[:10]);p.mkdir(parents=True);return p

def simple_rows(value=1,n=100,typ='object_abs_distance',stratum='primary'):
    return [dict(key=str(i),room='physical_room_'+str(i//5),question_type=typ,stratum=stratum,
        scores=dict(answer=value,released_answer=value),capped=False,called=True,call_errors=0,version_errors=0,
        checkpoint_sha256='a'*64,perception_identity='same-predicted-perception') for i in range(n)]

def fixture_export(root):
    base=root/'base';base.mkdir(); milestone=root/'m100';full=milestone/'full_weights';full.mkdir(parents=True)
    def tensor(path,dtype='BF16',shape=[2]):
        h=json.dumps({'model.weight':dict(dtype=dtype,shape=shape,data_offsets=[0,4])}).encode()
        path.write_bytes(struct.pack('<Q',len(h))+h+b'\x00\x00\x00\x00')
    tensor(base/'model.safetensors');shard=full/'weights.safetensors';tensor(shard)
    dump(full/'model.safetensors.index.json',dict(weight_map={'model.weight':shard.name}))
    manifest=dict(schema='full-ft-export-v1',dtype='bfloat16',tensor_count=1,
        index=dict(name='model.safetensors.index.json',sha256=sha(full/'model.safetensors.index.json')),
        files=[dict(name=shard.name,sha256=sha(shard),bytes=shard.stat().st_size,tensors=1)])
    dump(full/'full_weights.json',manifest)
    dump(milestone/'artifact.json',dict(schema='carrier-c1-artifact-v1',step=100,full_weights=pin(full/'full_weights.json')))
    return milestone/'artifact.json',base

class ExportTests(unittest.TestCase):
    def setUp(self):self.root=fresh('export');self.artifact,self.base=fixture_export(self.root)
    def check(self,**kw):return E.check_export(self.artifact,sha(self.artifact),self.base,100,**kw)
    def mutate_manifest(self,fn):
        p=self.artifact.parent/'full_weights/full_weights.json';m=load(p);fn(m);dump(p,m)
        a=load(self.artifact);a['full_weights']=pin(p);dump(self.artifact,a)
    def test_valid_complete_direct_export(self):self.assertEqual(self.check()['status'],'VERIFIED')
    def test_artifact_sha(self):
        with self.assertRaisesRegex(ValueError,'hash'):E.check_export(self.artifact,'a'*64,self.base)
    def test_step(self):
        with self.assertRaisesRegex(ValueError,'step'):E.check_export(self.artifact,sha(self.artifact),self.base,200)
    def test_schema(self):
        a=load(self.artifact);a['schema']='wrong';dump(self.artifact,a)
        with self.assertRaises(ValueError):self.check()
    def test_missing_full_weights_pin(self):
        dump(self.artifact,dict(schema='carrier-c1-artifact-v1',step=100))
        with self.assertRaises(KeyError):self.check()
    def test_wrong_absolute_manifest_path(self):
        a=load(self.artifact);a['full_weights']['path']=str(self.root/'elsewhere');dump(self.artifact,a)
        with self.assertRaisesRegex(ValueError,'path'):self.check()
    def test_manifest_digest(self):
        p=self.artifact.parent/'full_weights/full_weights.json';p.write_text(p.read_text()+' ')
        with self.assertRaisesRegex(ValueError,'Pin'):self.check()
    def test_dtype(self):
        self.mutate_manifest(lambda m:m.update(dtype='float32'))
        with self.assertRaises(ValueError):self.check()
    def test_missing_index(self):
        self.mutate_manifest(lambda m:m['index'].update(name='missing.json'))
        with self.assertRaises(ValueError):self.check()
    def test_index_hash(self):
        self.mutate_manifest(lambda m:m['index'].update(sha256='a'*64))
        with self.assertRaises(ValueError):self.check()
    def test_empty_shards(self):
        self.mutate_manifest(lambda m:m.update(files=[]))
        with self.assertRaises(ValueError):self.check()
    def test_duplicate_shards(self):
        self.mutate_manifest(lambda m:m['files'].append(m['files'][0]))
        with self.assertRaises(ValueError):self.check()
    def test_missing_shard(self):
        self.mutate_manifest(lambda m:m['files'][0].update(name='missing.safetensors'))
        with self.assertRaises(FileNotFoundError):self.check()
    def test_shard_size(self):
        self.mutate_manifest(lambda m:m['files'][0].update(bytes=2))
        with self.assertRaises(ValueError):self.check()
    def test_shard_hash(self):
        self.mutate_manifest(lambda m:m['files'][0].update(sha256='a'*64))
        with self.assertRaises(ValueError):self.check()
    def test_unsafe_shard(self):
        self.mutate_manifest(lambda m:m['files'][0].update(name='../bad.safetensors'))
        with self.assertRaises(ValueError):self.check()
    def test_shard_tensor_count(self):
        self.mutate_manifest(lambda m:m['files'][0].update(tensors=2))
        with self.assertRaises(ValueError):self.check()
    def test_total_tensor_count(self):
        self.mutate_manifest(lambda m:m.update(tensor_count=2))
        with self.assertRaises(ValueError):self.check()
    def test_native_inventory(self):
        p=self.base/'model.safetensors';raw=p.read_bytes().replace(b'model.weight',b'other.weight');p.write_bytes(raw)
        with self.assertRaises(ValueError):self.check()
    def test_header_bound(self):
        p=self.root/'bad.safetensors';p.write_bytes(struct.pack('<Q',2**40))
        with self.assertRaises(ValueError):E.headers(p)
    def test_routed_missing_receipt(self):
        with self.assertRaisesRegex(ValueError,'receipt'):self.check(scope='routed')
    def test_header_only_not_verified(self):self.assertEqual(self.check(header_only=True)['status'],'HEADER_ONLY_NOT_VERIFIED')

class DecisionTests(unittest.TestCase):
    def setUp(self):self.a=simple_rows();self.b=simple_rows()
    def test_identical_bootstrap_zero(self):self.assertEqual(D.paired(self.a,self.b)['ci95_pp'],[0.,0.])
    def test_whole_physical_rooms(self):
        # Ten copies in room A and one in B must yield room, not item, uncertainty.
        a=simple_rows(n=11);b=copy.deepcopy(a)
        for i,r in enumerate(a):r['room']='A' if i<10 else 'B';b[i]['room']=r['room'];b[i]['scores']['released_answer']=0 if i<10 else 1
        got=D.paired(a,b);self.assertEqual(got['rooms'],2);self.assertEqual(got['ci95_pp'],[0.,100.])
    def test_missing_pair_refuses(self):
        with self.assertRaises(ValueError):D.paired(self.a,self.b[:-1])
    def test_duplicate_pair_refuses(self):
        with self.assertRaises(ValueError):D.paired(self.a+[self.a[0]],self.b)
    def test_wrong_room_refuses(self):
        self.b[0]['room']='wrong'
        with self.assertRaises(ValueError):D.paired(self.a,self.b)
    def test_missing_label_refuses(self):
        self.a[0]['scores']['released_answer']=None
        with self.assertRaises(ValueError):D.paired(self.a,self.b)
    def test_nan_refuses(self):
        self.a[0]['scores']['answer']=float('nan')
        with self.assertRaises(ValueError):D.paired(self.a,self.b)
    def test_m100_regression_stops(self):
        a=simple_rows(0);r=D.direct_rules(a,self.b,self.b)
        self.assertTrue(r['m100_reversal'].startswith('STOP'));self.assertTrue(r['R3'].startswith('FAIL'))
    def test_route_own_labels_separate_and_stops(self):
        ra=simple_rows(0,typ='route_planning',stratum='missing_released');rb=simple_rows(1,typ='route_planning',stratum='missing_released')
        for r in ra+rb:r['key']='route'+r['key'];r['scores']['released_answer']=None
        got=D.direct_rules(self.a+ra,self.b+rb,self.b+rb)
        self.assertEqual(got['leg_minus_f17']['primary']['overall']['delta_pp'],0)
        self.assertIn('route_planning',got['m100_reversal'])
    def test_cap_one_per_hundred_passes(self):
        self.a[0]['capped']=True
        r=D.direct_rules(self.a,self.b,self.b,(self.a,self.b));self.assertEqual(r['R3'],'PASS')
    def test_cap_two_per_hundred_fails(self):
        self.a[0]['capped']=self.a[1]['capped']=True
        self.assertTrue(D.direct_rules(self.a,self.b,self.b)['R3'].startswith('FAIL'))
    def test_missing_dev858_cannot_pass_r3(self):self.assertTrue(D.direct_rules(self.a,self.b,self.b)['R3'].startswith('INCOMPLETE'))
    def test_dev858_regression_trips_r3(self):self.assertTrue(D.direct_rules(self.a,self.b,self.b,(simple_rows(0),self.b))['R3'].startswith('FAIL'))
    def test_dev858_cap_trips_r3(self):
        a=copy.deepcopy(self.a);a[0]['capped']=a[1]['capped']=True
        self.assertTrue(D.direct_rules(self.a,self.b,self.b,(a,self.b))['R3'].startswith('FAIL'))

class RoutedDecisionTests(unittest.TestCase):
    def setUp(self):
        self.arms={a:simple_rows() for a in routed.ARMS};self.table={'object_abs_distance':'route'}
        for r in self.arms['forced_direct']:r['scores']['released_answer']=r['scores']['answer']=0;r['called']=False
    def report(self,**kw):return D.routed_rules(self.arms,self.table,**kw)['per_type']['object_abs_distance']
    def test_all_rules_pass(self):
        r=self.report();self.assertEqual(r['R1'],'PASS');self.assertEqual(r['R1b'],'PASS');self.assertTrue(r['R2'].startswith('PASS'))
    def test_r1_score_deficit(self):
        for r in self.arms['forced_route']:r['scores']['released_answer']=r['scores']['answer']=.9
        self.assertTrue(self.report()['R1'].startswith('FAIL'))
    def test_r1_absolute_five_point_band(self):
        for r in self.arms['scripted']:r['scores']['released_answer']=r['scores']['answer']=.9
        self.assertTrue(self.report()['R1'].startswith('FAIL'))
    def test_r1_call_rate(self):
        for r in self.arms['forced_route'][:6]:r['called']=False
        self.assertTrue(self.report()['R1'].startswith('FAIL'))
    def test_r1_call_error(self):
        self.arms['forced_route'][0]['call_errors']=1;self.assertTrue(self.report()['R1'].startswith('FAIL'))
    def test_r1_version_error(self):
        self.arms['forced_route'][0]['version_errors']=1;self.assertTrue(self.report()['R1'].startswith('FAIL'))
    def test_r1b_path(self):
        for r in self.arms['unflagged'][:6]:r['called']=False
        self.assertTrue(self.report()['R1b'].startswith('FAIL'))
    def test_r1b_score(self):
        for r in self.arms['unflagged']:r['scores']['released_answer']=r['scores']['answer']=.97
        self.assertTrue(self.report()['R1b'].startswith('FAIL'))
    def test_r2_negative_moves_to_direct(self):
        for r in self.arms['forced_route']:r['scores']['released_answer']=r['scores']['answer']=0
        for r in self.arms['forced_direct']:r['scores']['released_answer']=r['scores']['answer']=1
        self.assertIn('move this type to direct',self.report()['R2'])
    def test_r2_zero_keeps_table(self):
        for r in self.arms['forced_direct']:r['scores']['released_answer']=r['scores']['answer']=1
        self.assertTrue(self.report()['R2'].startswith('INCONCLUSIVE'))
    def test_m200_persistent_r1_stops(self):
        self.arms['forced_route'][0]['call_errors']=1
        self.assertTrue(self.report(step=200,raised=['object_abs_distance'])['R1'].startswith('STOP'))
    def test_perception_mismatch_refuses(self):
        self.arms['scripted'][0]['perception_identity']='other'
        with self.assertRaises(ValueError):self.report()
    def test_missing_arm_refuses(self):
        self.arms.pop('scripted')
        with self.assertRaises(ValueError):self.report()
    def test_partial_type_coverage_is_incomplete(self):
        self.table['relative_count']='route';self.assertTrue(D.routed_rules(self.arms,self.table)['completeness'].startswith('INCOMPLETE'))

class NativeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        install_tree()
        import torch
        torch.set_num_threads(1)
        from tests.test_carrier_c1_final import final_fixture,FakeTokenizer
        from types import SimpleNamespace
        cls.model,cls.batch,_=final_fixture();cls.model.eval().requires_grad_(False)
        cls.processor=SimpleNamespace(tokenizer=FakeTokenizer(),_routing_tokens={'ids':{'<depth_at':40,'<move':45,'<turn':47}})
    def generate(self,tokens,**kw):
        import torch
        from evalpath.runtime import generate
        it=iter(tokens)
        def tap(ids,logits):
            out=torch.full_like(logits,-float('inf'));out[:,next(it)]=0;return out
        return generate(self.model,self.processor,self.batch,'routed',tap=tap,**kw)
    def test_native_random_model_own_heads_and_replay(self):
        from student_pilot.carrier_c1_decode import replay
        r=self.generate([40,41,45,46,1]);self.assertEqual(len(r['calls']),2)
        self.assertTrue(replay(r)['byte_equal']);self.assertEqual(r['errors'],0)
        dump(ROOT/'out/NATIVE_CPU_SMOKE.json',dict(scope='tiny random Qwen3.5 + actual own pose/depth heads; controlled token choices',
            model_function_replacements=0,learned_accuracy=False,full_MDG_G3T_loader=False,decode=r))
    def test_native_direct_eos(self):self.assertEqual(self.generate([1])['calls'],[])
    def test_native_refuses_low_cap(self):
        with self.assertRaisesRegex(ValueError,'16384'):self.generate([1],max_new_tokens=2048)
    def test_native_refuses_mask_without_backend(self):
        with self.assertRaisesRegex(ValueError,'matching_backend'):self.generate([1],mask_source='mdg')
    def test_native_refuses_training_mode(self):
        self.model.train()
        try:
            with self.assertRaisesRegex(ValueError,'eval mode'):self.generate([1])
        finally:self.model.eval()
    def test_native_refuses_own_pose_with_tower(self):
        from student_pilot.carrier_c1_decode import HeadState
        with self.assertRaisesRegex(ValueError,'tower_state'):HeadState(self.model,self.batch,None,tower_state=object())
    def test_all_600_references_validate(self):
        from student_pilot.scripted_calls import validate_reference
        refs=load(ROOT/'out/SCRIPTED_REFERENCES.json');self.assertEqual(len(refs),600)
        for ref in refs.values():validate_reference(ref)
    def test_script_rejects_hidden_answer(self):
        from student_pilot.scripted_calls import validate_reference
        ref=copy.deepcopy(next(iter(load(ROOT/'out/SCRIPTED_REFERENCES.json').values())))
        ref['segments'][0]['text']='<think>\n</think>\nA'+ref['segments'][0]['call']
        with self.assertRaises(ValueError):validate_reference(ref)
    def test_script_rejects_unsupported_count(self):
        from student_pilot.scripted_calls import validate_reference
        ref=copy.deepcopy(next(iter(load(ROOT/'out/SCRIPTED_REFERENCES.json').values())))
        ref['segments'][-1]=dict(call='<count obj="chair">',text='<count obj="chair">')
        with self.assertRaises(ValueError):validate_reference(ref)
    def test_grounding_missing_configured_geometry(self):
        from student_pilot.s1_grounding import build_backend
        row=dict(question_type='object_abs_distance',student_input=dict(question='chair and table',options=[]))
        with self.assertRaisesRegex(ValueError,'unavailable'):build_backend(row,dict(frame_indices=list(range(32)),video_sha256='a'*64),dict(sha256='b'*64),fresh('ground'),dict(allow_own_fallback=False))
    def test_grounding_invalid_frame_map(self):
        from student_pilot.s1_grounding import build_backend
        row=dict(question_type='object_abs_distance',student_input=dict(question='chair',options=[]))
        with self.assertRaises(ValueError):build_backend(row,dict(frame_indices=[0]*32,video_sha256='a'*64),dict(sha256='b'*64),fresh('ground'))
    def test_evaluator_refuses_missing_group_contract(self):
        from evalpath.runtime import check_init_spec
        p=fresh('groups')/'artifact.json';dump(p,dict(schema='carrier-c1-artifact-v1',trace_program_version='3.14'))
        with self.assertRaises(ValueError):check_init_spec(dict(depth_enabled=True),pin(p))

class BindingTests(unittest.TestCase):
    def direct_cfg(self):
        cfg=load(ROOT/'work/bound_cells_final/m100_main/request.json')
        cfg['legs1']['wrapper_sha256']=sha(ROOT/'out/direct.py')
        cfg['legs1']['wrapper_dependencies']={str(p.relative_to(ROOT)):sha(p) for p in (ROOT/'out/common.py',ROOT/'out/export_check.py')}
        return cfg
    def test_direct_identity(self):self.assertEqual(direct.validate_identity(self.direct_cfg())['step'],100)
    def test_wrong_checkpoint_identity(self):
        c=self.direct_cfg();c['models']['cp1m200']['sha256']='b'*64
        with self.assertRaises(ValueError):direct.validate_identity(c)
    def test_changed_wrapper_identity(self):
        c=self.direct_cfg();c['legs1']['wrapper_sha256']='b'*64
        with self.assertRaises(ValueError):direct.validate_identity(c)
    def test_wrong_decision_arm(self):
        c=self.direct_cfg();c['legs1']['decision_arm']='B4096'
        with self.assertRaises(ValueError):direct.validate_identity(c)
    def test_dry_direct_launch_refuses_before_gpu_import(self):
        from types import SimpleNamespace
        with self.assertRaises(ValueError):direct.launch(SimpleNamespace(dest=str(ROOT/'work/bound_cells_final/m100_main'),attempt='never'))
    def test_base_pin_refuses(self):
        m=self.direct_cfg()['models'];m['base']['manifest']['sha256']='a'*64
        with self.assertRaises(ValueError):direct.model_specs(m,'cp1m200')
    def test_zero_checkpoint_refuses(self):
        m=self.direct_cfg()['models'];m['cp1m200']['sha256']='0'*64
        with self.assertRaises(ValueError):direct.model_specs(m,'cp1m200')
    def test_shared_path_refuses(self):
        with self.assertRaises(ValueError):local('/data3/forbidden')
        with self.assertRaises(ValueError):local('/home/forbidden')
    def test_route_frame_identity_excludes_labels(self):
        t=rows(VENDOR/'r3/TASKS.jsonl')[0];cs={c['native']:c for c in load(VENDOR/'r3/FRAMES.json')['captures']}
        a=routed.trainer_row(t,cs[t['native']],ROOT/'work/unused')
        t['answer']='SECRET';t['released_answer']='SECRET'
        self.assertEqual(a,routed.trainer_row(t,cs[t['native']],ROOT/'work/unused'))
        self.assertNotIn('SECRET',json.dumps(a))

class TrainedGroupTests(unittest.TestCase):
    def setUp(self):
        install_tree();import torch
        from student_pilot import trained_groups as groups
        self.g=groups;self.torch=torch
        self.m=torch.nn.Module();self.m.auxiliary_heads=torch.nn.ModuleDict({
            'pose':torch.nn.ModuleDict({'body':torch.nn.Linear(2,2),'cam_token_connector':torch.nn.Linear(2,2)}),
            'depth':torch.nn.Linear(2,2),'mdg':torch.nn.Linear(2,2)})
        groups.capture(self.m);self.initial={k:v.clone() for k,v in self.m.auxiliary_heads.state_dict().items()}
        sum(p.square().sum() for p in self.m.parameters()).backward();groups.observe(self.m)
        with torch.no_grad():
            for p in self.m.parameters():p.add_(.01)
        self.state=self.m.auxiliary_heads.state_dict();self.contract=groups.publish(self.m,self.m.state_dict(),100)
    def test_complete_warm_contract(self):self.assertEqual(self.g.validate(self.m,self.state,self.contract,100),['camera_connector','depth','grounding','pose'])
    def test_every_missing_group(self):
        for name,e in self.contract['groups'].items():
            with self.subTest(group=name):
                state=dict(self.state);state.pop(e['names'][0])
                with self.assertRaises(ValueError):self.g.validate(self.m,state,self.contract,100)
    def test_every_zero_group(self):
        for name,e in self.contract['groups'].items():
            with self.subTest(group=name):
                state=dict(self.state);state.update({k:self.torch.zeros_like(state[k]) for k in e['names']})
                with self.assertRaises(ValueError):self.g.validate(self.m,state,self.contract,100)
    def test_every_cold_group(self):
        for name,e in self.contract['groups'].items():
            with self.subTest(group=name):
                state=dict(self.state);state.update({k:self.initial[k] for k in e['names']})
                with self.assertRaises(ValueError):self.g.validate(self.m,state,self.contract,100)
    def test_missing_gradient_evidence(self):
        c=copy.deepcopy(self.contract);c['groups']['grounding']['gradient_steps']=0
        with self.assertRaises(ValueError):self.g.validate(self.m,self.state,c,100)
    def test_init_spec_missing_each_group(self):
        from evalpath.runtime import check_init_spec,evaluator_init_spec
        p=fresh('groups')/'artifact.json';dump(p,dict(trained_groups=self.contract,mdg=dict(tau=.25),trace_program_version='3.14'))
        receipt=dict(depth_enabled=True,geometry_online={'mode':'predicted'},mdg={'present':True},trace_program_version='3.14')
        spec=evaluator_init_spec(receipt,pin(p));self.assertEqual(check_init_spec(receipt,pin(p)),spec)
        for name in spec['groups']:
            changed={**spec,'groups':[x for x in spec['groups'] if x!=name]}
            with self.subTest(group=name),self.assertRaises(ValueError):check_init_spec(receipt,pin(p),changed)

class LedgerTests(unittest.TestCase):
    def fixture(self,delta):
        types=['object_counting','object_abs_distance','object_size_estimation','room_size_estimation',
               'object_rel_distance','obj_appearance_order','route_planning',
               'object_rel_direction_easy','object_rel_direction_medium','object_rel_direction_hard']
        a=[];b=[]
        for t in types:
            for i in range(20):
                r=simple_rows(.5+delta,n=1,typ=t)[0];r.update(key=t+str(i),room=str(i));a.append(r)
                r=copy.deepcopy(r);r['scores']['released_answer']=.5;b.append(r)
        return a,b
    def test_ledger_lower_rejection(self):self.assertEqual(D.official_ledger(*self.fixture(-.03),require_full=False)['verdict'],'REJECT ledger')
    def test_ledger_upper_rejection(self):self.assertEqual(D.official_ledger(*self.fixture(.03),require_full=False)['verdict'],'REJECT ledger')
    def test_ledger_inside_band(self):self.assertEqual(D.official_ledger(*self.fixture(.01),require_full=False)['verdict'],'Ledger not rejected')
    def test_partial_official_refuses(self):
        with self.assertRaises(ValueError):D.official_ledger(*self.fixture(.01))
    def test_macro_not_item_weighted(self):
        a,b=self.fixture(0)
        for r in a:
            if r['question_type']=='object_rel_direction_easy':r['scores']['released_answer']=.8
        self.assertAlmostEqual(D.official_ledger(a,b,require_full=False)['delta_pp'],1.25)

class GeometryTests(unittest.TestCase):
    def setUp(self):
        install_tree();import geometry;import numpy as np
        from student_pilot.tower_read import TowerState
        self.g=geometry;self.np=np
        raw=np.zeros((32,9));raw[:,6]=1;raw[:,7:]=1.2;raw[:,0]=np.arange(32)*.1
        self.state=TowerState(raw,np.full((32,51,51),2.),np.linspace(0,1,32*51*51).reshape(32,51,51),np.arange(32),np.arange(32))
    def test_scale_once_native_loader(self):
        p=fresh('geom')/'geometry.npz';r=self.g.convert(self.state,self.np.full((32,51,51),4.),[0,-1,0],[480,640],p)
        self.assertAlmostEqual(r['scale'],2.);self.assertEqual(r['depth_scale_count'],1)
        from student_pilot.ground_profiles import load_geometry
        from student_pilot.scene_state import FrameMap
        g=load_geometry(p,FrameMap(tuple(range(32))),'tower_scaled')
        self.assertAlmostEqual(g.depth(1,self.np.array([[500.,500.]]))[0],4.)
    def test_bad_own_depth(self):
        with self.assertRaises(ValueError):self.g.convert(self.state,self.np.zeros((32,51,51)),[0,-1,0],[480,640],fresh('geom')/'bad.npz')
    def test_bad_gravity(self):
        with self.assertRaises(ValueError):self.g.convert(self.state,self.np.ones((32,51,51)),[0,0,0],[480,640],fresh('geom')/'bad.npz')
    def test_bad_raster(self):
        with self.assertRaises(ValueError):self.g.convert(self.state,self.np.ones((32,51,51)),[0,-1,0],[0,640],fresh('geom')/'bad.npz')
    def test_parent_geometry_refused(self):
        with self.assertRaisesRegex(ValueError,'exact LEG'):self.g.validate_manifest(dict(schema='s1-predicted-geometry-v1',videos={'x':{}}),dict(sha256='a'*64))
    def test_wrong_geometry_producer(self):
        a=dict(sha256='a'*64)
        with self.assertRaises(ValueError):self.g.validate_manifest(dict(schema='s1-predicted-geometry-v1',checkpoint=a,videos={'x':{}}),a)
    def test_valid_dense_anchors(self):
        c=dict(group='g3s32',anchor_indices=list(range(32)));e=dict(frames=[dict(index=i) for i in range(32)],anchor_slots=list(range(32)))
        self.assertEqual(self.g.validate_dense(c,e)[0],list(range(32)))
    def test_dense_anchor_mismatch(self):
        c=dict(group='g3s32',anchor_indices=list(range(1,33)));e=dict(frames=[dict(index=i) for i in range(32)],anchor_slots=list(range(32)))
        with self.assertRaises(ValueError):self.g.validate_dense(c,e)
    def test_dense_too_few(self):
        with self.assertRaises(ValueError):self.g.validate_dense(dict(group='g3s64'),dict(frames=[dict(index=i) for i in range(32)],anchor_slots=list(range(32))))
    def test_tower_cpu_refuses(self):
        from types import SimpleNamespace
        with self.assertRaises(ValueError):self.g.tower(SimpleNamespace(device='cpu'))
    def test_real_checkpoint_cpu_refuses(self):
        from types import SimpleNamespace
        with self.assertRaises(ValueError):self.g.prepare(SimpleNamespace(device='cpu'))

class NativeScoreTests(unittest.TestCase):
    def test_parsed_cap_credit(self):
        task=dict(question_type='object_rel_direction_easy',options=['A. left','B. right'])
        self.assertEqual(routed.native_score(task,'A',dict(text='reason\n</think>\nA',finish='max_new_tokens')),1.)
    def test_missing_think_zero(self):
        self.assertEqual(routed.native_score({},'A',dict(text='A',finish='eos')),0.)

class RoutedRequestTests(unittest.TestCase):
    def request(self):
        p=ROOT/'work/bound_cells_final/m100_supported600_forced_route/request.json'
        r=load(p);r['driver_sha256']=sha(ROOT/'out/routed.py');r['binding']=digest({k:v for k,v in r.items() if k!='binding'});return r
    def changed(self,key,value):
        r=self.request();r[key]=value;r['binding']=digest({k:v for k,v in r.items() if k!='binding'});return r
    def test_good_dry_request(self):self.assertEqual(len(routed.validate_request(self.request())['keys']),600)
    def test_dry_live_refuses(self):
        with self.assertRaises(ValueError):routed.validate_request(self.request(),live=True)
    def test_bad_masks(self):
        with self.assertRaises(ValueError):routed.validate_request(self.changed('mask_source','gt'))
    def test_bad_fusion(self):
        with self.assertRaises(ValueError):routed.validate_request(self.changed('fusion_policy','other'))
    def test_bad_flag(self):
        with self.assertRaises(ValueError):routed.validate_request(self.changed('prompt_flag','other'))
    def test_small_cap(self):
        with self.assertRaises(ValueError):routed.validate_request(self.changed('max_new_tokens',2048))
    def test_bad_layout(self):
        with self.assertRaises(ValueError):routed.validate_request(self.changed('layout','spread'))
    def test_unbound_export(self):
        r=self.request();r['artifact']['sha256']='0'*64;r['binding']=digest({k:v for k,v in r.items() if k!='binding'})
        with self.assertRaises(ValueError):routed.validate_request(r)
    def test_binding_tamper(self):
        r=self.request();r['step']=200
        with self.assertRaises(ValueError):routed.validate_request(r)
    def test_geometry_fallback(self):
        r=self.request();r['grounding']['allow_own_fallback']=True;r['binding']=digest({k:v for k,v in r.items() if k!='binding'})
        with self.assertRaises(ValueError):routed.validate_request(r)
    def test_scripted_full_scope_refuses(self):
        from types import SimpleNamespace
        with self.assertRaisesRegex(ValueError,'does not support'):routed.bind(SimpleNamespace(dest=str(fresh('bind')/'new'),scope='main1525',arm='scripted'))

class ReceiveTests(unittest.TestCase):
    def archive(self,name='artifact.json',link=False):
        import io,tarfile
        root=fresh('receive');p=root/'export.tar'
        with tarfile.open(p,'w') as t:
            m=tarfile.TarInfo(name);m.size=2
            if link:m.type=tarfile.SYMTYPE;m.linkname='/elsewhere';m.size=0
            t.addfile(m,None if link else io.BytesIO(b'{}'))
        return root,p
    def test_archive_receive(self):
        import receive
        root,p=self.archive();self.assertEqual(receive.receive(p,sha(p),root/'dest')['members'],1)
        self.assertEqual((root/'dest/artifact.json').read_text(),'{}')
    def test_archive_digest(self):
        import receive
        root,p=self.archive()
        with self.assertRaises(ValueError):receive.receive(p,'a'*64,root/'dest')
    def test_archive_parent_path(self):
        import receive
        root,p=self.archive('../escape')
        with self.assertRaises(ValueError):receive.receive(p,sha(p),root/'dest')
    def test_archive_absolute_path(self):
        import receive
        root,p=self.archive('/escape')
        with self.assertRaises(ValueError):receive.receive(p,sha(p),root/'dest')
    def test_archive_links(self):
        import receive
        root,p=self.archive(link=True)
        with self.assertRaises(ValueError):receive.receive(p,sha(p),root/'dest')
    def test_archive_existing_destination(self):
        import receive
        root,p=self.archive()
        with self.assertRaises(ValueError):receive.receive(p,sha(p),root)

if __name__=='__main__':
    unittest.main(verbosity=2)
