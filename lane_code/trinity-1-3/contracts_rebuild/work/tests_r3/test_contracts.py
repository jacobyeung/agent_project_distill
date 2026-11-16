import ast
import copy
import dataclasses
import json
from pathlib import Path
from types import SimpleNamespace as NS
import numpy as np
import pytest
from fixtures_contracts import L,fixture,rotations,session,response,CALLS,masks
from trace_format.contracts import contract_epoch, response_status, RUNTIME_STATUSES, heading_available, geometry_mode

def test_reviewed_guard_ast_grid_and_jitter():
    from student_pilot import geometry_profiles as G
    ref=(L/'work/ref/gravity_guard_a62e3975_recovered.py').read_text()
    a=ast.parse(ref); b=ast.parse(Path(G.__file__).read_text())
    fn=lambda tree:next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='validate_up_convention')
    assert ast.dump(fn(a))==ast.dump(fn(b))
    const=lambda tree:next(n.value for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='UP_PLANE_MIN' for t in n.targets))
    assert ast.dump(const(a))==ast.dump(const(b))
    namespace=dict(np=np,GeometryError=G.GeometryError,UP_PLANE_MIN=.3)
    exec(compile(ast.Module(body=[fn(a)],type_ignores=[]),'reviewed','exec'),namespace)
    def verdict(f,R):
        try:f(R);return 'pass'
        except G.GeometryError as e:return str(e)
    rng=np.random.default_rng(845)
    total=0
    for pitch in range(-90,91,5):
        for roll in range(-180,181,5):
            for jitter in (np.zeros(2),rng.normal(0,.03,2)):
                R=np.repeat(rotations()[None],32,axis=0)
                R[0]=rotations(pitch+jitter[0],roll+jitter[1])
                assert verdict(G.validate_up_convention,R)==verdict(namespace['validate_up_convention'],R)
                assert np.linalg.norm(R[0,2,:2])==pytest.approx(np.linalg.norm(R[0,:2,2]),abs=1e-12)
                total+=1
    (L/'out/GUARD_GRID_r3.json').write_text(json.dumps(dict(poses=total,reference=str(L/'work/ref/gravity_guard_a62e3975_recovered.py'))))

@pytest.mark.parametrize('kind',['landscape','portrait','nadir','nadir_positive','vertical','rolled','inverted','inverted_portrait','small'])
def test_actual_cpu_session(kind,tmp_path):
    contract,make=fixture('landscape' if kind=='small' else kind)
    if kind.startswith('inverted'):
        from student_pilot.geometry_profiles import GeometryError
        with pytest.raises(GeometryError,match='reference_camera_up_opposes_gravity'):make()
        return
    geo=make(); s=session(geo,tmp_path,small=kind=='small')
    texts={call:response(s,call) for call in CALLS}
    from student_pilot.live_trace313 import parse_response,AuditSession
    for call,body in texts.items():
        parse_response(call,body,'3.14')
    if kind in ('nadir','nadir_positive','vertical'):
        assert 'heading unavailable' in texts[CALLS[0]]
        assert '\nsize ' in texts[CALLS[0]]
        assert texts[CALLS[2]].startswith('distance ')
        assert texts[CALLS[3]].startswith('distance ')
        assert 'area ' in texts[CALLS[-1]]
        assert s.registry._points and all(not p.get("heading_defined",True) for p in s.registry._points.values())
    elif kind=='small':
        assert texts[CALLS[0]]=='chair: box unavailable'
    else:
        assert texts[CALLS[0]].startswith('chair: frames')
        assert texts[CALLS[2]].startswith('distance ')
    audit=AuditSession(s.queries,'3.14')
    assert [audit.execute(c) for c in CALLS]==list(texts.values())
    (L/f'out/fixture_{kind}_r3.json').write_text(json.dumps(dict(plane=float(np.linalg.norm(contract.camera_to_world[0,2,:2])),
        margin=float(-contract.camera_to_world[0,2,1]),verdict='pass',responses=texts),indent=2))

