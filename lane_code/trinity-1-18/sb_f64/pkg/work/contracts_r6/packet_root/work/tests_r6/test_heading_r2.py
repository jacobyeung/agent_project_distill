import ast
import dataclasses
import json
import re
from pathlib import Path
from types import SimpleNamespace as NS
import numpy as np
import pytest
from fixtures_contracts import L, fixture, rotations, own_geometry, session, response, masks
from trace_format.contracts import contract_epoch, heading_available, heading_plane_min


@pytest.mark.parametrize('value',[0,1,-.2,1.2,float('nan'),float('inf'),None,True,'0.3'])
def test_invalid_heading_threshold(value):
    with pytest.raises(ValueError,match='heading_plane_min'):
        with contract_epoch(True,heading_plane_min=value):pass


def test_threshold_identity_and_replay(tmp_path):
    from student_pilot.live_trace313 import AuditSession, replay
    from student_pilot.carrier_c1_run import identity
    geo=fixture('nadir_positive')[1]()
    assert heading_plane_min()==.3 and not heading_available(geo)
    with contract_epoch(True,heading_plane_min=.01):
        assert heading_available(geo)
        s=session(geo,tmp_path)
    assert s.heading_plane_min==.01 and s.owner.config['heading_plane_min']==.01
    call='<ground obj="chair">'
    text=response(s,call)
    assert 'heading unavailable' not in text
    assert s.queries[-1]['heading_plane_min']==.01
    result=replay(dict(heads=dict(trace_program_version='3.14',ground_queries=s.queries),calls=[dict(call=call,response=text)]))
    assert result['byte_equal']
    assert identity({'contract_epoch':True})==identity({'contract_epoch':True,'heading_plane_min':.3})
    assert identity({'contract_epoch':True,'heading_plane_min':.1})!=identity({'contract_epoch':True})
    with pytest.raises(ValueError,match='heading_plane_min_mismatch'):
        AuditSession([dict(heading_plane_min=.1),dict(heading_plane_min=.2)])
    with contract_epoch(False,heading_plane_min=.99):
        assert heading_available(geo)
    (L/'work/test_artifacts_r6/HEADING_IDENTITY_R5.json').write_text(json.dumps(dict(source=__file__,backend=s.owner.config,
        session=dict(contract_epoch=s.contract_epoch,heading_plane_min=s.heading_plane_min),query=s.queries[-1],replay=result),indent=2))


@pytest.mark.parametrize('kind',['nadir','nadir_positive','vertical'])
def test_all_relative_head_pairs(kind,tmp_path):
    from student_pilot.carrier_c1_decode import respond
    from trace_format.calculator import PrintedPointRegistry
    geo=fixture(kind)[1]();own=own_geometry(geo);s=session(geo,tmp_path)
    results=[]
    for i in range(2,33):
        for j in range(2,33):
            for name in ('move','turn'):
                call=f'<{name} from={i} to={j}>'
                actual=response(s,call)
                # A vertical reference has no sealed basis. Compare the ON
                # adapters there; OFF must retain the sealed error below.
                with contract_epoch(kind == 'vertical'):
                    expected=respond(call,PrintedPointRegistry(),own)[0]
                if kind == 'vertical':
                    with contract_epoch(False):
                        assert respond(call,PrintedPointRegistry(),own)[0]=='error: vertical_camera_heading'
                assert actual==expected and 'heading unavailable' not in actual,(kind,call,actual,expected)
                results.append(dict(call=call,response=actual))
    depth=response(s,'<depth_at frame=1 pts=[[500,500]]>')
    assert 'cam1 (' in depth and 'spread ' in depth and 'f1 (heading unavailable,' in depth
    pose=response(s,'<pose frame=2>')
    assert 'yaw heading unavailable' in pose
    (L/f'work/test_artifacts_r6/RELATIVE_HEADS_{kind}_R5.json').write_text(json.dumps(dict(source=__file__,kind=kind,
        comparisons=len(results),responses=results,depth=depth,pose=pose),indent=2))


