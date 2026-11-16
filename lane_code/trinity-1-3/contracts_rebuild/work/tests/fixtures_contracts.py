from pathlib import Path
from types import SimpleNamespace as NS
import numpy as np
L=Path(__file__).resolve().parents[2]

def rotations(pitch=0., roll=0.):
    p,r=np.radians([pitch,roll])
    base=np.array([[1.,0,0],[0,0,1],[0,-1,0]])
    rx=np.array([[1,0,0],[0,np.cos(p),-np.sin(p)],[0,np.sin(p),np.cos(p)]])
    rz=np.array([[np.cos(r),-np.sin(r),0],[np.sin(r),np.cos(r),0],[0,0,1]])
    return base@rx@rz

def fixture(kind='landscape'):
    from student_pilot.geometry_profiles import GeometryContract, ProfileGeometry
    from student_pilot.scene_state import FrameMap
    h,w=(640,480) if 'portrait' in kind else (480,640)
    C=np.repeat(np.eye(4)[None],32,axis=0)
    C[:,:3,:3]=rotations()
    C[:,0,3]=np.arange(32)%4*.02
    C[:,1,3]=np.arange(32)*.015
    if kind in ('nadir','nadir_positive'):
        C[0,:3,:3]=rotations(-88,180 if kind=='nadir' else 0)
    if kind=='vertical': C[0,:3,:3]=rotations(-90)
    if kind.startswith('inverted'): C[:,:3,:3]=rotations(0,180)
    if kind=='rolled': C[:,:3,:3]=rotations(0,90)
    K=np.repeat(np.array([[w*.8,0,w/2],[0,h*.8,h/2],[0,0,1.]])[None],32,axis=0)
    A=np.repeat(np.diag([w/1000,h/1000,1.])[None],32,axis=0)
    contract=GeometryContract('legacy_v3122',FrameMap(tuple(range(32))),0,K,A,C,1.,'vc','metric','metric',0,1)
    y,x=np.indices((11,11))
    depth=np.repeat((2.+.15*x/10+.05*(y/10)**2)[None],32,axis=0)
    return contract, lambda:ProfileGeometry(contract,depth)

def masks(name, small=False):
    from student_pilot.ground_sources import MaskBatch
    a=np.zeros((32,24,32),bool)
    x=4 if name in ('chair','refrigerator','microwave','table lamp','trash can') else 20
    if small: a[1,10:13,x:x+3]=True
    else: a[1:5,7:18,x:x+8]=True
    return MaskBatch(a,np.ones(32),tuple(range(32)))

def session(geo,root, *, small=False, policy=False, names=('chair','table')):
    from student_pilot.ground_sources import MaskProvider
    from student_pilot.ground_v3 import GroundV3
    from student_pilot.scene_state import SceneState
    from student_pilot.live_trace313 import LiveSession
    from student_pilot.s1_grounding import default_policy
    source=MaskProvider(lambda name:masks(name,small),'synthetic-rgb-mask-fixture',names)
    owner=GroundV3(SceneState('a'*64,geo.frame_map,geo.identity),geo,source,
        mask_source='mdg',audit_dir=root,ground_candidate_policy=default_policy() if policy else None,
        question_type='object_abs_distance' if policy else None)
    s=LiveSession(owner,program_version='3.14')
    s.bind_state(NS(verify_session=None))
    return s

def response(s,call):
    from student_pilot import trace_format313
    from student_pilot.carrier_c1_decode import respond_state
    token=trace_format313._current.set(s)
    try:
        value,info=respond_state(s.state,call,s.registry)
        assert isinstance(value,str)
        return value
    finally: trace_format313._current.reset(token)

CALLS=['<ground obj="chair" mode="box">','<ground obj="table" mode="box">',
       '<gap a="chair" b="table" rule="box_grid_5cm">',
       '<gap camera="2" b="chair" rule="box_grid_5cm">',
       '<ground obj="chair">','<ground obj="chair" mode="instances">','<ground mode="room">']
