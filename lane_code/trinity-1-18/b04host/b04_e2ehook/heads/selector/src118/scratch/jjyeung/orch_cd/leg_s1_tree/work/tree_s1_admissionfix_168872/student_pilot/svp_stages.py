"""Presence, visible-surface propagation and a bounded second proposal pass.

Each pass has 32 one-based slots. Rescue images have their own source indices,
but share the primary geometry's world reference. Only primary slots print.
"""
from dataclasses import dataclass
import numpy as np


def footprint(points, geometry, frame, shape=(80,112), *, relative=.05, absolute=.03):
    """Project a metric world surface, splat one pixel and test target depth."""
    h,w=shape
    R,t=geometry.cam(frame)
    camera=(np.asarray(points,float)-t)@R
    camera=camera[np.isfinite(camera).all(1)&(camera[:,2]>0)]
    result=np.zeros(shape,bool)
    if not len(camera):return result
    contract=geometry.contract
    K=np.linalg.inv(contract.canvas_to_source[frame-1])@contract.K[frame-1]
    pixels=camera@K.T;uv=pixels[:,:2]/pixels[:,2,None]
    valid=((uv>=0)&(uv<1000)).all(1)
    uv,z=uv[valid],camera[valid,2]
    if not len(z):return result
    xy=np.floor(uv*np.array([w,h])/1000).astype(int)
    zbuffer=np.full(h*w,np.inf)
    for dx in (-1,0,1):
        for dy in (-1,0,1):
            x,y=xy[:,0]+dx,xy[:,1]+dy
            keep=(x>=0)&(x<w)&(y>=0)&(y<h)
            np.minimum.at(zbuffer,y[keep]*w+x[keep],z[keep])
    ids=np.flatnonzero(np.isfinite(zbuffer));y,x=np.divmod(ids,w)
    target_uv=np.column_stack(((x+.5)/w*1000,(y+.5)/h*1000))
    depth=geometry.depth(frame,target_uv) if hasattr(geometry,'depth') else geometry._depth(frame-1,target_uv[:,0],target_uv[:,1])
    good=np.isfinite(depth)&(depth>0)&(np.abs(zbuffer[ids]-depth)<=np.maximum(absolute,relative*depth))
    result.ravel()[ids[good]]=True
    return result


def propagate(candidate, geometry, proposals, *, sam, relative=.05, absolute=.03, iou=.3):
    """SAM keeps its matching proposal; the own branch keeps the footprint."""
    points=np.concatenate([p.points for p in candidate.proposals])
    masks=np.zeros((32,80,112),bool)
    for frame in range(1,33):
        if not geometry.has(frame):continue
        projected=footprint(points,geometry,frame,relative=relative,absolute=absolute)
        if not sam:
            masks[frame-1]=projected
            continue
        ranked=[]
        for p in proposals:
            if p.frame!=frame:continue
            if p.mask.shape!=projected.shape:raise ValueError('propagation_requires_ofs_mask_shape')
            overlap=np.count_nonzero(projected&p.mask)/max(1,np.count_nonzero(projected|p.mask))
            ranked.append((overlap,p.joint,-p.index,p))
        if ranked:
            best=max(ranked,key=lambda x:x[:3])
            if best[0]>=iou:masks[frame-1]=best[3].mask
    return masks,masks.any(axis=(1,2)).astype(float)


class NativePresence:
    """MDG's frame head queried on an isolated prompt, without a label gate."""
    def __init__(self,identity):
        if not identity:raise ValueError('presence_artifact_identity_required')
        self.identity=identity;self.backend=None

    def bind_native_backend(self,backend):
        if backend is None:raise ValueError('presence_requires_attached_mdg_head')
        self.backend=backend

    def __call__(self,name,frame_map):
        from .mdg_decode import predict
        b=self.backend
        if b is None:raise ValueError('presence_requires_generate_binding')
        frame_map.require(b.batch['frame_indices'])
        states=b.query(name,allow_unknown=True)
        values,b.memory=predict(b.head,b.prefix,states,b.memory)
        return np.asarray(values['frame_prob'][0],float)


@dataclass(frozen=True)
class RescuePass:
    geometry: object
    source: object
    frame_map: object
    frames: dict
    world_reference: str
    presence: object = None

    def validate(self,primary,world_reference):
        primary.require(primary.source_indices)
        self.frame_map.require(self.geometry.frame_map.source_indices)
        self.frame_map.require(self.source.frame_indices)
        if set(primary.source_indices)&set(self.frame_map.source_indices):
            raise ValueError('rescue_requires_the_other_32_source_frames')
        if not world_reference or world_reference!=self.world_reference:
            raise ValueError('rescue_requires_shared_world_reference')
        if len(self.frames)!=32 or not self.frame_map.rgb_sha256:
            raise ValueError('rescue_requires_32_hashed_rgb_frames')
        if primary.dense_indices and set(primary.dense_indices)!=set(primary.source_indices+self.frame_map.source_indices):
            raise ValueError('rescue_must_complete_the_64_frame_map')


class SVPStages:
    def __init__(self,*,presence=None,presence_threshold=.5,rescue=None,
                 world_reference='',propagation=True,relative_depth=.05,absolute_depth=.03):
        if not 0<=presence_threshold<=1 or relative_depth<0 or absolute_depth<0:
            raise ValueError('invalid_svp_threshold')
        if presence is not None and not getattr(presence,'identity',None):
            raise ValueError('presence_identity_required')
        if rescue is not None and not propagation:
            raise ValueError('rescue_requires_propagation')
        self.presence,self.rescue=presence,rescue
        self.threshold,self.world_reference=presence_threshold,world_reference
        self.propagation,self.relative_depth,self.absolute_depth=propagation,relative_depth,absolute_depth

    def config(self):
        r=self.rescue
        return dict(presence=getattr(self.presence,'identity',None),presence_threshold=self.threshold,
            propagation=self.propagation,relative_depth=self.relative_depth,absolute_depth=self.absolute_depth,
            world_reference=self.world_reference,rescue=None if r is None else dict(source=r.source.identity,
            geometry=r.geometry.identity,frames=r.frame_map.source_indices,rgb=r.frame_map.rgb_sha256,
            presence=getattr(r.presence,'identity',None)))

    def prior(self,name,frame_map,provider=None):
        provider=self.presence if provider is None else provider
        if provider is None:return None
        p=np.asarray(provider(name,frame_map),float)
        if p.shape!=(32,) or not np.isfinite(p).all() or np.any((p<0)|(p>1)):
            raise ValueError('presence_requires_32_probabilities')
        return p

    def visible(self,candidate,prior):
        proposals=[p for p in candidate.proposals if prior is None or prior[p.frame-1]>=self.threshold]
        return min(proposals,key=lambda p:(-p.joint,p.frame,p.index)) if proposals else None

    def propagate(self,candidate,geometry,proposals,*,sam):
        return propagate(candidate,geometry,proposals,sam=sam,relative=self.relative_depth,absolute=self.absolute_depth)
