import ast
import copy
import dataclasses
import json
import re
from pathlib import Path
from types import SimpleNamespace as NS
import numpy as np
import pytest
from fixtures_contracts import L, fixture, rotations, session, response, CALLS
from trace_format.contracts import contract_epoch, response_status, heading_available


def test_review_ground_responses_and_recovery():
    from student_pilot.training_contract import audit_training_contract
    from test_contracts import row_case
    row=row_case('clean')
    row['events']=[dict(call='<ground obj="chair" mode="box">', response='chair: heading unavailable\nsize 0.43 x 0.06 x 0.86 m'),
                   dict(call='<gap a="chair" b="table" rule="box_grid_5cm">',response='distance 0.90 m')]
    assert response_status(row['events'][0]['response'])=='ok'
    assert audit_training_contract([row])==[None]
    for text in ('chair: frames 2,3 (best 2)\nP1: cam2 (1.00, 2.00, 3.00) m; f1 (1.00, 2.00, 3.00) m; spread 0.10\nsize unavailable',
                 'chair: frames 2,3 (best 2)\nsize unavailable'):
        assert response_status(text)=='ok'
    for status in ('not seen','unresolved','box unavailable','error: malformed_call'):
        row['events'][0]['response']='chair: '+status
        assert audit_training_contract([row])==['contract_call_after_failed_ground']
    row['events']=row['events'][:1]
    assert audit_training_contract([row])==[None]


@pytest.mark.parametrize('damage',[None, [], 'text', 9, {'routing':None}, {'routing':[]},
    {'events':[None]}, {'events':[{'kind':None}]}, {'events':[{'kind':'ground_call','token':None}]},
    {'events':[{'call':None,'response':'not seen'}]}, {'events':{}}, {'events':[{'call':'x','response':'ok'}],'student_input':None}])
def test_malformed_rows_defer(damage):
    from student_pilot.training_contract import audit_training_contract
    assert audit_training_contract([damage])==['contract_malformed_row']


def test_model_errors_use_runtime_text():
    from student_pilot.carrier_c1_decode import respond
    from trace_format.calculator import PrintedPointRegistry
    from student_pilot.training_contract import audit_training_contract, OPERATOR_FAULTS, RUNTIME_ONLY_FAULTS
    from test_contracts import row_case
    row=row_case('clean');call='<ground nonsense>'
    text, info=respond(call,PrintedPointRegistry(),None)
    assert text.startswith('error:') and info['kind']=='error'
    row['events']=[dict(call=call,response=text)]
    assert audit_training_contract([row])==[None]
    for code in OPERATOR_FAULTS+RUNTIME_ONLY_FAULTS:
        row['events'][0]['response']='error: '+code
        assert audit_training_contract([row])==['contract_operator_fault']


def test_cache_binding_separate_reads(tmp_path):
    from student_pilot.training_contract import audit_training_contract, admission_phrases
    from student_pilot.s1_grounding import build_backend
    from student_pilot.ground_v3 import GroundV3
    from student_pilot.ground_sources import MaskProvider
    from student_pilot.routed_features import select_instances
    from student_pilot.scene_state import SceneState
    from test_contracts import row_case
    row=row_case('cache');row['mask_source']='cached_sam3';row.pop('candidate_phrases')
    assert audit_training_contract([row])==['contract_manifest_missing']
    a=tmp_path/'admission.json';b=tmp_path/'runtime.json'
    for p in (a,b):p.write_text(json.dumps({'phrases':['table','couches']}))
    row['candidate_manifest']=json.loads(a.read_text())
    runtime=json.loads(b.read_text())
    assert audit_training_contract([row])==['contract_operand_outside_candidates']
    inputs=dict(question=row['question'],options=[])
    runtime_row={k:v for k,v in row.items() if k!='candidate_manifest'}
    backend=build_backend(dict(runtime_row,student_input=inputs,question_type='object_abs_distance'),
        dict(frame_indices=list(range(32)),video_sha256='a'*64,cache_phrases=runtime['phrases']),dict(sha256='b'*64),tmp_path/'backend')
    assert backend.config['candidate_universe']==['couch','table']
    backend.geometry_error=None
    with pytest.raises(ValueError,match='fixed named candidate universe'):
        select_instances(backend,'chair',None)
    geo=fixture()[1]()
    source=MaskProvider(lambda name:None,'cache-fixture',names=['chair'])
    source.cache=runtime
    direct=GroundV3(SceneState('a'*64,geo.frame_map,geo.identity),geo,source,mask_source='mdg',audit_dir=tmp_path/'direct')
    assert direct.config['candidate_universe']==list(admission_phrases('',[],json.loads(a.read_text())['phrases']))==['couch','table']