def test_frame_dependencies_and_world_rotation():
    from student_pilot.carrier_c1_decode import respond
    from trace_format.calculator import PrintedPointRegistry
    from student_pilot.geometry_profiles import ProfileGeometry
    c,make=fixture('nadir_positive');C=c.camera_to_world.copy();C[3,:3,:3]=rotations(-90)
    geo=ProfileGeometry(dataclasses.replace(c,camera_to_world=C),make().depth_grid)
    own=own_geometry(geo);registry=PrintedPointRegistry()
    def call(text):return respond(text,registry,own)[0]
    assert 'heading unavailable' not in call('<move from=2 to=4>')
    assert 'frame 4' in call('<move from=4 to=2>')
    assert 'frames 4' in call('<turn from=2 to=4>')
    assert 'cam4 (' in call('<depth_at frame=4 pts=[[500,500]]>')
    from student_pilot.carrier_c1_routing import RenderError
    with contract_epoch(False):
        with pytest.raises(RenderError,match='vertical_camera_heading'):own.move_text(2,4)
        with pytest.raises(RenderError,match='vertical_camera_heading'):own.click(4,[500,500])
    with contract_epoch(True,heading_plane_min=.01):
        assert 'yaw heading unavailable (frame 4)' in call('<pose frame=4>')
    baseline=call('<move from=2 to=3>'),call('<turn from=2 to=3>')
    for angle in (23,81,137):
        a=np.radians(angle);Q=np.array([[np.cos(a),-np.sin(a),0],[np.sin(a),np.cos(a),0],[0,0,1]])
        rotated=C.copy();rotated[:,:3,:3]=Q@C[:,:3,:3];rotated[:,:3,3]=C[:,:3,3]@Q.T
        own=own_geometry(ProfileGeometry(dataclasses.replace(c,camera_to_world=rotated),geo.depth_grid))
        assert baseline==(call('<move from=2 to=3>'),call('<turn from=2 to=3>'))


def test_calculator_field_scope_and_shared_implementation():
    from trace_format.calculator import PrintedPointRegistry
    from student_pilot.p3_printed_calculator import PrintedPointRegistry as HeadRegistry
    assert PrintedPointRegistry is HeadRegistry
    a,b=PrintedPointRegistry(),PrintedPointRegistry()
    points=[[0.,0.,0.],[1.,1.,.4],[.3,2.,1.2],[1.4,.5,1.8]]
    for p in points:
        kw=dict(camera=[p[0],p[1],p[2]+2],f1=p,spread=.1,requested_frame=2)
        a.register(**kw);line=b.register(**kw,heading_defined=False)['line']
        assert 'cam2 (' in line and 'spread 0.10' in line
    calls=['<dist P1 P2>','<closest A=P1,P2 B=P3,P4>','<cam_dist P1,P2>',
        '<angle S=P1 F=P2 Q=P3 rule=easy>','<angle S=P1 F=P2 Q=P3 rule=medium>',
        '<angle S=P1 F=P2 Q=P3 rule=hard>','<turn from=P1 at=P2 to=P3>','<area C=P1,P2,P3>']
    records={}
    for call in calls:
        x,y=a.execute(call)['text'],b.execute(call)['text']
        if call.startswith(('<angle ', '<turn ')):
            assert y.startswith('u heading unavailable; v heading unavailable; dot ')
            assert x.split('; dot ',1)[1] == y.split('; dot ',1)[1]
        else:
            assert x==y
        records[call]=dict(defined=x,undefined=y)
    (L/'work/test_artifacts_r6/CALCULATOR_FIELDS_R5.json').write_text(json.dumps(dict(source=__file__,responses=records),indent=2))