@pytest.mark.parametrize('text,expected',[(s,s) for s in RUNTIME_STATUSES]+[
    ('error: x','error'),('chair: not seen','not seen'),('distance 1.20 m','ok'),
    ('chair: frames 1\nsize unavailable','ok'),
    ('distance 1.00 m\ntable: unresolved','ok'),
    ('<tool_response>\nunavailable\n</tool_response>','unavailable'),('', 'missing response'),(None,'missing response')])
def test_response_status(text,expected):
    assert response_status(text)==expected

@pytest.mark.parametrize('question,options,raw,expected',[
    ('What is the distance between the refrigerator and the bucket (in meters)?',[],['REFRIGERATORS',' buckets '],['bucket','refrigerator']),
    ('What is the distance between the microwave and the printer (in meters)?',[],['MICROWAVES','Printers'],['microwave','printer']),
    ('How far is the table lamp from the office chairs?',[],['table_lamps',' Office Chairs '],['office chair','table lamp']),
    ('Which object?',['A. trash can','B. mini fridge'],['Trash_Cans','Mini_Fridges'],['mini fridge','trash can'])])
def test_independent_admission_and_real_runtime(question,options,raw,expected,tmp_path):
    from student_pilot.training_contract import admission_phrases
    from student_pilot.s1_grounding import candidate_names,build_backend
    from student_pilot.routed_features import select_instances
    from student_pilot.ground_sources import MaskProvider
    from student_pilot.live_instances314 import ExactFrames
    # Admission parses the question independently; runtime consumes raw cache phrases.
    admitted=admission_phrases(question,options,None)
    assert list(admitted)==expected
    geo=fixture()[1]()
    row=dict(question_type='object_abs_distance',student_input=dict(question=question,options=options))
    b=build_backend(row,dict(frame_indices=list(range(32)),video_sha256='b'*64,cache_phrases=raw),dict(sha256='c'*64),tmp_path)
    assert b.config['candidate_universe']==list(admitted)
    b.geometry=geo;b.geometry_error=None
    b.source=MaskProvider(lambda n:masks(n),'synthetic-cache',raw)
    for name in admitted:
        result,audit=select_instances(b,name,ExactFrames(geo))
        assert audit['candidate_universe']==list(admitted)
        assert isinstance(result,list)
    assert candidate_names(question,options)==admitted

def test_epoch_legacy_candidate_universe(tmp_path):
    from student_pilot.s1_grounding import build_backend
    from student_pilot.routed_features import select_instances
    row=dict(question_type='object_abs_distance',student_input=dict(question='How far is the refrigerator from the bucket?',options=[]))
    b=build_backend(row,dict(frame_indices=list(range(32)),video_sha256='a'*64),dict(sha256='b'*64),tmp_path,dict(contract_epoch=False))
    assert b.config['candidate_universe']==['refrigerator']
    assert 'contract_epoch' not in b.config
    b.geometry_error=None
    with contract_epoch(False),pytest.raises(ValueError,match='requires a fixed named candidate universe'):
        select_instances(b,'bucket',fixture()[1]())

def test_bridge_does_not_recut_and_replay(tmp_path):
    from student_pilot.live_instances314 import bridge_cut,relift_instances
    geo=fixture()[1]()
    s=session(geo,tmp_path,policy=True)
    text=response(s,CALLS[0])
    assert 'box unavailable' not in text and 'frames' in text
    q=s.queries[-1]
    assert q['instances']
    for item in q['instances']:
        assert item['depth_cut_applied'] and not item['depth_cut']
        assert item['result']['points_cut']==item['result']['points']
    replay=relift_instances(q,geo)
    for a,b in zip(replay,q['instances']):assert a['result']['points_cut']==b['result']['points_cut']
    points={'2':[[1,2,3]]}
    assert bridge_cut(dict(points=points),dict(depth_cut_applied=True),True)['points_cut'] is points
    assert 'points_cut' not in bridge_cut(dict(points=points),dict(depth_cut_applied=True),False)
    assert 'points_cut' not in bridge_cut(dict(points=points),{},True)

