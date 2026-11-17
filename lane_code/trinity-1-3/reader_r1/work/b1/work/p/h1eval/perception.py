"""Own-head perception and interventions before the shared response formatter."""
from dataclasses import dataclass,replace
import math
import time
import numpy as np
from student_pilot.camera_targets import rotation_from_xyzw,quaternion_xyzw,to_gravity_reference_frame
from student_pilot.carrier_c1_routing import OwnGeometry
from e2e_reader.geometry import reader_contract
from e2e_reader.servers import ReadServers

@dataclass(frozen=True)
class Heads:
    pose9: object
    gravity: object
    depth: object
    capture_id: str
    turn_pose9: object = None

    @classmethod
    def prefill(cls,state,capture_id):
        h=state.heads
        return cls(np.asarray(h.pose9).copy(),np.asarray(h.gravity).copy(),h.depth,capture_id)


def axis_rotation(axis,degrees):
    axis=np.asarray(axis,float);axis=axis/np.linalg.norm(axis)
    x,y,z=axis;S=np.array([[0,-z,y],[z,0,-x],[-y,x,0]])
    a=math.radians(degrees)
    return np.eye(3)*math.cos(a)+(1-math.cos(a))*np.outer(axis,axis)+math.sin(a)*S


def perturb(heads, mode=None, *, donor=None, gt=None):
    mode=dict(mode or {'name':'none'});name=mode['name']
    p=np.array(heads.pose9,float,copy=True);up=np.array(heads.gravity,float,copy=True);depth=heads.depth
    turn_pose=None
    record=dict(mode=mode,source_capture=heads.capture_id,changed_fields=[])
    if name in ('scale_translation','scale_scene'):
        k=float(mode['k'])
        if not math.isfinite(k) or k<=0: raise ValueError('scale must be finite and positive')
        p[:,:3]*=k;record['changed_fields'].append('translation')
        if name=='scale_scene':
            depth=lambda f,uv:np.asarray(heads.depth(f,uv))*k
            record['changed_fields'].append('depth')
    elif name=='rotate_translation':
        A=axis_rotation(up,float(mode['deg']))
        for code in p:
            R=rotation_from_xyzw(code[3:7]);centre=-R.T@code[:3];code[:3]=-R@A@centre
        record['changed_fields']=['translation_direction']
    elif name=='negate_turn':
        # Reflect heading about the reference heading, preserving centres and FoV.
        R,t,_=to_gravity_reference_frame(p,up)
        yaw=np.arctan2(R[:,1,2],R[:,0,2]);angles=yaw-yaw[0]
        changed=np.array([axis_rotation([0,0,1],math.degrees(-2*a))@r for a,r in zip(angles,R)])
        for i,code in enumerate(p):
            rel=changed[i].T@changed[0]
            code[:3]=changed[i].T@(t[0]-t[i]);code[3:7]=quaternion_xyzw(rel)
        turn_pose=p; p=np.array(heads.pose9,float,copy=True)
        record['changed_fields']=['turn']
    elif name=='donor':
        if donor is None or donor.capture_id==heads.capture_id: raise ValueError('donor requires another capture')
        p=np.array(donor.pose9,copy=True);up=np.array(donor.gravity,copy=True);depth=donor.depth
        record.update(donor_capture=donor.capture_id,changed_fields=['pose9','gravity','depth'])
    elif name=='gt':
        if not gt or not any(k in gt for k in ('gt_pose9','gt_up','depth')): raise ValueError('gt requires supplied arrays')
        if 'gt_pose9' in gt:p=np.array(gt['gt_pose9'],float,copy=True);record['changed_fields'].append('pose9')
        if 'gt_up' in gt:up=np.array(gt['gt_up'],float,copy=True);record['changed_fields'].append('gravity')
        if 'depth' in gt:depth=gt['depth'];record['changed_fields'].append('depth')
        record['gt_substitution']=True
    elif name!='none':raise ValueError('unknown perturbation: '+name)
    OwnGeometry(p,up,depth)  # existing finite/shape contract, no gravity guard
    return Heads(p,up,depth,heads.capture_id,turn_pose),record