def test_ground_box_count_witness_and_keypoints(tmp_path):
    from trace_format.ground_v313 import Session
    from student_pilot import ground_lifting as G
    from student_pilot.live_trace313 import parse_response
    geo=fixture('nadir_positive')[1]();s=session(geo,tmp_path)
    for mode in ('',' mode="instances"',' mode="box"'):
        call='<ground obj="chair"'+mode+'>'
        text=response(s,call);parse_response(call,text,'3.14')
        assert 'heading unavailable' in text
        if mode==' mode="box"':assert 'frames ' in text and 'size ' in text
        else:assert 'cam' in text
    legacy=Session(G,geo,None,instances=lambda n:[],program_version='3.13',keypoint_calls=True)
    legacy.objects={n:G.lift_object(n,masks(n).masks,np.ones(32),geo,tau=.5) for n in ('chair','table')}
    gap=legacy._gap('chair',['table'])
    assert 'nearest point cam' in gap and gap.splitlines()[0].endswith(' m')
    assert gap.count('f1 (heading unavailable,')==2
    p=np.asarray(legacy.objects['chair']['points']['2'])
    positions=[p[0],p[-1]]
    legacy.keypoint_provider=lambda op,names:dict(status='ok',observed_surface_points=True,positions=positions,
        frames=[2,2],distance_m=float(np.linalg.norm(positions[0]-positions[1])))
    text=legacy._keypoints('extent_ends',['chair'])
    assert 'observed endpoint distance ' in text and 'extent start cam2' in text
    (L/'work/test_artifacts_r6/GROUND_FIELDS_R5.json').write_text(json.dumps(dict(source=__file__,gap=gap,extent=text),indent=2))


def test_all_ground_fields_match_defined_computation(tmp_path):
    from fixtures_contracts import CALLS
    from trace_format.ground_v313 import Session
    from student_pilot import ground_lifting as G
    from student_pilot.carrier_c1_decode import ground_text
    geo=fixture('nadir_positive')[1]()
    def mask_heading(text):
        text=re.sub(r'f1 (centre )?\(([^,]+), ([^,]+), ([^)]+)\)',
                    lambda m:'f1 '+(m[1] or '')+'(heading unavailable, '+m[3]+', heading unavailable)',text)
        return re.sub(r'yaw -?\d+ deg \(0 = \+x; positive \+x toward -z about \+y\)', 'yaw heading unavailable',text)
    outputs={}
    for threshold in (.01,.3):
        with contract_epoch(True,heading_plane_min=threshold):
            s=session(geo,tmp_path/str(threshold))
            outputs[threshold]=[response(s,c) for c in CALLS]
            legacy=Session(G,geo,None,instances=lambda n:[],program_version='3.13',keypoint_calls=True)
            legacy.objects={n:G.lift_object(n,masks(n).masks,np.ones(32),geo,tau=.5) for n in ('chair','table')}
            p=[np.asarray(legacy.objects[n]['points']['2']) for n in ('chair','table')]
            # Choose facing surface points; provider validation still checks support and authority.
            a=p[0][np.argmax(p[0][:,0])];b=p[1][np.argmin(p[1][:,0])]
            legacy.keypoint_provider=lambda op,names:dict(status='ok',observed_surface_points=True,positions=[a,b],
                frames=[2,2],distance_m=float(np.linalg.norm(a-b)),true_closest_visible=True,
                full_surface_distance_m=float(np.linalg.norm(a-b)),full_surface_authority='fixture')
            outputs[threshold].append(legacy._keypoints('surface_pair',['chair','table']))
    for defined,partial in zip(outputs[.01],outputs[.3]):
        assert mask_heading(defined)==partial,(defined,partial)
    assert 'full surface gap ' in outputs[.3][-1] and 'support centroid cam2' in outputs[.3][-1]
    prob=[.8]*32;uv=[[500,400]]*32
    with contract_epoch(True,heading_plane_min=.99):text=ground_text('chair',prob,uv,.5)
    with contract_epoch(False):assert ground_text('chair',prob,uv,.5)==text
    (L/'work/test_artifacts_r6/ALL_GROUND_PARITY_R5.json').write_text(json.dumps(dict(source=__file__,defined=outputs[.01],partial=outputs[.3]),indent=2))