def test_shared_normalizer_cache_lookup_and_accessors(tmp_path):
    from student_pilot.phrases import normalize_phrase,cache_key
    from student_pilot.sam3_tower import normalize_phrase as tower
    from student_pilot.scene_state import normalize_name
    from student_pilot.ground_admission import normalized_name
    from student_pilot.ground_sources import cache_phrase
    for name in ('Office_Chairs','TRASH CANS',' mini fridges ','table lamps','shelves'):
        assert normalize_phrase(name)==tower(name)==normalize_name(name)==normalized_name(name)
    codec=NS(phrase=lambda n:'wrong')
    assert cache_phrase({'phrases':['Office_Chairs']},'office chair',codec)=='Office_Chairs'
    assert cache_key({'phrases':[]},'table lamps')=='table lamp'
    assert cache_key({'phrases':['chairs','chair']},'chair') == 'chair'
    with contract_epoch(False):assert cache_phrase({},'chair',codec)=='wrong'
    assert geometry_mode(NS())=='sensor'
    with pytest.raises(ValueError,match='unknown_geometry'):geometry_mode(NS(geometry_mode='x'))
    with pytest.raises(ValueError,match='boolean'):
        with contract_epoch('x'):pass
    from trace_format.contracts import status_text
    with pytest.raises(ValueError,match='unknown_runtime'):status_text('x')

def row_case(case):
    calls=[dict(call='<ground obj="chair" mode="box">',response='chair: not seen')]
    row=dict(qid=case,question='How far is the chair from the table?',options=[],events=calls,
        target='<think>\nLocate the chair and estimate visually.\n</think>\n<answer>2</answer>',candidate_phrases=['chair','table'])
    if case=='after_failure':calls.extend([dict(call='<ground obj="table" mode="box">',response='table: not seen'),
        dict(call='<gap a="chair" b="table" rule="box_grid_5cm">',response='not seen')])
    if case=='same_retry':calls.append(dict(call=calls[0]['call'],response='chair: not seen'))
    if case=='missing_response':calls[0].pop('response')
    if case=='manifest':
        row.pop('candidate_phrases')
        row['question']='Estimate the separation visually.'
    if case=='operator':calls[0]['response']='error: form_requires_v3.13'
    if case=='unknown':calls[0]['response']='chair: occluded'
    if case=='legal_retry':calls.append(dict(call='<ground obj="table" mode="box">',response='table: not seen'))
    return row

@pytest.mark.parametrize('case,reason',[
    ('after_failure','contract_call_after_failed_ground'),('same_retry','contract_call_after_failed_ground'),
    ('missing_response','contract_missing_response'),('manifest','contract_manifest_missing'),
    ('operator','contract_operator_fault'),('unknown','contract_unknown_status'),('clean',None),('legal_retry',None)])
def test_row_audit(case,reason):
    from student_pilot.training_contract import audit_training_contract
    row=row_case(case)
    assert audit_training_contract([row])==[reason]
    with contract_epoch(False):assert audit_training_contract([row])==[None]

def test_head_direction_outputs_refuse_without_allocating_points():
    from student_pilot.carrier_c1_decode import respond
    from student_pilot.p3_printed_calculator import PrintedPointRegistry
    from fixtures_contracts import own_geometry
    geo=own_geometry(fixture('nadir_positive')[1]())
    registry=PrintedPointRegistry()
    depth=respond('<depth_at frame=1 pts=[[500,500]]>',registry,geo)[0]
    assert 'cam1' in depth and 'heading unavailable' in depth
    assert 'heading unavailable' in respond('<pose frame=1>',registry,geo)[0]
    assert 'distance = ' in respond('<move from=1 to=2>',registry,geo)[0]
    assert 'heading unavailable (frames 1)' in respond('<turn from=1 to=2>',registry,geo)[0]
    assert respond('<angle S=P1 F=P2 Q=P3 rule=easy>',registry,geo)[0]=='error: unknown_point_label'
    assert len(registry._points)==1
