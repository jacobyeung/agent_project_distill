"""Replay packed masks through lifting; stored printed results are never the oracle."""
import base64
from dataclasses import asdict
import math
import zlib
import numpy as np
from .ground_lifting import lift_object, render_ground, OwnGeometryAdapter
from .mdg_decode import cached_gap


def pack_array(value):
    a=np.ascontiguousarray(value)
    return dict(shape=list(a.shape),dtype=a.dtype.str,
                data=base64.b64encode(zlib.compress(a.tobytes())).decode('ascii'))


def unpack_array(value):
    return np.frombuffer(zlib.decompress(base64.b64decode(value['data'])),
                         dtype=value['dtype']).reshape(value['shape'])


def geometry_record(geo):
    from .geometry_profiles import ProfileGeometry
    if isinstance(geo,OwnGeometryAdapter):
        return None  # Recorded head/depth queries are replayed by the decoder.
    if not hasattr(geo,'contract'):
        raise ValueError('replay_requires_bound_geometry')
    c=asdict(geo.contract)
    for k in ('K','canvas_to_source','camera_to_world'):
        c[k]=pack_array(c[k])
    if isinstance(geo,ProfileGeometry):
        # Store pre-scale depth; ProfileGeometry owns the one scale operation.
        depth=geo.depth_grid/(geo.contract.scale if geo.contract.profile=='scaled_g3t_depth' else 1.)
        return dict(kind='profile',contract=c,depth=pack_array(depth))
    raw=geo.geometry
    if geo.contract.ground_truth_substitution:
        return dict(kind='gt_native',contract=c,depth=pack_array(raw.depth),
                    valid=np.asarray(raw.valid).tolist(),hw=[raw.H,raw.W])
    return dict(kind='legacy',contract=c,depth=pack_array(raw.grid),fov=pack_array(raw.fov))


def record_mask(masks,prob,tau,geometry):
    masks=np.zeros((32,1,1),bool) if masks is None else np.asarray(masks,bool)
    prob=np.zeros(32) if prob is None else np.asarray(prob)
    return dict(mask_shape=list(masks.shape),mask_bits=np.packbits(masks).tolist(),
                prob=prob.tolist(),tau=float(tau),geometry=geometry_record(geometry) if masks.any() else None)


def restore_geometry(record,own):
    if record is None:
        return own
    from .geometry_profiles import GeometryContract,ProfileGeometry
    from .scene_state import FrameMap
    c=dict(record['contract']);c['frame_map']=FrameMap(**c['frame_map'])
    for k in ('K','canvas_to_source','camera_to_world'):
        c[k]=unpack_array(c[k])
    c=GeometryContract(**c)
    depth=unpack_array(record['depth'])
    if record['kind']=='profile':
        return ProfileGeometry(c,depth)
    if record['kind']=='legacy':
        class Legacy(ProfileGeometry):
            def rays(self,frame,uv):
                fh,fw=unpack_array(record['fov'])[frame-1]
                return np.stack([(uv[:,0]/500-1)*math.tan(fw/2),
                                 (uv[:,1]/500-1)*math.tan(fh/2),np.ones(len(uv))],1)
        return Legacy(c,depth)
    class Native:
        def has(self,k):return bool(record['valid'][k-1])
        def cam(self,k):return c.camera_to_world[k-1,:3,:3],c.camera_to_world[k-1,:3,3]
        def lift(self,k,uv,mode='center'):
            H,W=record['hw'];uv=np.asarray(uv,float)
            def px(uv):
                return np.clip((uv[:,0]/1000*W).astype(int),0,W-1),np.clip((uv[:,1]/1000*H).astype(int),0,H-1)
            offsets=np.array([(dx,dy) for dx in np.linspace(-10,10,5) for dy in np.linspace(-10,10,5)])
            x,y=px(np.clip(uv[:,None]+offsets,0,999.9).reshape(-1,2))
            d=depth[k-1,y,x].astype(float).reshape(len(uv),25);d[d<=0]=np.nan
            p20,p50,p80=np.nanpercentile(d,(20,50,80),axis=1)
            x,y=px(uv);dc=depth[k-1,y,x].astype(float)
            pc=(np.column_stack((x+.5,y+.5,np.ones(len(x)))) @ np.linalg.inv(c.K[k-1]).T)*np.where(dc>0,dc,np.nan)[:,None]
            R,t=self.cam(k)
            return pc@R.T+t,pc,(p80-p20)/np.maximum(p50,1e-3)
    return Native()


class ReplayBackend:
    def __init__(self,queries,geometry,registry):
        self.queries,self.registry=queries,registry
        self.geometry=OwnGeometryAdapter(geometry)
        self.results={}

    def ground(self,name,query=None):
        q=self.queries[name] if query is None else query
        mask=np.unpackbits(np.asarray(q['mask_bits'],np.uint8),count=int(np.prod(q['mask_shape']))).astype(bool).reshape(q['mask_shape'])
        geo=restore_geometry(q.get('geometry'),self.geometry)
        result=lift_object(name,mask,q['prob'],geo,tau=q['tau'])
        self.results[name]=result
        return render_ground(result,self.registry)

    def gap(self,a,b):return cached_gap(self.results,a,b)
