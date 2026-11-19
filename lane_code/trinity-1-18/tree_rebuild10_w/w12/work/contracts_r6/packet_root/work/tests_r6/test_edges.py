import copy
import json
from types import SimpleNamespace as NS
import numpy as np
import pytest
from fixtures_contracts import fixture,session,response,CALLS,masks,L
from trace_format.contracts import contract_epoch,heading_available,response_status

def test_inherited_normalization_reference_in_replay_mode(monkeypatch):
    import ast
    from pathlib import Path
    from tests.test_sam3_tower import TowerTests
    base=L/'work/base/work/base/tree_b01ce449/student_pilot/sam3_tower.py'
    tree=ast.parse(base.read_text())
    nodes=[n for n in tree.body if (isinstance(n,ast.FunctionDef) and n.name=='normalize_phrase') or
           (isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='SINGULAR' for t in n.targets))]
    for n in nodes:
        if isinstance(n,ast.FunctionDef):n.name='phrase'
    reference=ast.unparse(ast.Module(body=nodes,type_ignores=[]))
    external=Path('/scratch/jjyeung/orch_cd/ttower/work/sam3/common.py')
    original=Path.read_text
    monkeypatch.setattr(Path,'read_text',lambda path,*a,**kw:reference if path==external else original(path,*a,**kw))
    with contract_epoch(False):
        TowerTests('test_normalization_matches_reference').test_normalization_matches_reference()

def test_private_box_audit_and_unavailable_replay(tmp_path):
    from trace_format.box_v313 import replay_audit
    for kind in ('landscape','nadir','small'):
        s=session(fixture('landscape' if kind=='small' else kind)[1](),tmp_path/kind,small=kind=='small')
        for call in CALLS[:4]:response(s,call)
        values=replay_audit(s.events)
        assert len(values)==(0 if kind=='small' else 2)
    from student_pilot.live_trace313 import AuditSession
    with pytest.raises(ValueError,match='epoch_mismatch'):
        AuditSession([dict(contract_epoch=True),dict(contract_epoch=False)])
    assert heading_available(None)
    geo=fixture('nadir')[1]()
    with contract_epoch(False):assert heading_available(geo) is True

def test_legacy_witness_keypoints_and_metric_move(tmp_path):
    from student_pilot import ground_lifting as G
    from trace_format.ground_v313 import Session
    from student_pilot.carrier_c1_decode import respond
    geo=fixture('nadir')[1]()
    with pytest.raises(ValueError,match='heading unavailable'):G.public_centres(geo,2,np.ones(3))
    s=Session(G,geo,None,instances=lambda n:[],program_version='3.13')
    s.objects={n:G.lift_object(n,masks(n).masks,np.ones(32),geo,tau=.5) for n in ('chair','table')}
    assert ' m' in s._gap('chair',['table'])
    s.keypoint_calls=True
    assert s._keypoints('surface_pair',['chair','table'])=='unavailable'
    from fixtures_contracts import own_geometry
    heads=own_geometry(geo)
    assert 'heading unavailable (frame 1)' in respond('<move from=1 to=2>',s.registry,heads)[0]

def test_generator_uses_runtime_and_renders_heading_failure(tmp_path,monkeypatch):
    from generator.derivgen_v7.derivgen import box_v313 as B,ground_v313 as G
    from trace_format import ground_v313 as runtime,box_v313 as boxes
    from student_pilot import ground_lifting as lifting
    assert isinstance(G.Session(lifting,fixture()[1](),None,instances=lambda n:[]),runtime.Session)
    # Direct text comes from an independently supplied canonical answer; this
    # test isolates the renderer's failure branch from its source join checker.
    monkeypatch.setattr(B.old,'direct_continuation',lambda item:('Locate the chair in the frames and estimate its distance visually.','2'))
    for camera in (False,True):
        s=session(fixture('nadir')[1](),tmp_path/str(camera))
        s.simulated_misses.add('chair')
        item=dict(qid='synthetic',type='camera_obj_abs_dist' if camera else 'object_abs_distance',
            roles=dict(frame=2,names=['chair']) if camera else dict(a='chair',b='table'),
            question='How far?',options=[],gt_answer='2',gt_authority='synthetic',target_distance_rule=boxes.RULE_GRID)
        row=(B.render_camera if camera else B.render)(item,s,lambda text:len(text.split()))
        assert len(row['events'])==1
        assert response_status(row['events'][0]['response'])=='not seen'
        assert '<answer>2</answer>' in row['suffix']
    with contract_epoch(False):
        assert not isinstance(G.Session(lifting,fixture()[1](),None,instances=lambda n:[]),runtime.Session)
        registry=B.BoxRegistry()
        assert registry.gap('chair',['table'])[0]=='not seen'
        assert B.cam_gap_body(registry,1,['chair'],np.zeros(3))[0]=='not seen'

