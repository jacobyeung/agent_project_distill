"""Mask-source interfaces. Providers must bind masks to exact source indices."""
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import numpy as np
from .scene_state import normalize_name
from .phrases import cache_key
from trace_format.contracts import new_contracts

def cache_phrase(cache, name, codec):
    return cache_key(cache, name) if new_contracts() else codec.phrase(name)


# Storage/lifting floor and the semantic admission gate are separate contracts.
RETAINED_SCORE_FLOOR = .3
NATIVE_JOINT_THRESHOLD = .5


def native_gate(proposals):
    return [p for p in proposals if p.score >= RETAINED_SCORE_FLOOR
            and p.joint > NATIVE_JOINT_THRESHOLD]


def native_candidates(cache, name, codec):
    """Keep mask-centroid clicks before surface erosion or geometric linking."""
    from ofs import core as O, hrp_reference as H
    phrase = cache_phrase(cache, name, codec)
    if phrase not in cache['phrases']:
        return []
    candidates = []
    for frame in range(1, 33):
        record = cache['frames'][str(frame-1)]['phrases'][phrase]
        for index, instance in enumerate(sorted(record.get('instances') or [], key=lambda p: -float(p['score']))):
            score = float(instance['score'])
            joint = float(record['presence']) * score
            if score < RETAINED_SCORE_FLOOR or joint <= NATIVE_JOINT_THRESHOLD:
                continue
            mask = O.small_rle(instance['mask'])
            uv = H.centroid(mask)
            if uv is not None:
                candidates.append(H.Candidate(frame, uv, joint, index, mask, 'sam3'))
    return candidates


def file_sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for block in iter(lambda: f.read(1024*1024), b''):
            h.update(block)
    return h.hexdigest()


@dataclass
class MaskBatch:
    masks: object
    probabilities: object
    frame_indices: tuple
    tau: float = .5
    state: object = None
    reason: str = 'no_eligible_mask'


class MaskProvider:
    """GT or native MDG callable returning MaskBatch, with a pinned identity."""
    def __init__(self, fetch, identity, names=()):
        if not identity:
            raise ValueError('mask_provider_identity_required')
        self.fetch, self.identity = fetch, identity
        self.names = tuple(sorted({normalize_name(name) for name in names}))

    def masks_for(self, name):
        return self.fetch(name)


class NativeMDG:
    """Use the native isolated prompt-plus-call query, preserving v2 admission."""
    def __init__(self, frame_map, artifact_identity, names=()):
        if not artifact_identity:
            raise ValueError('mdg_artifact_identity_required')
        self.frame_indices = frame_map.source_indices
        self.identity = 'native_mdg:'+artifact_identity
        self.names = tuple(sorted({normalize_name(name) for name in names}))
        self.backend = None

    def bind_native_backend(self, backend):
        self.backend = backend

    def masks_for(self, name):
        from .mdg_decode import predict
        b = self.backend
        if b is None:
            raise ValueError('native_mdg_requires_generate_binding')
        states = b.query(name, allow_unknown=True)
        values,b.memory = predict(b.head,b.prefix,states,b.memory)
        return MaskBatch(values['mask'][0],values['prob'][0],self.frame_indices,b.tau)