def own_profile(heads, frames, grid_uv=None):
    """Metric VC profile: own depth, own FoV, gravity reference, scale one."""
    from student_pilot.scene_state import FrameMap
    uv=np.linspace(0,1000,51) if grid_uv is None else np.asarray(grid_uv)
    yy,xx=np.meshgrid(uv,uv,indexing='ij');points=np.column_stack([xx.ravel(),yy.ravel()])
    depth=np.stack([heads.depth(k,points).reshape(len(uv),len(uv)) for k in range(1,33)])
    R,t,fov=to_gravity_reference_frame(heads.pose9,heads.gravity)
    H,W=frames['source_hw'];C=np.tile(np.eye(4),(32,1,1));C[:,:3,:3]=R;C[:,:3,3]=t
    K=np.zeros((32,3,3));K[:,0,0]=W/(2*np.tan(fov[:,1]/2));K[:,1,1]=H/(2*np.tan(fov[:,0]/2))
    K[:,0,2]=W/2;K[:,1,2]=H/2;K[:,2,2]=1
    A=np.tile(np.diag([W/1000,H/1000,1.]),(32,1,1))
    indices=frames.get('anchor_indices',list(range(32)))
    def make(GP):
        contract=reader_contract(GP)('legacy_v3122',FrameMap(tuple(indices)),indices[0],K,A,C,1.,
                                     'vc','metric','metric',0,1)
        return GP.ProfileGeometry(contract,depth,uv)
    from student_pilot import geometry_profiles as GP
    return make(GP)


class OwnPerception:
    def __init__(self,socket=None,*,mode=None,donor=None,gt=None,grid_uv=None):
        self.socket=socket;self.mode=mode;self.donor=donor;self.gt=gt;self.grid_uv=grid_uv
        self.last={}

    def lazy(self,frames,prefill_state,timings):
        heads,intervention=perturb(Heads.prefill(prefill_state,str(frames['capture_id'])),self.mode,donor=self.donor,gt=self.gt)
        own=OwnGeometry(heads.pose9,heads.gravity,heads.depth)
        turn=own if heads.turn_pose9 is None else OwnGeometry(heads.turn_pose9,heads.gravity,heads.depth)
        from student_pilot.p3_printed_calculator import PrintedPointRegistry
        registry=PrintedPointRegistry()
        built={'scale':1.,'heads':heads,'intervention':intervention,'frames':frames};self.last=built
        def head(call):
            from student_pilot.carrier_c1_decode import respond
            text,info=respond(call,registry,turn if call.startswith('<turn ') else own)
            return text,{**info,'intervention':intervention,'perception':'own'}
        def ground(call):
            if self.socket is None:
                from e2e_reader.callhook import Unserved
                raise Unserved('ground' if call.startswith('<ground') else 'gap')
            if 'servers' not in built:
                from e2e_reader.grounding import ground_session
                t0=time.perf_counter();geometry=own_profile(heads,frames,self.grid_uv)
                session=ground_session(geometry,self.socket(frames,geometry))
                servers=ReadServers(geometry,session);servers.registry=registry
                built.update(servers=servers,geometry=geometry)
                timings['own_ground_geometry_s']=time.perf_counter()-t0
            text,info=built['servers'].session_call(call)
            return text,{**info,'intervention':intervention,'perception':'own'}
        return {**dict.fromkeys(('move','turn','pose','depth_at','other'),head),**dict.fromkeys(('ground','gap'),ground)},built


def perception(arm,*,artifact=None,device='cpu',socket=None,sam3_tower=None,selector_head=None,scale_head=None,**kw):
    if arm=='tower':
        if kw.get('mode',{}).get('name','none')!='none':raise ValueError('tower arm keeps the existing unperturbed reader path')
        from e2e_reader.real import real_perception
        return real_perception(artifact,device=device,scale_head=scale_head,sam3_tower=sam3_tower,selector_head=selector_head)
    if arm!='own':raise ValueError('arm must be own or tower')
    if socket is None and sam3_tower is not None:
        from e2e_reader.stage1 import stage1_factory
        from e2e_reader.real import anchor_frames
        socket=stage1_factory(sam3_tower,selector_head,anchor_frames)
    return OwnPerception(socket,**kw)