def test_room_generator_missing_geometry_mode_uses_sensor_default(tmp_path):
    from generator.derivgen_v7.derivgen import room_rows_v314 as R
    from trace_format.ground_v312 import wrap
    s=session(fixture()[1](),tmp_path)
    s.geometry_mode='sensor'
    body=s.execute('<ground mode="room">')
    parsed=R.R.parse_response(body)
    bare=NS(events=[])
    def execute(call):
        bare.events.append(dict(call=call,response=wrap(body),audit=s.events[-1]['audit']))
        return body
    bare.execute=execute
    row=R.render(dict(qid='room',question=R.QUESTION,options=[],gt_authority='synthetic',gt_answer=parsed['area_m2']),bare,lambda text:len(text.split()))
    assert row['answer']==f"{parsed['area_m2']:.2f}"

def test_cache_readers_bind_raw_aliases(tmp_path):
    from student_pilot.ground_sources import CachedSAM3,native_candidates
    from student_pilot.routed_features import detections,rle
    from student_pilot.scene_state import FrameMap
    from ofs import core as O
    mask=np.zeros((24,32),bool);mask[7:18,4:12]=True
    cache=dict(phrases=['Office_Chairs'],frames={str(k):dict(phrases={'Office_Chairs':dict(presence=1.,instances=[dict(score=1.,mask=rle(mask))])}) for k in range(32)})
    def decode(r):return np.repeat(np.arange(len(r['counts']))%2,r['counts']).astype(bool).reshape(r['size'],order='F')
    reader=NS(phrase=lambda name:'incorrect',rle_decode=decode)
    source=object.__new__(CachedSAM3);source.cache=cache;source.reader=reader;source.live=None;source.frame_indices=tuple(range(32))
    assert len(source.selector_candidates('office chair'))==32
    assert np.array_equal(source.native_mask('office chair',NS(frame=1,index=0)),mask)
    frames,origin=detections(source,'office chairs',FrameMap(tuple(range(32))))
    assert origin=='sam3' and len(frames[0])==1
    geo=fixture()[1]()
    proposals,refused=source.proposals_for('office chairs',geo,O,None)
    assert proposals
    source.live=NS(proposals_for=lambda *args:('fallback',[]),selector_candidates=lambda n:['fallback'],native_mask=lambda *a:mask)
    assert source.proposals_for('unlisted',geo,O,None)[0]=='fallback'
    assert source.selector_candidates('unlisted')==['fallback']
    assert source.native_mask('unlisted',NS(frame=1,index=0)) is mask

def test_event_forms_and_manifest_failure_reasons():
    from student_pilot.training_contract import audit_training_contract,call_responses,admission_phrases
    from student_pilot.phrases import normalize_phrase,annotation_phrase,annotation_labels
    from trace_format.category_vocab import normalized
    for word,expected in [('batteries','battery'),('boxes','box'),('office chairs','office chair')]:
        assert normalize_phrase(word)==normalized(word)==expected
    for word in ('','chair\n','<chair>'):
        with pytest.raises(ValueError):normalize_phrase(word)
    assert annotation_labels('Office_Chairs',['office chair'],lambda *args:[])==['office chair']
    with contract_epoch(False):
        assert annotation_phrase('ＯＦＦＩＣＥ CHAIRS')=='office chairs'
        assert annotation_labels('chair',['chair'],lambda *args:['legacy'])==['legacy']
    with pytest.raises(ValueError,match='outside_candidates'):
        admission_phrases('q',[],['chair'],['bucket'])
    events=[dict(kind='ground_call',token='<ground obj="chair" mode="box">',call_id='a'),
            dict(kind='ground_response',text='<tool_response>chair: not seen</tool_response>',call_id='a')]
    row=dict(qid='a',events=events,target='<think>Locate visually.</think><answer>2</answer>')
    assert audit_training_contract([row],{'a':dict(phrases=['chairs'])})==[None]
    assert audit_training_contract([dict(row,target='')],{'a':['chair']})==['contract_recovery_without_answer']
    assert audit_training_contract([row],{'a':['table']})==['contract_operand_outside_candidates']
    native=[dict(kind='calculator_call',command='<dist P1 P2>'),dict(kind='calculator_response',response=dict(text='2.00 m'))]
    assert list(call_responses(dict(events=native)))==[('<dist P1 P2>','2.00 m')]
    malformed=[events[0],events[0],dict(call='x',response='x')]
    assert list(call_responses(dict(events=malformed)))[:2]==[(events[0]['token'],None)]*2

