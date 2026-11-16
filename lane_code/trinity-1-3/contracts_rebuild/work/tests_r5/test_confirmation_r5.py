import ast
import copy
import json
import subprocess
import sys
from pathlib import Path
import pytest
from fixtures_contracts import L, fixture, masks, own_geometry
from trace_format.contracts import contract_epoch


def test_sensor313_off_provider_and_audit():
    from student_pilot import ground_lifting
    from trace_format.ground_v313 import Session
    from student_pilot.live_trace313 import AuditSession
    with contract_epoch(False):
        s=Session(ground_lifting,fixture()[1](),None,
            instances=lambda n:[dict(instance_id='1',masks=masks(n).masks,prob=[1.]*32)],
            program_version='3.13',geometry_mode='sensor')
        assert s.box_provider_id == 'fit_gbox_best_v1'
        text=s.execute('<ground obj="chair" mode="box">')
        assert 'size 0.40 x 0.02 x 0.86' in text
        assert 'centre (-0.62, -0.06, 2.07)' in text
        assert AuditSession([{'box_provider_id':'fit_gbox_best_v1'}]).box_provider_id=='fit_gbox_best_v1'
    with contract_epoch(True):
        s=Session(ground_lifting,fixture()[1](),None,program_version='3.13',geometry_mode='sensor')
        assert s.box_provider_id=='fit_gbox_fused_full_v1'


def test_rotated_calculator_fields():
    path=L/'work/review2_inputs/attack_r4_angle.py'
    from scipy.spatial.transform import Rotation
    import numpy as np
    from student_pilot.carrier_c1_routing import OwnGeometry
    from student_pilot.carrier_c1_decode import respond
    from trace_format.calculator import PrintedPointRegistry
    module=ast.parse(path.read_text())
    nodes=[n for n in module.body if isinstance(n,ast.FunctionDef)]
    calls=['<depth_at frame=2 pts=[[200,300],[800,350],[450,800]]>',
           '<angle S=P1 F=P2 Q=P3 rule=hard>','<turn from=P1 at=P2 to=P3>',
           '<dist P1 P2>','<area C=P1,P2,P3>']
    ns=dict(np=np,Rot=Rotation,fixture=fixture,OwnGeometry=OwnGeometry,respond=respond,
            PrintedPointRegistry=PrintedPointRegistry,CALLS=calls,
            BASE=np.array([[1.,0,0],[0,0,1],[0,-1,0]]))
    exec(compile(ast.Module(body=nodes,type_ignores=[]),str(path),'exec'),ns)
    with contract_epoch(True):
        rows=[ns['run'](yaw) for yaw in (0,40,130,250)]
    assert all(row==rows[0] for row in rows), rows
    for call in calls[1:3]:
        assert rows[0][call].startswith('u heading unavailable; v heading unavailable; dot ')


def test_grounded_calculator_metric_basis_and_generator_parity():
    import numpy as np
    from scipy.spatial.transform import Rotation
    from types import SimpleNamespace
    from student_pilot.ground_lifting import public_centres
    from trace_format.calculator import PrintedPointRegistry
    from generator.derivgen_v7.derivgen.calculator import PrintedPointRegistry as GeneratorRegistry
    from fixtures_contracts import rotations
    outputs=[]
    with contract_epoch(True):
        for yaw in (0,40,130,250):
            R1=Rotation.from_euler('z',yaw,degrees=True).as_matrix()@rotations(-88)
            geo=SimpleNamespace(cam=lambda k:(R1 if k==1 else rotations(),np.zeros(3)))
            registry,generated=PrintedPointRegistry(),GeneratorRegistry()
            for point in ([0.,0.,0.],[1.,.4,1.],[.3,1.2,2.]):
                camera,f1=public_centres(geo,2,np.asarray(point),metric_only=True)
                kw=dict(camera=camera.tolist(),f1=f1.tolist(),spread=0.,requested_frame=2,heading_defined=False)
                assert registry.register(**kw)['line']==generated.register(**kw)['line']
            calls=['<angle S=P1 F=P2 Q=P3 rule=hard>','<turn from=P1 at=P2 to=P3>',
                   '<dist P1 P2>','<closest A=P1 B=P2,P3>','<cam_dist P2,P3>','<area C=P1,P2,P3>']
            texts=[registry.execute(call)['text'] for call in calls]
            assert texts==[generated.execute(call)['text'] for call in calls]
            outputs.append(texts)
    assert all(row==outputs[0] for row in outputs)


