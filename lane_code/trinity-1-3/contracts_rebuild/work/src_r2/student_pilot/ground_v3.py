"""Mask-source switch, per-clip memory and unchanged v3.12.2 rendering."""
from copy import deepcopy, copy
import json
from pathlib import Path
import uuid
import numpy as np
from .ground_lifting import lift_object, render_ground, render_gap, render_gaps
from .geometry_profiles import GeometryError, profile
from .object_memory import ClipMemory, ObjectSlot, State
from .scene_state import digest, normalize_name
from .ground_sources import VerifyStub

MASK_SOURCES = ('gt', 'mdg', 'svp_sam3', 'svp_own')


def same_object(a, b):
    """Match claims by metric geometry; local candidate IDs are name-dependent."""
    # Linking peels a second same-frame piece into a separate candidate. Keep
    # its cross-view edges when comparing identities after that peel.
    for p in a.proposals:
        for q in b.proposals:
            if p.frame != q.frame:
                radius=max(.30,.5*min(p.extent,q.extent))+.025*(p.depth+q.depth)
                overlap=len(p.voxels & q.voxels)/max(1,min(len(p.voxels),len(q.voxels)))
                if np.linalg.norm(p.center-q.center)<=radius or overlap>=.25:
                    return True
    av, bv = a.voxels, b.voxels
    overlap = len(av & bv)/max(1,min(len(av),len(bv)))
    extent = min(np.median([p.extent for p in a.proposals]), np.median([p.extent for p in b.proposals]))
    depth = np.mean([p.depth for p in a.proposals+b.proposals])
    return np.linalg.norm(a.center-b.center) <= max(.30,.5*extent)+.05*depth or overlap >= .25