def test_annotation_admission_uses_phrase_identity(monkeypatch):
    from generator.derivgen_v7.derivgen.ground_v312_io import GTClip
    from generator.derivgen_v7.derivgen.ground_v313_distance import prepare
    from generator.derivgen_v7.derivgen import ground_v312_io as I
    clip=object.__new__(GTClip)
    raw=dict(centroid=[0,0,0],axesLengths=[1,1,1],normalizedAxes=np.eye(3).ravel())
    clip.geo=NS(labels=['office chair','table lamp'],ids=[1,2],obb={1:raw,2:raw},has=lambda k:True)
    clip.programs=NS(T=NS(match_labels=lambda *args:[]))
    clip.masks=lambda name:(np.ones((32,4,4),bool),np.ones(32))
    monkeypatch.setattr(I,'degeneracy_reasons',lambda *args:[])
    from generator.derivgen_v7.derivgen import ground_v312_degenerate as D
    monkeypatch.setattr(D,'degeneracy_reasons_multi',lambda *args:[])
    item=dict(type='object_abs_distance',roles=dict(a='Office_Chairs',b='Table_Lamps'))
    clip.validate_operands(item)
    clip.validate_operands_multi(item)
    prepare(item,clip,multi_instance=True)
    assert [x['instance_id'] for x in item['independent_ordered_boxes']]==[1,2]
    clip.cache={};clip.geo.inst=np.ones((32,10,10),int)
    assert GTClip.masks(clip,'Office_Chairs')[0].any()

def test_ground_row_recovery_validation_and_response_masking():
    from student_pilot.ground_rows import pack,validate
    from trace_format.ground_v312 import wrap
    call='<ground obj="chair" mode="box">'; body='chair: heading unavailable'
    suffix='<think>\nLocate the chair.\n'+call+'\n'+wrap(body)+'\nLocate the chair again and estimate visually.\n</think>\n<answer>2.00</answer>'
    record=dict(qid='recovery',type='object_abs_distance',question='How far?',options=[],spec_version='3.14',
        candidate_id='c',answer='2.00',answer_content='2.00',gt_answer='2',suffix=suffix,
        events=[dict(call=call,response=wrap(body))],not_seen=True,gt_agrees=True,training_admitted=False)
    row=pack(record,{})
    row['candidate_phrases']=['chair']
    target,spans=validate(row)
    assert target==suffix and len(spans)==1
    assert target[spans[0]['start']:spans[0]['end']]==wrap(body)
    row['candidate_phrases']=[]
    with pytest.raises(ValueError,match='outside_candidates'):validate(row)

def test_native_tower_cache_uses_shared_phrase():
    from student_pilot.ground_sources import TowerSAM3
    from student_pilot.routed_features import rle
    from student_pilot.scene_state import FrameMap
    mask=np.ones((4,4),bool)
    def decode(r):return np.repeat(np.arange(len(r['counts']))%2,r['counts']).astype(bool).reshape(r['size'],order='F')
    tower=NS(encode=lambda frames:frames,detect=lambda encoded,name:[NS(scores=[1.],masks=[mask],presence=1.)]*32)
    codec=NS(phrase=lambda n:'incorrect',rle_encode=rle,rle_decode=decode)
    source=TowerSAM3(tower,list(range(32)),FrameMap(tuple(range(32))),'fake-tower',codec)
    assert source._detect('Office_Chairs')['phrases']==['office chair']

def test_legacy_live_session_records_epoch(tmp_path):
    from student_pilot.live_trace313 import LiveSession
    base=session(fixture()[1](),tmp_path)
    s=LiveSession(base.owner,program_version='3.13')
    s.bind_state(NS(verify_session=None,tool_context=NS(),heads=NS(mdg_states=None)))
    assert response(s,'<ground obj="chair">').startswith('chair: frames')
    assert s.queries[-1]['contract_epoch'] is True