class CachedSAM3:
    """The ttower cache reader validates its own hash and scene contract.

    ttower v1 does not embed source frame indices. The caller must supply the
    separately pinned frame manifest; the audit retains this provenance limit.
    """
    def __init__(self, raw, scene, frame_map, reader, frame_manifest, names=(), live=None):
        manifest_path = Path(frame_manifest)
        manifest = json.loads(manifest_path.read_text())
        self.frame_indices = tuple(manifest['frame_indices'])
        frame_map.require(self.frame_indices)
        if manifest.get('scene', scene) != scene:
            raise ValueError('cache_scene_mismatch')
        self.manifest_sha256 = file_sha256(manifest_path)
        self.cache = reader.load_cache(raw, scene)
        self.reader, self.live = reader, live
        self.names = tuple(normalize_name(n) for n in names)
        self.identity = file_sha256(reader.cache_path(raw, scene))+':'+self.manifest_sha256
        self.provenance = 'ttower_v1_external_frame_manifest'

    def proposals_for(self, name, geometry, ofs, grids):
        if cache_phrase(self.cache, name, self.reader) not in self.cache['phrases'] and self.live is not None:
            return self.live.proposals_for(name, geometry, ofs, grids)
        proposals, rejected = ofs.lift(self.cache, name, geometry, floor=RETAINED_SCORE_FLOOR, grids=grids)
        return native_gate(proposals), rejected

    def selector_candidates(self, name):
        if cache_phrase(self.cache, name, self.reader) not in self.cache['phrases'] and self.live is not None:
            return self.live.selector_candidates(name)
        return native_candidates(self.cache, name, self.reader)

    def native_mask(self,name,proposal):
        if cache_phrase(self.cache, name, self.reader) not in self.cache['phrases'] and self.live is not None:
            return self.live.native_mask(name,proposal)
        record=self.cache['frames'][str(proposal.frame-1)]['phrases'][cache_phrase(self.cache, name, self.reader)]
        instances=sorted(record.get('instances') or [],key=lambda p:-float(p['score']))
        return self.reader.rle_decode(instances[proposal.index]['mask'])


class TowerSAM3:
    """encode once per clip; detect only on a memory miss. No model ownership."""
    def __init__(self, tower, frames, frame_map, identity, cache_codec):
        if len(frames) != 32 or not identity:
            raise ValueError('tower_requires_32_frames_and_identity')
        self.tower, self.frames, self.codec = tower, frames, cache_codec
        self.frame_indices, self.identity = frame_map.source_indices, identity
        self.encoded = None
        self.native_masks = {}
        self.provenance = 'sam3_native_joint_gt_0.5_retained_score_ge_0.3'

    def _detect(self, name):
        if self.encoded is None:
            self.encoded = self.tower.encode(self.frames)
        # Match the archived SAM proposal pool before the backend's joint gate.
        detect=getattr(self.tower,'detect_cache_reference',self.tower.detect)
        detected = detect(self.encoded, name)
        if len(detected) != 32:
            raise ValueError('tower_detection_frame_count')
        phrase = normalize_name(name) if new_contracts() else self.codec.phrase(name)
        cache = dict(phrases=[phrase], frames={})
        for k, rec in enumerate(detected):
            if len(rec.scores) != len(rec.masks):
                raise ValueError('tower_score_mask_count')
            instances = [dict(score=float(score), mask=self.codec.rle_encode(np.asarray(mask, bool)))
                         for score, mask in zip(rec.scores, rec.masks)]
            for i,instance in enumerate(sorted(instances,key=lambda p:-p['score'])):
                self.native_masks[name,k+1,i]=self.codec.rle_decode(instance['mask'])
            cache['frames'][str(k)] = dict(phrases={phrase:dict(presence=float(rec.presence), instances=instances)})
        return cache

    def proposals_for(self, name, geometry, ofs, grids):
        cache = self._detect(name)
        proposals, rejected = ofs.lift(cache, name, geometry, floor=RETAINED_SCORE_FLOOR, grids=grids)
        return native_gate(proposals), rejected

    def selector_candidates(self, name):
        return native_candidates(self._detect(name), name, self.codec)

    def native_mask(self,name,proposal):
        return self.native_masks[name,proposal.frame,proposal.index]


class OwnProposals:
    """Native-box/mask producer injection; proposals use the ofs Proposal type."""
    def __init__(self, fetch, frame_map, identity):
        if not identity:
            raise ValueError('own_proposal_identity_required')
        self.fetch, self.identity = fetch, identity
        self.frame_indices = frame_map.source_indices
        self.provenance = 'injected_svp_own_producer'

    def proposals_for(self, name, geometry, ofs, grids):
        return self.fetch(name, geometry, ofs, grids)


class VerifyStub:
    """Explicit P(yes) stub for CPU plumbing, never a calibrated confidence."""
    identity = 'verify_stub_pyes_1_v1'
    stubbed = True

    def __call__(self, name, candidates):
        return {c.id: 1. for c in candidates}