class GroundV3:
    def __init__(self, scene, geometry, source, *, mask_source='gt', memory=None,
                 selector=None, verify=None, audit_dir, geometry_profile='legacy_v3122',
                 rule='native_selector', threshold=0., verify_threshold=.5,
                 ambiguity_margin=None, weights=None, selector_identity=None, stages=None,
                 ground_candidate_policy=None, question_type=None):
        if mask_source not in MASK_SOURCES:
            raise ValueError('unknown_mask_source')
        if rule not in ('native_selector','seed','seed_excl_fwd','fused'):
            raise ValueError('online_rule_requires_forward_or_independent_selection')
        if not 0 <= threshold <= 1 or not 0 <= verify_threshold <= 1:
            raise ValueError('invalid_selection_threshold')
        if ambiguity_margin is not None:
            raise ValueError('ambiguity_margin_removed_split_object_abstention')
        if not getattr(source,'identity',None):
            raise ValueError('source_identity_required')
        if mask_source.startswith('svp') and (selector is None or not selector_identity):
            raise ValueError('svp_requires_pinned_selector')
        self.scene, self.geometry = scene, geometry
        self.source=copy(source) if hasattr(source,'bind_native_backend') else source
        self.mask_source, self.selector = mask_source, selector
        from .svp_stages import SVPStages
        self.stages=copy(stages) if stages is not None else SVPStages()
        if hasattr(self.stages.presence,'bind_native_backend'):
            self.stages.presence=copy(self.stages.presence)
        if self.stages.rescue is not None:
            if not self.stages.propagation:
                raise ValueError('rescue_requires_propagation')
            self.stages.rescue.validate(scene.frames,self.stages.world_reference)
        self.rescue_backend=None
        self.verify = verify if verify is not None else VerifyStub()
        if not getattr(self.verify,'identity',None):
            raise ValueError('verify_identity_required')
        self.config = dict(mask_source=mask_source, geometry_profile=geometry_profile,
            source=source.identity, geometry=scene.geometry_identity, frames=scene.frames.source_indices,
            rule=rule, threshold=threshold, verify=self.verify.identity, verify_threshold=verify_threshold,
            ambiguity_margin=ambiguity_margin, weights=weights, selector=selector_identity)
        from trace_format.contracts import new_contracts, heading_plane_min
        from .phrases import phrase_set
        self.contract_epoch = new_contracts()
        self.heading_plane_min = heading_plane_min()
        names = getattr(source, 'cache', {}).get('phrases', getattr(source,'names',()))
        self.config['candidate_universe'] = list(phrase_set(names)) if self.contract_epoch else sorted(getattr(source,'names',()))
        if self.contract_epoch:
            self.config['contract_epoch'] = True
            self.config['heading_plane_min'] = self.heading_plane_min
        self.candidate_policy = None
        if ground_candidate_policy is not None:
            from .candidate_policy import Policy
            if not question_type:
                raise ValueError('Routed policy requires a question type')
            self.candidate_policy = Policy(ground_candidate_policy, question_type)
            self.config['ground_candidate_policy'] = ground_candidate_policy
            self.config['question_type'] = question_type
        if rule == 'fused' and weights and weights.get('exclusivity_margin') and not self.config['candidate_universe']:
            raise ValueError('exclusivity_feature_requires_fixed_competitor_universe')
        self.config['stages']=self.stages.config()
        self.config['proposal_gate'] = dict(joint_strict_gt=.5, retained_score_floor=.3)
        self.config_hash = digest(self.config)
        self.geometry_error = None
        try:
            profile(geometry_profile)
            if geometry is None:
                raise GeometryError('geometry_missing')
            geometry.contract.validate()
            if geometry.contract.profile != geometry_profile or geometry.identity != scene.geometry_identity:
                raise GeometryError('geometry_identity_mismatch')
            scene.frames.require(geometry.frame_map.source_indices)
        except (GeometryError,ValueError,AttributeError) as exc:
            self.geometry_error = str(exc)
        self.memory = memory if memory is not None else ClipMemory()
        self.memory.bind(scene)
        self.audit_dir = Path(audit_dir)
        self.audit_dir.mkdir(parents=True, exist_ok=True)
        self.session = uuid.uuid4().hex
        self.calls = 0
        self.results, self.queries, self.gap_queries, self.query_passes = {}, [], [], []
        self.grids = None
        self.candidate_cache = {}
        self.claims, self.question_slots = {}, {}

    def _memory_entry(self, name):
        primary = self.memory.get(name,self.config_hash,scene=self.scene)
        rescue = self.memory.get(name,self.config_hash+':rescue',scene=self.scene)
        return rescue if rescue is not None else primary

    def _claims_enabled(self):
        return self.config['rule'] in ('seed_excl_fwd','fused')

    def _miss(self, name, state, reason, **kw):
        return ObjectSlot(name, State(state), reason, dict(name=name,seen=False), **kw).finalize()

    def _resolve(self, name):
        if self.geometry_error:
            return self._miss(name, State.INVALID_GEOMETRY,self.geometry_error)
        if not self.mask_source.startswith('svp'):
            batch = self.source.masks_for(name)
            self.scene.frames.require(batch.frame_indices)
            if batch.state is not None:
                state=State(batch.state)
                if state==State.RESOLVED:
                    raise ValueError('providers_cannot_predeclare_resolved_geometry')
                return self._miss(name,state,batch.reason,masks=batch.masks)
            result = lift_object(name,batch.masks,batch.probabilities,self.geometry,tau=batch.tau)
            return ObjectSlot(name,State.RESOLVED if result['seen'] else State.NOT_SEEN,
                'accepted' if result['seen'] else batch.reason,result,masks=np.array(batch.masks,copy=True),
                verdict=dict(source=self.mask_source),probabilities=np.array(batch.probabilities,copy=True),tau=batch.tau).finalize()
        self.scene.frames.require(self.source.frame_indices)
        O = self.selector
        if self.config['rule'] == 'native_selector':
            from .native_selection import select
            candidates, values, selection, primary = select(name,self.source,self.geometry,O,self.grids)
            prior = self.stages.prior(name,self.scene.frames)
            for c in candidates:
                best = self.stages.visible(c,prior)
                c.features['presence'] = float(prior[best.frame-1]) if prior is not None and best is not None else 1.
            verdict = self.verify(name,candidates)
            if set(verdict) != {c.id for c in candidates} or any(
                    not np.isfinite(p) or not 0 <= p <= 1 for p in verdict.values()):
                raise ValueError('verify_result_mismatch')
            from ofs.core import candidate_json
            return dict(name=name,candidates=candidates,summaries=[candidate_json(c) for c in candidates],
                verdict=verdict,prior=prior,native_values=values,
                primary_proposals=primary,
                audit=dict(p_yes=verdict,stubbed=bool(getattr(self.verify,'stubbed',False)),
                           selection=selection,source_provenance=getattr(self.source,'provenance','unspecified')))
        if self.grids is None:
            from importlib import import_module
            self.grids = import_module(O.__name__+'.core').lift_grid(self.geometry)
        universe = self.config['candidate_universe']
        def build(names,competitors=None):
            by_name=deepcopy(competitors or {});rejections={}
            for n in names:
                proposals,rejections[n]=self.source.proposals_for(n,self.geometry,O,self.grids)
                from .ground_sources import native_gate
                proposals=native_gate(proposals)
                proposals=sorted(proposals,key=lambda p:(p.frame,p.index))
                if len({(p.frame,p.index) for p in proposals})!=len(proposals):
                    raise ValueError('duplicate_proposal')
                by_name[n]=O.link(proposals,name=n)
            O.scene_candidates(by_name,self.geometry)
            return {n:(by_name[n],rejections[n]) for n in names}
        if universe and any(n not in self.candidate_cache for n in universe):
            self.candidate_cache.update(build(universe))
        if name not in self.candidate_cache:
            # Unknown names are queried against fixed competitors. They cannot
            # change the cached rankings of other names in later questions.
            competitors={n:self.candidate_cache[n][0] for n in universe}
            self.candidate_cache.update(build([name],competitors))
        candidates,rejected = self.candidate_cache[name]
        candidates=deepcopy(candidates)
        prior=self.stages.prior(name,self.scene.frames)
        for c in candidates:
            best=self.stages.visible(c,prior)
            c.features['presence']=float(prior[best.frame-1]) if prior is not None and best is not None else 0. if prior is not None else 1.
        verdict = self.verify(name,candidates)
        if set(verdict) != {c.id for c in candidates} or any(
                not np.isfinite(p) or not 0 <= p <= 1 for p in verdict.values()):
            raise ValueError('verify_result_mismatch')
        candidates=sorted(candidates,key=lambda c:(-self._score(c,verdict),c.id))
        from importlib import import_module
        serialize = import_module(O.__name__+'.core').candidate_json
        summaries = [serialize(c) for c in candidates]
        audit_verdict = dict(p_yes=verdict,stubbed=bool(getattr(self.verify,'stubbed',False)),
                             presence_available=prior is not None,presence_source=getattr(self.stages.presence,'identity',None),
                             rejected_proposals=rejected,source_provenance=getattr(self.source,'provenance','unspecified'))
        return dict(name=name,candidates=candidates,summaries=summaries,verdict=verdict,audit=audit_verdict,prior=prior,
                    primary_proposals=[p for c in candidates for p in c.proposals])

    def _score(self,candidate,verdict):
        if self.config['rule']!='fused':return candidate.features['peak']
        from scipy.special import expit
        x=dict(candidate.features,p_yes=verdict[candidate.id]);w=self.config['weights']
        return float(expit(w.get('intercept',0.)+sum(v*x[k] for k,v in w.items() if k!='intercept')))

    def _select(self, name, entry):
        if isinstance(entry,ObjectSlot):
            return entry
        candidates,summaries,verdict = entry['candidates'],entry['summaries'],entry['verdict']
        audit_verdict = deepcopy(entry['audit'])
        universe = self.config['candidate_universe']
        O = self.selector
        claimed = self.claims if self._claims_enabled() else {}
        blocked = {c.id:owner for c in candidates for owner,other in claimed.items()
                   if owner != name and ((not entry.get('rescue') and name in universe and owner in universe and c.slot==other.slot) or
                       ((entry.get('rescue') or not (name in universe and owner in universe)) and same_object(c,other)))}
        audit_verdict['blocked_by'] = blocked
        eligible = [c for c in candidates if c.id not in blocked and verdict[c.id]>=self.config['verify_threshold']
            and self.stages.visible(c,entry.get('prior')) is not None
            and (entry.get('verified_ids') is None or c.id in entry['verified_ids'])]
        rule = self.config['rule']
        external = {cid:dict(p_yes=p) for cid,p in verdict.items()}
        selected = (eligible[0] if eligible else None) if rule == 'native_selector' else O.select(
            {name:eligible},rule=rule,threshold=self.config['threshold'],
            external=external,weights=self.config['weights'])[name]
        if selected is None:
            reason = 'exclusivity_conflict' if blocked else 'verify_rejected' if candidates and not eligible else 'below_threshold' if candidates else 'no_candidates'
            from ofs.core import empty_values
            return self._miss(name,State.AMBIGUOUS if blocked else State.NOT_SEEN,reason,
                              candidates=summaries,verdict=audit_verdict,values=empty_values(1))
        values = deepcopy(entry['native_values']) if rule == 'native_selector' else O.values_for([name],{name:selected})
        if self.stages.propagation and entry.get('verified_by') and (rule != 'native_selector' or entry.get('rescue')):
            proposals=entry['primary_proposals']
            if rule == 'native_selector':
                from .ground_lifting import mask_pixels
                selected=deepcopy(selected)
                for p in selected.proposals:
                    p.points=self.stages.rescue.geometry.lift(p.frame,mask_pixels(p.mask),mode='center')[0]
            masks,prob=self.stages.propagate(selected,self.geometry,proposals,sam=self.mask_source=='svp_sam3')
            values['mask'][0],values['prob'][0]=masks,prob
            audit_verdict['propagation']='depth_tested_primary_slots'
        result = lift_object(name,values['mask'][0],values['prob'][0],self.geometry,tau=.5)
        return ObjectSlot(name,State.RESOLVED if result['seen'] else State.INVALID_GEOMETRY,
            'accepted' if result['seen'] else 'selected_mask_cannot_lift',result,candidates=summaries,
            features=deepcopy(selected.features),verdict=audit_verdict,masks=values['mask'][0],
            candidate=selected,probabilities=values['prob'][0],tau=.5,values=values).finalize()

    def query(self, name):
        return None  # Providers own isolated queries; main trace states never enter memory.

    def begin_question(self):
        """Keep clip memory, but isolate gap admission and decode records per question."""
        if getattr(self, 'geometry_source', None) == 'same_checkpoint_own':
            self.geometry = None
            self.geometry_error = 'geometry_missing'
        self.claims.clear()
        self.question_slots.clear()
        self.results.clear()
        self.queries.clear()
        self.gap_queries.clear()
        self.query_passes.clear()
        self.pending_verify = {}
        self.rescue_attempted=set()

    def ground(self, name, states=None, registry=None):
        if registry is None:
            registry = states
        from .carrier_c1_decode import CallError
        try:
            canonical = normalize_name(name)
        except ValueError as exc:
            raise CallError('bad_object') from exc
        slot = self.question_slots.get(canonical)
        hit = slot is not None
        if slot is None:
            entry = self._memory_entry(canonical)
            hit = entry is not None
            try:
                if entry is None:
                    entry = self._resolve(canonical)
                    self.memory.put(canonical,self.config_hash,entry,scene=self.scene)
                slot = self._select(canonical,entry)
                self.question_slots[canonical] = slot
                if self._claims_enabled() and slot.candidate is not None and slot.state == State.RESOLVED:
                    self.claims[canonical] = slot.candidate
            except Exception as exc:
                # Operational errors are audit events, never clip observations.
                import torch
                if isinstance(exc,torch.cuda.OutOfMemoryError):
                    raise
                self.candidate_cache.pop(canonical,None)
                slot = self._miss(canonical,State.INVALID_GEOMETRY,str(exc))
        return self._emit(name,canonical,slot,registry,hit)

    def _emit(self,name,canonical,slot,registry,hit=False):
        native=getattr(self.source,'backend',None)
        if native is not None:
            self.query_passes[:]=deepcopy(native.query_passes)
        result = deepcopy(slot.result)
        result['name'] = name  # Literal spelling belongs to each call, not the cache key.
        self.results[name] = result
        text = render_ground(result,registry)
        self.calls += 1
        audit = dict(schema='ground-v3-call-v1',call=self.calls,video_sha256=self.scene.video_sha256,
            name=name,normalized_name=canonical,config_hash=self.config_hash,config=self.config,
            memory_hit=hit,state=slot.state.value,reason=slot.reason,candidates=slot.candidates,
            features=slot.features,verdict=slot.verdict,frames=list(slot.frames),response=text,
            point_count=len(slot.merged_points),association_samples=len(slot.association_samples),
            uncertainty=slot.uncertainty,visible_extent=slot.visible_extent)
        path=self.audit_dir/f'{self.session}_{self.calls:06d}.json'
        path.write_text(json.dumps(audit,sort_keys=True,allow_nan=False)+'\n')
        from .ground_replay import record_mask
        self.queries.append(dict(name=name,backend='ground_v3',state=slot.state.value,
            result=result,**record_mask(slot.masks,slot.probabilities,slot.tau,self.geometry)))
        return text

    def verify_request(self,name,context):
        canonical=normalize_name(name)
        if context.clip_key != self.scene.video_sha256:
            raise ValueError('verify_clip_key_mismatch')
        self.scene.frames.require(context.frame_map.source_indices)
        entry=self._memory_entry(canonical)
        marker=getattr(entry,'verified_by',None) if isinstance(entry,ObjectSlot) else (entry or {}).get('verified_by')
        if marker==context.verify_identity:
            return None
        entry=self._resolve(canonical)
        pending=getattr(self,'pending_verify',{})
        pending[canonical]=entry;self.pending_verify=pending
        return self._verify_candidates(name,canonical,entry,context)

    def _verify_candidates(self,name,canonical,entry,context,source=None):
        source=self.source if source is None else source
        candidates=[]
        if isinstance(entry,ObjectSlot):
            if entry.result['seen']:
                k=entry.result['best']
                candidates=[dict(candidate_id=canonical+':mask',slot=k,mask=entry.masks[k-1])]
        else:
            for c in sorted(entry['candidates'],key=lambda c:(-c.features['peak'],c.id)):
                p=self.stages.visible(c,entry.get('prior'))
                if p is None:continue
                mask=source.native_mask(canonical,p) if hasattr(source,'native_mask') else p.mask
                candidates.append(dict(candidate_id=c.id,slot=p.frame,mask=mask))
                if len(candidates)==5:break
        for c in candidates:
            k=c['slot'];c.update(source_index=context.frame_map.source_indices[k-1],
                                rgb_sha256=context.frame_map.rgb_sha256[k-1])
        return dict(name=name,forms=('V1',),candidates=candidates,frames=context.frames,
                    frame_map=context.frame_map,context=context)

    def retry_verify(self,name,receipt,context):
        canonical=normalize_name(name);rescue=self.stages.rescue
        result=self.results.get(name,{})
        slot=self.question_slots.get(canonical)
        # A claim belongs to this trace. It is not evidence that the object is
        # absent, and must not replace the primary candidate memory with rescue.
        if slot is not None and slot.reason=='exclusivity_conflict':
            return None
        if (rescue is None or canonical in self.rescue_attempted or result.get('seen')
                or receipt['status'] not in ('ok','empty','invalid_candidates') or not self.mask_source.startswith('svp')):
            return None
        self.rescue_attempted.add(canonical)
        primary=self.pending_verify.get(canonical)
        if primary is None or isinstance(primary,ObjectSlot) or primary.get('rescue'):
            primary=self.memory.get(canonical,self.config_hash,scene=self.scene)
        if primary is not None and not receipt.get('dropped') and self.memory.get(canonical,self.config_hash,scene=self.scene) is None:
            self.memory.put(canonical,self.config_hash,primary,scene=self.scene)
        from .scene_state import SceneState
        from .svp_stages import SVPStages
        from dataclasses import replace
        if self.rescue_backend is None:
            self.rescue_backend=GroundV3(SceneState(self.scene.video_sha256,rescue.frame_map,rescue.geometry.identity),
                rescue.geometry,rescue.source,mask_source=self.mask_source,selector=self.selector,
                selector_identity=self.config['selector'],audit_dir=self.audit_dir,
                geometry_profile=rescue.geometry.contract.profile,verify=self.verify,
                rule=self.config['rule'],threshold=self.config['threshold'],weights=self.config['weights'],
                verify_threshold=self.config['verify_threshold'],ambiguity_margin=self.config['ambiguity_margin'],
                stages=SVPStages(presence=rescue.presence,presence_threshold=self.stages.threshold,propagation=False))
        entry=self.rescue_backend._resolve(canonical)
        if isinstance(entry,ObjectSlot):return None
        entry['rescue']=True
        entry['primary_proposals']=(primary or {}).get('primary_proposals',[])
        for c in entry['candidates']:c.id='rescue:'+c.id
        entry['verdict']={c.id:1. for c in entry['candidates']}
        self.pending_verify[canonical]=entry
        batch=dict(context.batch,hrp_frame_indices=rescue.frame_map.source_indices)
        secondary=replace(context,geometry=rescue.geometry,frame_map=rescue.frame_map,frames=rescue.frames,batch=batch)
        return self._verify_candidates(name,canonical,entry,secondary,rescue.source)

    def accept_verify(self,name,receipt,context):
        if receipt['status']!='ok':raise ValueError('cannot_accept_failed_verification')
        canonical=normalize_name(name);entry=self.pending_verify.pop(canonical)
        values={r['candidate_id']:r['p_yes'] for r in receipt['rows'] if r['form']=='V1'}
        if any(not np.isfinite(p) or not 0<=p<=1 for p in values.values()):
            raise ValueError('invalid_verify_probability')
        if isinstance(entry,ObjectSlot):
            entry.verified_by=context.verify_identity
            if values.get(canonical+':mask',0.)<self.config['verify_threshold']:
                entry=self._miss(canonical,State.NOT_SEEN,'verify_rejected')
                entry.verified_by=context.verify_identity
            slot=entry
        else:
            if not set(values).issubset({c.id for c in entry['candidates']}):
                raise ValueError('misaligned_verify_candidate_id')
            entry['verified_ids']=set(values)
            entry['verdict']={c.id:values.get(c.id,0.) for c in entry['candidates']}
            entry['candidates']=sorted(entry['candidates'],key=lambda c:(-self._score(c,entry['verdict']),c.id))
            entry['audit'].update(p_yes=entry['verdict'],stubbed=False)
            entry['verified_by']=context.verify_identity
            slot=self._select(canonical,entry)
        # Only the context's bound own geometry is eligible for the accepted lift.
        if slot.masks is not None:
            slot.result=lift_object(name,slot.masks,slot.probabilities,context.geometry,tau=slot.tau)
            slot.finalize()
        if not receipt.get('dropped'):
            memory_key=self.config_hash+':rescue' if isinstance(entry,dict) and entry.get('rescue') else self.config_hash
            self.memory.put(canonical,memory_key,entry,scene=self.scene)
        self.question_slots[canonical]=slot
        if self._claims_enabled() and slot.candidate is not None and slot.result['seen']:self.claims[canonical]=slot.candidate
        return self._emit(name,canonical,slot,context.registry)

    def gap(self,a,b):
        names=[b] if isinstance(b,str) else b
        if a not in self.results or any(n not in self.results for n in names):
            return 'not seen'
        return render_gap(self.results[a],self.results[b],audit=self.gap_queries) if isinstance(b,str) else render_gaps(
            self.results[a],[self.results[n] for n in names],audit=self.gap_queries)
