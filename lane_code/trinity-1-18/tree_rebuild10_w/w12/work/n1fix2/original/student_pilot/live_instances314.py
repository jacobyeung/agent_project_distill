"""Resolve all live detections, retain exact frame support, and record replay inputs."""
from copy import deepcopy
import numpy as np
from trace_format.ground_v313 import MergedInstances, connected_components
from . import ground_lifting as lifting
from .ground_replay import record_mask, geometry_record, pack_array, unpack_array, restore_geometry
from .scene_state import normalize_name
from trace_format.contracts import new_contracts, geometry_mode


class ExactFrames:
    """Mask lifting requires depth at that exact slot; camera gaps need pose only."""
    def __init__(self, geometry, frames=None):
        self.geometry=geometry
        if frames is None:
            raw=getattr(geometry,'geometry',geometry)
            anchors=getattr(raw,'anchors',None)
            effective=getattr(raw,'effective',getattr(raw,'frame_of',lambda k:k))
            frames=[k for k in range(1,33)
                    if getattr(geometry,'has',lambda _:True)(k)
                    and (anchors is None or k in anchors) and effective(k)==k]
        self.frames=tuple(frames)
    def has(self,k):return k in self.frames
    def has_pose(self,k):
        if not 1<=k<=32:return False
        raw=getattr(self.geometry,'geometry',self.geometry)
        try:
            if hasattr(raw,'effective') and raw.effective(k,pose=True)!=k:return False
            if hasattr(raw,'frame_of') and raw.frame_of(k)!=k:return False
            self.geometry.cam(k)
            return True
        except (ValueError,KeyError,IndexError):return False
    def lift(self,k,*args,**kwargs):
        if not self.has(k):
            from trace_format.program_errors import ProgramRefusal
            raise ProgramRefusal('exact_depth_frame_unavailable')
        result=self.geometry.lift(k,*args,**kwargs)
        grid=getattr(self.geometry,'grids',{}).get(k)
        if grid is not None and not np.isfinite(grid).all():
            from trace_format.program_errors import ProgramRefusal
            raise ProgramRefusal('nonfinite_depth_grid')
        return result
    def __getattr__(self,key):return getattr(self.geometry,key)


def record_geometry(geo):
    if not isinstance(geo,lifting.OwnGeometryAdapter):return geometry_record(geo)
    raw=geo.geometry
    if not hasattr(raw,'p'):raise ValueError('v314_own_geometry_requires_per_frame_codes')
    return dict(kind='v314_own',pose9=pack_array(raw.p),up=(-raw.down).tolist(),
                fov=None if raw.fov_override is None else pack_array(raw.fov_override),
                grids={str(k):pack_array(v) for k,v in geo.grids.items()})


def restore_recorded_geometry(record):
    if record is None or record.get('kind')!='v314_own':return restore_geometry(record,None)
    from .carrier_c1_routing import OwnGeometry
    def forbidden(*args):raise ValueError('replay_missing_depth_grid')
    raw=OwnGeometry(unpack_array(record['pose9']),record['up'],forbidden,
                    fov=None if record['fov'] is None else unpack_array(record['fov']))
    geo=lifting.OwnGeometryAdapter(raw)
    geo.grids={int(k):unpack_array(v) for k,v in record['grids'].items()}
    return geo


def unpack_mask(item):
    return np.unpackbits(np.asarray(item['mask_bits'],np.uint8),
        count=int(np.prod(item['mask_shape']))).astype(bool).reshape(item['mask_shape'])


def relift_instances(query, geometry):
    geometry=ExactFrames(geometry,query['exact_frames'])
    return [dict(item, result=bridge_cut(lifting.lift_object(query['name'],unpack_mask(item),
        item['prob'],geometry,tau=item['tau'],
        depth_cut=item.get('depth_cut',query.get('geometry_mode','sensor')=='predicted')), item, query.get('contract_epoch',False))) for item in query['instances']]


def bridge_cut(obj, entry, enabled):
    if enabled and entry.get('depth_cut_applied', False):
        obj['points_cut'] = obj['points']
    return obj


