import dataclasses,json,re
from pathlib import Path
import numpy as np
import pytest
from fixtures_contracts import L,fixture,rotations,session,response,CALLS
from trace_format.contracts import contract_epoch,heading_available

KINDS=['landscape','portrait','nadir','nadir_positive','vertical','inverted','inverted_portrait','rolled','small','mdg','nadir_003']

@pytest.mark.parametrize('kind',KINDS)
def test_b2_fixture_matrix(kind,tmp_path):
    from student_pilot.geometry_profiles import ProfileGeometry,GeometryError
    c,make=fixture('landscape' if kind in ('small','mdg','nadir_003') else kind)
    if kind=='nadir_003':c.camera_to_world[0,:3,:3]=rotations(-np.degrees(np.arccos(.03)),180)
    depth=fixture()[1]().depth_grid
    records={}
    for orientation in ('original','inverted','rolled90'):
        C=c.camera_to_world.copy()
        if orientation!='original':
            # Retain each pitch and translation, set absolute image roll.
            # This keeps the inverted input fixtures genuinely inverted too.
            for i in range(len(C)):
                pitch=np.degrees(np.arcsin(np.clip(C[i,2,2],-1,1)))
                C[i,:3,:3]=rotations(pitch,180 if orientation=='inverted' else 90)
        case=dataclasses.replace(c,camera_to_world=C)
        modes={}
        for enabled in (False,True):
            with contract_epoch(enabled):
                r=dict(responses={},guard='pass',plane=float(np.linalg.norm(C[0,2,:2])),margin=float(-C[0,2,1]))
                try:
                    case.validate()
                    geo=ProfileGeometry(case,depth)
                    r['heading_defined']=heading_available(geo)
                    s=session(geo,tmp_path/orientation/str(enabled),small=kind=='small',policy=kind=='mdg')
                    for call in CALLS:r['responses'][call]=response(s,call)
                except GeometryError as e:r['guard']=str(e)
                modes['on' if enabled else 'off']=r
        on,off=modes['on'],modes['off']
        if orientation=='inverted':assert on['guard']=='reference_camera_up_opposes_gravity'
        if orientation=='rolled90':assert on['guard']=='pass'
        if orientation=='original' and kind in ('nadir','nadir_positive','nadir_003','vertical'):
            assert on['guard']=='pass'
            assert 'heading unavailable' in on['responses'][CALLS[0]]
        if on['guard']==off['guard']=='pass':
            # A sealed guard pass can still encounter the known MDG box defect
            # or a singular lifting basis. Compare each emitted metric value.
            metrics=lambda text:re.findall(r'(?m)^(?:distance |area |size )[^\n]*',text)
            matches=[];exceptions=[]
            for call in CALLS:
                a,b=off['responses'].get(call,''),on['responses'].get(call,'')
                if metrics(a):assert metrics(a)==metrics(b),(kind,orientation,call,a,b)
                if a==b:matches.append(call)
                elif kind=='mdg' and ('unavailable' in a or a=='not seen'):
                    exceptions.append(dict(call=call,reason='Sealed MDG box unavailable; required bridge serves metric.',off=a,on=b))
                elif 'heading unavailable' in b:
                    assert not on['heading_defined']
                else:
                    # Exact vertical sealed lifting refuses even after guard pass.
                    assert 'error:' in a or 'unavailable' in a or (kind=='vertical' and a=='not seen'),(kind,orientation,call,a,b)
                    exceptions.append(dict(call=call,reason='Sealed lifting basis unavailable after guard pass.',off=a,on=b))
            modes['metric_parity_asserted']=True;modes['exceptions']=exceptions
        records[orientation]=modes
    (L/f'work/test_artifacts_r6/B2_fixture_{kind}_r4.json').write_text(json.dumps(dict(source=str(Path(__file__)),kind=kind,orientations=records),indent=2)+'\n')

def test_real_distance_parser_and_admission():
    from student_pilot.training_contract import audit_training_contract,admission_phrases
    proof=json.loads((L/'out/REAL_ROW_DEFECT_B1.json').read_text());row=proof['row']
    assert admission_phrases(row['question'],row['options'],None)==('clock','lamp')
    assert audit_training_contract([row])==[None]
    assert audit_training_contract([row],{})==['contract_manifest_missing']

@pytest.mark.parametrize('kind',['landscape','portrait','rolled','nadir_positive'])
def test_head_outputs_through_bound_session(kind,tmp_path):
    from scipy.spatial.transform import Rotation
    from types import SimpleNamespace as NS
    from student_pilot.carrier_c1_routing import OwnGeometry
    calls=['<depth_at frame=1 pts=[[500,500]]>','<pose frame=1>','<move from=1 to=2>','<turn from=1 to=2>']
    records={}
    for enabled in (False,True):
        with contract_epoch(enabled):
            c,make=fixture(kind);geo=make();C=c.camera_to_world
            extrinsics=np.linalg.inv(C)@C[0]
            p=np.zeros((32,9));p[:,:3]=extrinsics[:,:3,3]
            p[:,3:7]=Rotation.from_matrix(extrinsics[:,:3,:3]).as_quat()
            p[:,7:9]=np.pi/3
            own=OwnGeometry(p,C[0,2,:3],geo.depth)
            s=session(geo,tmp_path/str(enabled))
            s.bind_state(NS(verify_session=None,heads=NS(mdg_states=None,mdg_backend=None),
                mdg=None,ground_backend=s.owner,tool_context=NS(),rereader=None,geometry=own))
            records['on' if enabled else 'off']={call:response(s,call) for call in calls}
    for call in calls:
        if kind=='nadir_positive' and not call.startswith('<pose '):
            assert 'heading unavailable' in records['on'][call]
            if call.startswith('<move'):
                metric=lambda t:re.search(r'distance = ([0-9.]+) m',t)[1]
                assert metric(records['on'][call])==metric(records['off'][call])
        else:assert records['on'][call]==records['off'][call]
    (L/f'work/test_artifacts_r6/B2_heads_{kind}_r4.json').write_text(json.dumps(dict(source=str(Path(__file__)),responses=records),indent=2)+'\n')
