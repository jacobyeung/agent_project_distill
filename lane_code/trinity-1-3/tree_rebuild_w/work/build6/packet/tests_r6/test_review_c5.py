"""Construction/use context and strict input regressions from the confirmation review."""
from pathlib import Path
from types import SimpleNamespace as NS
import ast, copy, importlib.util, json, os, subprocess, sys
import numpy as np
import pytest
from fixtures_contracts import fixture, own_geometry, rotations
from trace_format.contracts import contract_epoch
L=Path(__file__).resolve().parents[2]/'proofs/packet'


def pitched_geometry():
    contract,make=fixture('landscape')
    contract.camera_to_world[0,:3,:3]=rotations(-80,0)
    contract.camera_to_world[1:,:3,:3]=np.array([rotations()@np.array(
        [[np.cos(a),0,np.sin(a)],[0,1,0],[-np.sin(a),0,np.cos(a)]])
        for a in np.radians(np.arange(1,32)*7.)])
    return own_geometry(make())


@pytest.mark.parametrize('query', [(False,.3),(True,.1)])
def test_basis_uses_query_context(query):
    from student_pilot.carrier_c1_decode import respond
    from trace_format.calculator import PrintedPointRegistry
    calls=['<depth_at frame=2 pts=[[300,500]]>','<pose frame=3>','<move from=1 to=3>']
    with contract_epoch(True,heading_plane_min=.3):
        cross=pitched_geometry()
        cross.pose(3)  # Populate the pose cache in the construction context.
    with contract_epoch(query[0],heading_plane_min=query[1]):
        fresh=pitched_geometry()
        actual=[respond(c,PrintedPointRegistry(),cross)[0] for c in calls]
        expected=[respond(c,PrintedPointRegistry(),fresh)[0] for c in calls]
        assert actual==expected
        assert 'f1 (-0.24, 0.00, 2.12)' in actual[0]
        assert 'yaw -14 deg' in actual[1]
    with contract_epoch(True,heading_plane_min=.3):
        assert cross.pose_text(3)==pitched_geometry().pose_text(3)


@pytest.mark.parametrize('ambient,backend_epoch',[(True,False),(False,True)])
def test_live_provider_uses_backend_epoch(ambient,backend_epoch,tmp_path):
    from fixtures_contracts import masks, head_state, response
    from student_pilot.ground_sources import MaskProvider
    from student_pilot.ground_v3 import GroundV3
    from student_pilot.scene_state import SceneState
    from student_pilot.live_trace313 import LiveSession,AuditSession
    geo=fixture()[1]()
    with contract_epoch(backend_epoch,heading_plane_min=.1):
        owner=GroundV3(SceneState('a'*64,geo.frame_map,geo.identity),geo,
            MaskProvider(masks,'fixture',('chair',)),mask_source='mdg',audit_dir=tmp_path)
    with contract_epoch(ambient):
        session=LiveSession(owner,program_version='3.13',geometry_mode='sensor')
        assert session.box_provider_id==('fit_gbox_fused_full_v1' if backend_epoch else 'fit_gbox_best_v1')
        session.bind_state(head_state(geo,owner))
        call='<ground obj="chair" mode="box">'
        text=response(session,call)
        audit=AuditSession(session.queries,'3.13')
        assert audit.execute(call)==text
        assert session.heading_plane_min==.1


def test_generator_import_order():
    import student_pilot
    tree=Path(student_pilot.__file__).resolve().parents[1]
    code="""import sys
sys.path[:0]=[sys.argv[1],sys.argv[1]+'/generator/derivgen_v7']
from derivgen.calculator import PrintedPointRegistry
assert 'trace_format.contracts' not in sys.modules
reg=PrintedPointRegistry()
p=reg.register(camera=[1,2,3],f1=[4,5,6],spread=0,requested_frame=2,heading_defined=False)
assert 'heading unavailable' in p['line']
"""
    p=subprocess.run([sys.executable,'-I','-s','-B','-c',code,str(tree)],capture_output=True,text=True)
    assert p.returncode==0,p.stderr


def test_cache_view_shares_mask_payload_without_mutation():
    from student_pilot.phrases import cache_view
    mask={'counts':[1,4,2],'size':[2,4]}
    cache={'phrases':['chair','chairs'],'frames':{'0':{'phrases':{
        'chair':{'presence':.2,'instances':[{'score':.3,'mask':mask}]},
        'chairs':{'presence':.9,'instances':[]}}}}}
    original=copy.deepcopy(cache)
    view,key=cache_view(cache,'chair')
    assert view['frames']['0']['phrases'][key]['instances'][0]['mask'] is mask
    assert cache==original
    assert view['frames']['0']['phrases'][key]['presence']==.9
    assert cache_view({'phrases':['chair'],'frames':{}},'chair')[1]=='chair'


def test_missing_manifest_phrases(tmp_path):
    from student_pilot.phrases import candidate_binding
    from student_pilot.s1_grounding import build_backend
    row=dict(qid='missing',question_type='object_abs_distance',uses_mask_cache=True,
             candidate_manifest={},student_input=dict(question='How far is the chair from the table?',options=[]))
    assert candidate_binding(row) is None
    with contract_epoch(True),pytest.raises(ValueError,match='contract_manifest_missing'):
        build_backend(row,dict(frame_indices=list(range(32)),video_sha256='a'*64),dict(sha256='b'*64),tmp_path)


@pytest.mark.parametrize('name,args',[('pose',{'frame':3}),('move',{'from':1,'to':3}),('turn',{'from':1,'to':3})])
def test_rerender_head_arguments(name,args):
    from student_pilot.carrier_c1_routing import rerender
    row=dict(events=[dict(kind='plan',text='Read.'),dict(kind='tool_call',call_id='c1',name=name,
        arguments=args,token=f'<{name} noncanonical>'),dict(kind='tool_response',call_id='c1',name=name,text='x')],
        answer='<answer>x</answer>',trace_revision='3.14')
    for kind in ('landscape','nadir_positive'):
        with contract_epoch(True):
            geo=own_geometry(fixture(kind)[1]())
            text,_,_=rerender(row,geo)
            expected=getattr(geo,name+'_text')(*args.values())
            assert expected in text and 'error:' not in text


@pytest.mark.parametrize('before,after',[({'a':'x'},{'a':'x','b':'y'}),({'a':'x','b':'y'},{'a':'x'}),
    ({'a':1},{'a':2}),({'a':False},{'a':0}),({'a':[1,None]},{'a':[1,0]})])
def test_strict_row_structure(before,after):
    path=Path(os.environ.get('R6_COMPARE',str(L/'work/row_families_r6/heading_compare.py')))
    spec=importlib.util.spec_from_file_location('compare_c5',path)
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    assert not mod.row_texts_valid(before,after)
    assert mod.row_texts_valid(before,copy.deepcopy(before))