def test_normalizer_exceptions_and_duplicate_merge(tmp_path):
    from student_pilot.phrases import normalize_phrase, annotation_labels, cache_key
    from student_pilot.s1_grounding import build_backend
    pairs={'glasses':'glass','mattresses':'mattress','buses':'bus','knives':'knife','lens':'lens',
           'lenses':'lens','shelves':'shelf','bookshelves':'bookshelf','cases':'case','houses':'house',
           'vases':'vase','curves':'curve','nerves':'nerve','series':'series','chairs':'chair','batteries':'battery'}
    for raw,expected in pairs.items():
        assert normalize_phrase(raw)==expected
        assert annotation_labels(raw,[expected,'unrelated'],lambda *args:[])==[expected]
    cache={'phrases':['chairs','chair'],'frames':{'0':{'phrases':{
        'chairs':{'presence':.7,'instances':[{'score':.8,'mask':'a'}]},
        'chair':{'presence':.8,'instances':[{'score':.9,'mask':'b'}]}}}}}
    other=copy.deepcopy(cache);other['phrases'].reverse()
    assert cache_key(cache,'chairs')==cache_key(other,'chair')=='chair'
    assert cache==other and len(cache['frames']['0']['phrases']['chair']['instances'])==2
    backend=build_backend(dict(question_type='object_abs_distance',student_input=dict(question='How far is the "chair" from the table?',options=[])),
        dict(frame_indices=list(range(32)),video_sha256='a'*64),dict(sha256='b'*64),tmp_path)
    assert backend.config['candidate_universe']==['chair','table']


def attack_helpers():
    path=Path('/scratch/jjyeung/orch_n30/review_contracts/work/mytests/attack_decode.py')
    module=ast.parse(path.read_text())
    nodes=[n for n in module.body if isinstance(n,ast.FunctionDef) and n.name in ('cam','geometry')]
    from scipy.spatial.transform import Rotation
    from student_pilot.carrier_c1_routing import OwnGeometry
    ns=dict(np=np,Rot=Rotation,OwnGeometry=OwnGeometry,BASE=np.array([[1.,0,0],[0,0,1],[0,-1,0]]))
    exec(compile(ast.Module(body=nodes,type_ignores=[]),str(path),'exec'),ns)
    return ns['cam'],ns['geometry']


def test_decode_attacks_and_move_source_distance():
    from student_pilot.carrier_c1_decode import respond
    from trace_format.calculator import PrintedPointRegistry
    cam,geometry=attack_helpers();records={}
    centres=np.array([[.1*k, .05*k*k%1, 1.5] for k in range(32)])
    for case in ('A','B','later31'):
        angles=[cam(0,0,20*k) for k in range(32)]
        degenerate={'A':0,'B':1,'later31':30}[case];angles[degenerate]=cam(-87 if case=='later31' else -88)
        values=[]
        for noise in (None,(3,0),(3,90),(3,180),(3,270)):
            geo=geometry(angles,centres,noise)
            i=31 if case=='later31' else 2;j=3
            calls=[f'<move from={i} to={j}>',f'<turn from={i} to={j}>',f'<pose frame={i}>','<depth_at frame=2 pts=[[500,500]]>']
            texts=[respond(c,PrintedPointRegistry(),geo)[0] for c in calls]
            if case=='A':
                assert all('heading unavailable' not in t for t in texts[:2])
                assert 'f1 centre (heading unavailable,' in texts[2]
                assert 'f1 (heading unavailable,' in texts[3]
            else:
                assert f'dx = heading unavailable (frame {i})' in texts[0]
                assert f'dz = heading unavailable (frame {i})' in texts[0]
                assert 'turn = heading unavailable' in texts[1]
                assert 'f1 centre (heading unavailable,' in texts[2]
                assert 'f1 (heading unavailable,' not in texts[3]
            expected=f'{np.linalg.norm(centres[j-1]-centres[i-1]):.2f}'
            assert f'distance = {expected} m' in texts[0]
            # Gravity noise physically changes the gravity projection (dy and depth height).
            # Compare every served field against the same noisy geometry with only policy disabled.
            with contract_epoch(False):
                baseline=[respond(c,PrintedPointRegistry(),geo)[0] for c in calls]
            if case=='A':assert texts[:2]==baseline[:2]
            else:
                from student_pilot.carrier_c1_routing import s2
                expected_dy=s2(-geo.down @ (geo.camera(j)[1]-geo.camera(i)[1]))+' m'
                assert re.search(r'dy = ([^,]+)',texts[0])[1]==expected_dy
                assert texts[3]==baseline[3]
            values.append(dict(noise=noise,calls=calls,responses=texts,defined=baseline))
        if case=='A':assert len({tuple(re.sub(r'dy = [^,]+', 'dy = gravity projection', t) for t in v['responses'][:2]) for v in values})==1
        records[case]=values
    (L/'out/DECODE_ATTACK_R3.json').write_text(json.dumps(dict(source=str(Path(__file__)),cases=records),indent=2))