def test_vertical_generator_and_off_identity():
    from generator.derivgen_v7.derivgen.ground_v312_io import Frame1GTGeometry
    from student_pilot.carrier_c1_run import identity
    raw=NS(cam=lambda k:(rotations(-90),np.zeros(3)))
    with contract_epoch(True):assert np.array_equal(Frame1GTGeometry(raw).basis,np.eye(3))
    with contract_epoch(False):
        with pytest.raises(ValueError,match='undefined GT level basis'):Frame1GTGeometry(raw)
    assert identity(dict(contract_epoch=False,heading_plane_min=.1))==identity(dict(contract_epoch=False,heading_plane_min=.9))


@pytest.mark.parametrize('camera',[False,True])
def test_partial_ground_training_continues_to_metric(camera,tmp_path):
    from generator.derivgen_v7.derivgen import box_v313 as B
    from student_pilot.training_contract import audit_training_contract
    geo=fixture('nadir_positive')[1]();probe=session(geo,tmp_path/'probe')
    response(probe,'<ground obj="chair" mode="box">')
    if not camera:response(probe,'<ground obj="table" mode="box">')
    call='<gap camera="2" b="chair" rule="box_grid_5cm">' if camera else '<gap a="chair" b="table" rule="box_grid_5cm">'
    text=response(probe,call);target=text.split()[1]
    item=dict(qid='partial-training',type='camera_obj_abs_dist' if camera else 'object_abs_distance',
        roles=dict(frame=2,names=['chair']) if camera else dict(a='chair',b='table'),
        question='How far is the chair from the table?',options=[],gt_answer=target,gt_authority='synthetic',target_distance_rule=B.RULE_GRID)
    s=session(geo,tmp_path/'render')
    row=(B.render_camera if camera else B.render)(item,s,lambda text:len(text.split()))
    assert not row['not_seen'] and row['events'][-1]['call']==call
    row['candidate_phrases']=['chair','table']
    assert audit_training_contract([row])==[None]


def test_multi_box_partial_observations():
    from trace_format.ground_v313 import Session
    from trace_format.box_v313 import split_instances
    from student_pilot.live_trace313 import parse_response
    from student_pilot import ground_lifting as G
    from generator.derivgen_v7.derivgen import box_v313 as B
    geo=fixture('nadir_positive')[1]()
    def make():
        return Session(G,geo,None,program_version='3.14',instances=lambda name:[
            dict(instance_id=str(i),masks=masks(name).masks,prob=np.ones(32)) for i in (1,2)])
    s=make();call='<ground obj="chair" mode="box">';text=s.execute(call)
    assert text.startswith('chair: 2 instances') and len(split_instances(text))==2
    parse_response(call,text,'3.14')
    s.execute('<ground obj="table" mode="box">')
    gap='<gap a="chair" b="table" rule="box_grid_5cm">';value=s.execute(gap).split()[1]
    row=B.render(dict(qid='multi',type='object_abs_distance',roles=dict(a='chair',b='table'),
        question='How far is the chair from the table?',options=[],gt_answer=value,gt_authority='fixture',
        target_distance_rule=B.RULE_GRID),make(),lambda text:len(text.split()))
    assert not row['not_seen'] and row['events'][-1]['call']==gap


def test_relative_gap_fields_and_ties(tmp_path):
    geo=fixture('nadir_positive')[1]()
    bodies={}
    for threshold in (.01,.3):
        with contract_epoch(True,heading_plane_min=threshold):
            s=session(geo,tmp_path/str(threshold),names=('chair','table','lamp'))
            for name in ('chair','table','lamp'):response(s,f'<ground obj="{name}" mode="box">')
            calls=['<gap a="chair" b="table" b="lamp" rule="box_grid_5cm">',
                '<gap camera="2" b="chair" b="table" rule="box_grid_5cm">']
            bodies[threshold]=[response(s,c) for c in calls]
    assert bodies[.01]==bodies[.3]
    assert 'min "table","lamp"' in bodies[.3][0]
    assert all('heading unavailable' not in b for b in bodies[.3])