def test_training_head_substitution_matches_runtime():
    from student_pilot.carrier_c1_routing import rerender
    from student_pilot.carrier_c1_decode import respond
    from student_pilot.p3_printed_calculator import PrintedPointRegistry
    from fixtures_contracts import own_geometry
    geo=own_geometry(fixture('nadir_positive')[1]())
    call='<move from=1 to=2>'
    events=[dict(kind='tool_call',token=call,name='move',call_id='m',arguments={'from':1,'to':2}),
            dict(kind='tool_response',call_id='m',name='move',text='placeholder')]
    text,spans,_=rerender(dict(events=events,answer='1',trace_revision='3.14'),geo)
    expected=respond(call,PrintedPointRegistry(),geo)[0]
    assert expected in text and len(spans)==1

def test_response_metric_counts_partial_failures(tmp_path):
    from student_pilot.live_trace313 import replay
    s=session(fixture('nadir')[1](),tmp_path)
    calls=[dict(call=c,response=response(s,c)) for c in CALLS[:3]]
    result=replay(dict(heads=dict(trace_program_version='3.14',ground_queries=s.queries),calls=calls))
    assert result['byte_equal'] and result['ok_responses']==3
    assert result['response_statuses']=={'ok':3}

def test_sealed_cache_reader_dispatch(monkeypatch):
    import sys
    from ofs import core
    codec=NS(phrase=lambda name:'sealed key')
    monkeypatch.setitem(sys.modules,'rk.sam3mask',NS(tower=lambda:codec))
    with contract_epoch(False):
        assert core.lift(dict(phrases=[]),'chair',None)==([],[])

def test_box_renderer_status_paths(tmp_path,monkeypatch):
    from trace_format import box_v313 as B
    from trace_format.ground_v313 import Session
    from student_pilot import ground_lifting as G
    monkeypatch.setattr(B.old,'direct_continuation',lambda item:('Locate the chair and estimate its distance visually.','2.00'))
    geo=fixture('nadir')[1]()
    s=Session(G,geo,None,program_version='3.13',instances=lambda name:[dict(instance_id='1',masks=masks(name).masks,prob=np.ones(32))])
    item=dict(qid='legacy-row',type='object_abs_distance',roles=dict(a='chair',b='table'),gt_authority='fixture',question='How far?',options=[])
    s.simulated_misses.add('chair')
    row=B.render(item,s,lambda text:len(text.split()))
    assert len(row['events'])==1 and row['not_seen']
    s=session(geo,tmp_path)
    s.simulated_misses.add('chair')
    row=B._disabled_render_camera(dict(item,type='camera_obj_abs_dist',roles=dict(frame=2,names=['chair'])),s,lambda text:len(text.split()))
    assert row['not_seen']
    from generator.derivgen_v7.derivgen import box_v313 as old
    with contract_epoch(False):
        assert old.replay_audit([dict(call='<ground obj="chair" mode="box">',response=B.old.wrap('chair: not seen'))])==[]

def test_defined_heading_training_depth_stays_byte_identical():
    from student_pilot.carrier_c1_routing import rerender
    geo=NS(down=np.array([0.,1.,0.]),click=lambda *args:([1.,2.,3.],[4.,5.,6.],0.))
    events=[dict(kind='tool_call',name='depth_at',token='<depth_at frame=1 pts=[[500,500]]>',call_id='d',arguments=dict(pts=[[500,500]])),
            dict(kind='tool_response',name='depth_at',call_id='d',points=[dict(label='P1',actual_frame=1,requested_frame=1)])]
    row=dict(events=events,answer='1',trace_revision='3.14')
    current=rerender(row,geo)
    with contract_epoch(False):assert rerender(row,geo)==current

def test_session_heading_applies_to_head_calls_and_keeps_displacement(tmp_path):
    s=session(fixture('nadir')[1](),tmp_path)
    assert response(s,'<pose frame=1>')=='f1 centre (0.00, 0.00, 0.00) m, yaw 0 deg'
    body=response(s,'<move from=1 to=2>')
    assert 'heading unavailable (frame 1)' in body and 'distance = ' in body
    assert not s.registry._points