@pytest.mark.parametrize('superset', ['manifest','phrases','cache','batch'])
@pytest.mark.parametrize('operand',['chair','lamp'])
def test_shared_binding_served_or_deferred(superset,operand,tmp_path):
    from student_pilot.phrases import candidate_binding
    from student_pilot.training_contract import audit_training_contract
    from student_pilot.s1_grounding import build_backend
    row=dict(qid='binding',question_type='object_abs_distance',uses_mask_cache=True,
        student_input=dict(question='How far is the chair from the table?',options=[]),
        candidate_phrases=['chair','table'],candidate_manifest=['chair','table'],
        cache_phrases=['chair','table'],target='<answer>x</answer>',
        events=[dict(call=f'<ground obj="{operand}" mode="box">',response=f'{operand}: not seen')])
    key=dict(manifest='candidate_manifest',phrases='candidate_phrases',cache='cache_phrases',batch='batch_cache_phrases')[superset]
    row[key]=['chair','table','lamp']
    batch=dict(frame_indices=list(range(32)),video_sha256='a'*64)
    if superset=='batch':batch['cache_phrases']=row[key]
    with contract_epoch(True):
        backend=build_backend(row,batch,dict(sha256='b'*64),tmp_path)
        universe=backend.config['candidate_universe']
        verdict=audit_training_contract([row])[0]
        expected={'chair','table','lamp'} if superset in ('phrases','batch') else {'chair','table'}
        assert set(universe)==expected
        assert set(universe)==set(candidate_binding(row,batch))
        assert (verdict is None)==(operand in universe)
        assert verdict in (None,'contract_operand_outside_candidates')
        passed_batch=dict(batch,cache_phrases=['chair','table','lamp'])
        assert audit_training_contract([row],batch=passed_batch)==[None]


@pytest.mark.parametrize('pts', [[[300,500]],[[10,500]],[[300+i*100,500] for i in range(5)]])
def test_rerender_depth_arguments(pts):
    from student_pilot.carrier_c1_routing import rerender
    row=dict(events=[dict(kind='plan',text='Read.'),dict(kind='tool_call',call_id='c1',name='depth_at',
        arguments=dict(frame=2,pts=pts),token='<depth_at frame=2 pts=[(300,500)]>'),
        dict(kind='tool_response',call_id='c1',name='depth_at',text='x',
             points=[dict(label=f'P{i+1}',requested_frame=2,actual_frame=2) for i in range(len(pts))])],
        answer='<answer>x</answer>',trace_revision='3.14')
    for kind in ('landscape','nadir_positive'):
        with contract_epoch(True):
            text,spans,_=rerender(row,own_geometry(fixture(kind)[1]()))
        assert 'error:' not in text
        assert text.count('spread ')==len(pts)
        assert ('f1 (heading unavailable,' in text)==(kind=='nadir_positive')


def test_pose_identity_and_later_centre():
    with contract_epoch(True):
        geo=own_geometry(fixture('nadir_positive')[1]())
        assert geo.pose_text(1)=='f1 centre (0.00, 0.00, 0.00) m, yaw 0 deg'


def test_standalone_generator_imports():
    import student_pilot
    tree=Path(student_pilot.__file__).resolve().parent.parent
    script="import sys;sys.path.insert(0,sys.argv[1]);import derivgen.canon,derivgen.program,derivgen.calculator,derivgen.camera_rows;assert 'trace_format' not in sys.modules"
    p=subprocess.run([sys.executable,'-I','-s','-B','-c',script,str(tree/'generator/derivgen_v7')],
        cwd=L,capture_output=True,text=True)
    assert p.returncode==0,p.stderr


@pytest.mark.parametrize('damage',['unbacked','mismatch','unknown'])
def test_generator_refusal_type(damage):
    from generator.derivgen_v7.derivgen.trace import render
    from generator.derivgen_v7.derivgen.common import Refusal
    call=dict(role='assistant',kind='tool_call',call_id='t1',name='unknown',arguments={})
    event=dict(role='tool',kind='tool_response',call_id='t1',name='unknown',values={})
    if damage=='mismatch':event['name']='pose'
    if damage=='unbacked':event['call_id']='t2'
    with pytest.raises(Refusal):render([call,event],'<answer>x</answer>')


def test_legacy_gap_off_grammar():
    from student_pilot.live_trace313 import parse_response
    call='<gap a="chair" b="table">'
    with contract_epoch(False),pytest.raises(ValueError):parse_response(call,'1.88 m','3.12.2')
    with contract_epoch(True),pytest.raises(ValueError):parse_response(call,'1.88 m','3.12.2')


def test_declared_revision_controls_instance_grammar():
    from trace_format.ground_v313 import Session
    from student_pilot import ground_lifting
    from student_pilot.training_contract import audit_training_contract
    with contract_epoch(True):
        s=Session(ground_lifting,fixture()[1](),None,program_version='3.14',multi_instance=True,
            instances=lambda n:[dict(instance_id=str(i),masks=masks(n).masks,prob=[1.]*32) for i in (1,2)])
        call='<ground obj="chair" mode="box">'
        body=s.execute(call)
        assert body.startswith('chair: 2 instances')
        row=dict(candidate_phrases=['chair'],events=[dict(call=call,response=body)],spec_version='3.13')
        assert audit_training_contract([row])==['contract_unknown_status']
        assert audit_training_contract([dict(row,spec_version='3.14')])==[None]