@pytest.mark.parametrize('roll',[30,45,80])
@pytest.mark.parametrize('storage',['landscape','portrait'])
def test_genuine_rolled_capture(roll,storage,tmp_path):
    from student_pilot.geometry_profiles import ProfileGeometry
    c,make=fixture(storage);C=c.camera_to_world.copy();C[:,:3,:3]=rotations(0,roll)
    geo=ProfileGeometry(dataclasses.replace(c,camera_to_world=C),make().depth_grid)
    assert heading_available(geo)
    s=session(geo,tmp_path)
    texts=[response(s,call) for call in CALLS]
    assert texts[2].startswith('distance ') and texts[3].startswith('distance ')
    assert all('heading unavailable' not in t and not t.startswith('error:') for t in texts)


def test_classes_remain_classes():
    from generator.derivgen_v7.derivgen import ground_v313 as G, box_v313 as B
    from trace_format import box_v313 as RB
    for enabled in (False,True):
        with contract_epoch(enabled):
            for cls in (G.Session,G.GTInstances,B.BoxRegistry,B.FittedBoxProvider,B.FusedBoxProvider):
                assert isinstance(cls,type)
            registry=B.BoxRegistry()
            if enabled:assert isinstance(registry,RB.BoxRegistry)
            else:assert not isinstance(registry,RB.BoxRegistry)
            class Provider(G.GTInstances):
                def labels_for(self,name):return {'custom'}
            p=Provider(NS())
            assert isinstance(p,Provider) and p.labels_for('chair')=={'custom'}


def test_camera_gap_uses_named_frame():
    from trace_format.box_v313 import camera_centre_f1
    geo=fixture('nadir_positive')[1]()
    for k in (2,5,31):
        np.testing.assert_array_equal(camera_centre_f1(geo,k),geo.cam(k)[1])
        assert not np.array_equal(camera_centre_f1(geo,k),geo.cam(1)[1])


def test_training_head_substitution_depth():
    from fixtures_contracts import own_geometry
    from student_pilot.carrier_c1_routing import rerender
    from student_pilot.carrier_c1_decode import respond
    from trace_format.calculator import PrintedPointRegistry
    geo=own_geometry(fixture('nadir_positive')[1]())
    call='<depth_at frame=2 pts=[[500,500]]>'
    events=[dict(kind='tool_call',token=call,name='depth_at',call_id='d',arguments=dict(frame=2,pts=[[500,500]])),
        dict(kind='tool_response',call_id='d',name='depth_at',points=[dict(label='P1',requested_frame=2,actual_frame=2)])]
    expected=respond(call,PrintedPointRegistry(),geo)[0]
    assert 'heading unavailable' in expected
    text,spans,_=rerender(dict(events=events,answer='1',trace_revision='3.14'),geo)
    assert expected in text and len(spans)==1


def test_served_point_without_size_admits_following_grounds(tmp_path):
    from student_pilot.training_contract import audit_training_contract
    s=session(fixture()[1](),tmp_path,names=('chair','table','lamp'))
    events=[]
    for name in ('chair','table','lamp'):
        call=f'<ground obj="{name}">';text=response(s,call)
        assert text.startswith(name+': frames')
        if name=='chair':
            text=re.sub(r'(?m)^size .*$', 'size unavailable', text)
            assert text.endswith('size unavailable') and 'P1:' in text
        events.append(dict(call=call,response=text))
    row=dict(qid='served-point',events=events,candidate_phrases=['chair','table','lamp'],
        question='How far is the chair from the table?',options=[])
    assert audit_training_contract([row])==[None]


def test_backend_manifest_binding_and_missing(tmp_path):
    from student_pilot.s1_grounding import build_backend
    row=dict(question_type='object_abs_distance',mask_source='cached_sam3',
        student_input=dict(question='How far is the chair from the table?',options=[]))
    batch=dict(frame_indices=list(range(32)),video_sha256='a'*64)
    with pytest.raises(ValueError,match='contract_manifest_missing'):
        build_backend(row,batch,dict(sha256='b'*64),tmp_path/'missing')
    row['candidate_manifest']={'phrases':['chairs','table','lamp']}
    backend=build_backend(row,batch,dict(sha256='b'*64),tmp_path/'bound')
    assert backend.config['candidate_universe']==['chair','lamp','table']


def test_empty_wrapper_and_cache_alias_without_frames():
    from student_pilot.phrases import cache_key
    assert response_status('<tool_response></tool_response>')=='missing response'
    cache=dict(phrases=['chair','chairs'],frames={'0':{'phrases':{}}})
    assert cache_key(cache,'chair')=='chair' and cache['phrases']==['chair']