def components(owner, name):
    """Read the provider before singular selection. SAM candidates are already gated."""
    source=owner.source
    if hasattr(owner,'geometry_error') and owner.geometry_error:
        raise ValueError('live_ground_invalid_geometry')
    if hasattr(source,'frame_indices'):
        owner.scene.frames.require(source.frame_indices)
    if hasattr(source,'selector_candidates'):
        frames=[[] for _ in range(32)]
        for c in source.selector_candidates(name):
            if not 1<=c.frame<=32:raise ValueError('invalid_detection_frame')
            frames[c.frame-1].append(np.asarray(c.mask,bool))
        return frames
    if hasattr(source,'proposals_for'):
        from .ground_sources import native_gate
        proposals,_=source.proposals_for(name,owner.geometry,owner.selector,owner.grids)
        frames=[[] for _ in range(32)]
        for p in sorted(native_gate(proposals),key=lambda p:(p.frame,p.index)):
            frames[p.frame-1].append(np.asarray(p.mask,bool))
        return frames
    batch=source.masks_for(name)
    owner.scene.frames.require(batch.frame_indices)
    if batch.state is not None:
        if str(batch.state).lower() in ('not_seen','state.not_seen'):return [[] for _ in range(32)]
        raise ValueError('v314_unresolved_mask_source')
    # Preserve the provider's gate before splitting category masks.
    prob=np.where(np.asarray(batch.probabilities)>=batch.tau,1.,0.)
    return connected_components(lambda _: (batch.masks,prob))(name)


def query_instances(owner, name, state):
    canonical=normalize_name(name)
    session=state.live_trace_session
    cache=getattr(session,'instance_cache',{})
    session.instance_cache=cache
    if canonical in cache:
        query=dict(deepcopy(cache[canonical]),memory_hit=True,name=name)
        for item in query['instances']:item['result']['name']=name
        session.geometry=ExactFrames(owner.geometry,query['exact_frames'])
        return query
    geo=ExactFrames(owner.geometry)
    session.geometry=geo
    policy_audit = None
    if getattr(owner, 'candidate_policy', None) is not None:
        from .routed_features import select_instances
        if state.verify_session is not None:
            raise ValueError('Routed default forbids an additional unpriced verifier')
        if getattr(owner, '_routed_session', None) is not session:
            owner._routed_session = session
            owner._routed_candidate_cache = None
        raw, policy_audit = select_instances(owner, canonical, geo)
    else:
        detections=components(owner,canonical)
        from trace_format.instance_policy314 import valid_mask
        from trace_format.program_errors import ProgramRefusal
        if any(any(valid_mask(m) for m in dets) and not geo.has(k) for k,dets in enumerate(detections,1)):
            raise ProgramRefusal('exact_depth_frame_unavailable')
        raw=MergedInstances(lifting,geo,lambda n:detections)(canonical)
    lifted=[]
    for entry in raw:
        cut = geometry_mode(session)=='predicted' and not entry.get('depth_cut_applied',False)
        obj=lifting.lift_object(name,entry['masks'],entry['prob'],geo,tau=.5,
                                depth_cut=cut)
        bridge_cut(obj, entry, getattr(session, 'contract_epoch', new_contracts()))
        if obj['seen']:lifted.append((dict(entry,lifting_depth_cut=cut),obj))
    verification=None
    verifier=state.verify_session
    if verifier is not None:
        from .verify_pass import verify_pass, native_view
        context=state.tool_context
        candidates=[]
        for entry,obj in lifted:
            k=obj['best']
            candidates.append(dict(candidate_id=entry['instance_id'],slot=k,mask=entry['masks'][k-1],
                source_index=context.frame_map.source_indices[k-1],rgb_sha256=context.frame_map.rgb_sha256[k-1]))
        request=dict(name=name,forms=('V1',),candidates=candidates,frames=context.frames,
                     frame_map=context.frame_map,context=context)
        if getattr(verifier,'native',None) is None:verifier.native=native_view(verifier.model)
        verification=verify_pass(verifier.native,verifier.processor,request,budget=verifier.budget,
                                 max_candidates=max(20,len(candidates)))
        if verification['status'] not in ('ok','empty'):
            raise ValueError('live_verification_error:'+verification['status'])
        scores={r['candidate_id']:r['p_yes'] for r in verification['rows'] if r['form']=='V1'}
        if any(not np.isfinite(p) or not 0<=p<=1 for p in scores.values()):
            raise ValueError('invalid_verify_probability')
        lifted=[(e,o) for e,o in lifted if scores.get(e['instance_id'],0.)>=owner.config['verify_threshold']]
    items=[]
    for entry,obj in lifted:
        packed=record_mask(entry['masks'],entry['prob'],.5,owner.geometry)
        packed.pop('geometry',None)
        items.append(dict(instance_id=entry['instance_id'],result=obj,
                          depth_cut=entry['lifting_depth_cut'],
                          depth_cut_applied=entry.get('depth_cut_applied',False),**packed))
    query=dict(name=name,backend='ground_v314',state='resolved' if items else 'not_seen',
               instances=items,geometry=record_geometry(owner.geometry),memory_hit=False,
               geometry_source=getattr(owner,'geometry_source','configured'),
               merge_rule=policy_audit['policy'] if policy_audit else MergedInstances.rule,
               candidate_policy=policy_audit,verification=verification,exact_frames=list(geo.frames))
    cache[canonical]=deepcopy(query)
    return query