def test_paired_text_call_id_mismatch():
    from student_pilot.training_contract import audit_training_contract
    row=dict(events=[dict(kind='tool_call',call_id='a',token='<pose frame=1>'),
                     dict(kind='tool_response',call_id='b',text='f1 centre (0.00, 0.00, 0.00) m, yaw 0 deg')])
    assert audit_training_contract([row])==['contract_malformed_row']


def test_vocabulary_and_suffix_exclusions():
    from student_pilot.phrases import candidate_phrases,normalize_phrase,ANGLE_TEMPLATES
    from trace_format.category_vocab import vocabulary
    candidates=[(k,v) for k,v in vocabulary().items() if any(normalize_phrase(n)!=normalize_phrase(k) for n in v)]
    assert candidates
    for category,labels in candidates:
        question=ANGLE_TEMPLATES[0].format(stand=category,face='table',query='plant',sense='clockwise')
        names=candidate_phrases(question,['A. left','B. right'])
        assert set(map(normalize_phrase,labels)) <= set(names),(category,labels,names)
    for phrase in ('canvases','archives'):
        assert normalize_phrase(phrase)==phrase
    with contract_epoch(False):
        question=ANGLE_TEMPLATES[0].format(stand='bed',face='table',query='plant',sense='clockwise')
        assert 'mattress' not in candidate_phrases(question,[])


def test_all_angle_templates_and_aliases():
    from student_pilot.phrases import candidate_phrases,ANGLE_TEMPLATES
    aliases={'sofa':'couch','computer tower':'tower','computer mouse':'mouse','ceiling light':'ceiling lamp'}
    with contract_epoch(True):
        for template in ANGLE_TEMPLATES:
            for name,alias in aliases.items():
                question=template.format(stand=name,face='table',query='plant',sense='counterclockwise')
                assert {name,alias,'table','plant'} <= set(candidate_phrases(question,[]))


def test_cache_lookup_preserves_caller():
    from student_pilot.phrases import cache_key,cache_view
    cache=dict(phrases=['chair','chairs'],frames={'0':dict(phrases={
        'chair':dict(presence=.2,instances=[dict(score=.3)]),
        'chairs':dict(presence=.9,instances=[dict(score=.8)])})})
    original=copy.deepcopy(cache)
    assert cache_key(cache,'chairs')=='chair'
    merged,key=cache_view(cache,'chairs')
    assert cache==original
    assert key=='chair' and merged['phrases']==['chair']
    assert merged['frames']['0']['phrases']['chair']['presence']==.9
    assert len(merged['frames']['0']['phrases']['chair']['instances'])==2


def test_strict_heading_comparison():
    import importlib.util
    path=L/'work/row_families_r5/heading_compare.py'
    spec=importlib.util.spec_from_file_location('strict_heading',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    old=json.loads((L/'work/row_families_r4/off.json').read_text())['results']
    on=json.loads((L/'work/row_families_r4/on.json').read_text())['results']
    by_key={(r['family'],r['variant']):r for r in old}
    rows=[r for r in on if r['family']=='routing/depth_at' and r['variant'].startswith('nadir_positive')]
    assert rows
    for row in rows:
        base=by_key[row['family'],row['variant']]['row']
        assert 'error: malformed_call' in row['row']['target']
        assert not module.row_texts_valid(base,row['row'])
    a='P1: cam2 (1.00, 2.00, 3.00) m; f1 (4.00, 5.00, 6.00) m; spread 0.10'
    b='P1: cam2 (1.00, 2.00, 3.00) m; f1 (heading unavailable, 5.00, heading unavailable) m; spread 0.10'
    assert module.heading_text(a,b)
    assert not module.heading_text(a,b.replace('spread 0.10','spread 0.11'))
    assert not module.heading_text(a,b.replace('5.00','5.01'))
    assert not module.heading_text(a,b.replace('cam2','cam3'))


def test_move_nadir_distance_retains_sealed_rounding():
    geo=own_geometry(fixture('nadir_positive')[1]())
    with contract_epoch(False):old=geo.move_text(1,4)
    with contract_epoch(True):new=geo.move_text(1,4)
    assert old.split('distance = ')[1]==new.split('distance = ')[1]


def test_dead_partial_ground_and_registry_status_probe():
    from trace_format.contracts import response_status
    from student_pilot.training_contract import audit_training_contract
    from trace_format.ground_v313 import Session
    from student_pilot import ground_lifting
    from types import SimpleNamespace
    for text in ('chair: frames 2,3 (best 2)\nheading unavailable',
                 'chair: 2 instances\nheading unavailable',
                 'chair: 2 found\nheading unavailable'):
        assert response_status(text)=='ok'
    for kind in ('landscape','nadir_positive'):
        for enabled in (False,True):
            with contract_epoch(enabled):
                s=Session(ground_lifting,fixture(kind)[1](),None,program_version='3.14',
                    instances=lambda n:[] if n=='absent' else [dict(instance_id='1',masks=masks(n).masks,prob=[1.]*32)])
                for name in ('chair','table','absent'):
                    body=s.execute(f'<ground obj="{name}" mode="box">')
                    assert (s.box_registry.states.get(name)=='ok')==(response_status(body)=='ok')
