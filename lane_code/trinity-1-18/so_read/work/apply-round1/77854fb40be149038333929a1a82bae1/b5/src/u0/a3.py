"""In-call heads of the real reader: the stage-1 grounding socket and the scale-head adapter.

Stage 1 (ground/gap): the frozen SAM 3 tower runs inside the call on this read's anchor frames with the name as
written (lowercase and strip only; the tree's `normalize_phrase` singular map is bypassed). Its proposals are
lifted, linked and featurised by the runtime's unchanged producers (`routed_features`, `routed_candidates`), the
selector head's inputs come from `selector_inputs.candidate_vectors`, and the head's argmax over
[candidates, null] picks one candidate or none. Proposal retention is the contract of the K1 raw-prompt run the
head's raw-only tables come from (mask_kit variantlib 'dense': joint >= 0.05, at most 30 per frame, mask logit > 0),
not the tree's live contract (joint >= 0.2, 10). Each name is featurised alone: cross-name exclusivity sees no
other name, at training time and in the call, so a feature never depends on which names the model asked before.

Scale: `ScaleHeadCall(head)(tower)` maps the tower dict of `Perception` onto ScaleHead's tensors.
"""
import sys
from pathlib import Path

import numpy as np
import torch

from parity_kit.common import LANE
HEADS = LANE / 'heads'
K1_CONTRACT = dict(joint_floor=.05, cap=30)


def name_key(name):
    return str(name).strip().lower()


class ScaleHeadCall(torch.nn.Module):
    def __init__(self, head):
        super().__init__()
        self.head = head

    def forward(self, tower):
        pose = np.asarray(tower['raw_pose9'])[np.asarray(tower['anchor_slots'])]
        t = lambda a: torch.as_tensor(np.asarray(a))[None]  # noqa: E731
        return self.head(depth_grid=t(tower['depth_grid']), depth_conf_grid=t(tower['depth_conf_grid']),
                         points_grid=t(tower['points_grid']), anchor_pose=t(pose),
                         grid_uv=torch.as_tensor(np.asarray(tower['grid_uv'])))[0]


class OwnDepthScale(torch.nn.Module):
    """Scale from the checkpoint's own depth head: median(own depth / G3T depth) on grid points whose tower
    confidence is above the clip median and whose two depths are finite and positive (the confidence rule of
    student_pilot.tower_scale_rule.estimate without its own-depth range gate). Own depth is the depth head queried at the tower's 51x51 grid of every anchor frame, from
    the heads of this read's prefill. No parameters of its own: it reads the depth head inside the checkpoint."""

    reads_prefill = True

    def forward(self, tower, prefill_state):
        heads = prefill_state.heads
        if heads.depth_map is None:
            raise ValueError('checkpoint_lacks_depth_head')
        axis = torch.as_tensor(np.asarray(tower['grid_uv']).copy(), device=heads.depth_map.device)
        yy, xx = torch.meshgrid(axis, axis, indexing='ij')
        n = np.asarray(tower['depth_grid']).shape[0]
        uv = torch.stack((xx, yy), -1).reshape(1, -1, 2).expand(n, -1, -1)
        with torch.no_grad():
            own = heads.depth_head.query(heads.depth_map, uv).double().cpu().numpy().reshape(np.asarray(tower['depth_grid']).shape)
        scale = median_ratio(tower['depth_grid'], tower['depth_conf_grid'], own)
        return torch.tensor(float(np.log(scale)), dtype=torch.float64)


def median_ratio(depth, confidence, own):
    d, c, v = (np.asarray(x, float) for x in (depth, confidence, own))
    if d.shape != c.shape or d.shape != v.shape:
        raise ValueError('depth_grids_differ')
    finite = c[np.isfinite(c)]
    if not len(finite):
        raise ValueError('no_finite_confidence')
    selected = np.isfinite(c) & (c > np.percentile(finite, 50)) & np.isfinite(d) & (d > 0) & np.isfinite(v) & (v > 0)
    if not selected.any():
        raise ValueError('no_scale_points')
    return float(np.median(v[selected] / d[selected]))


def sam3_detect(tower, features, name):
    """One list per anchor frame of dict(mask bool[480,640], score, presence) for the raw name: Sam3Tower._detect's forward with the
    K1 retention contract and no phrase normalisation."""
    import torch.nn.functional as TF
    from student_pilot import routed_features as F
    tower._load()
    phrase = name_key(name)
    with torch.inference_mode(), tower._autocast():
        text = tower._backend.model.backbone.forward_text([phrase], device=str(tower.device))
    out = []
    for stored, (h, w) in zip(features.frames, features.sizes):
        backbone = {k: (v.to(tower.device) if hasattr(v, 'to') else [x.to(tower.device) for x in v])
                    for k, v in stored.items()}
        backbone['vision_features'] = backbone['backbone_fpn'][-1]
        backbone.update(text)
        with torch.inference_mode(), tower._autocast():
            raw = tower._backend.model.forward_grounding(
                backbone_out=backbone, find_input=tower._backend.find_stage,
                geometric_prompt=tower._backend.model._get_dummy_prompt(), find_target=None)
        scores = raw['pred_logits'].sigmoid().reshape(-1).float()
        presence = float(raw['presence_logit_dec'].sigmoid().item())
        joint = scores * presence
        order = torch.argsort(scores, descending=True, stable=True)
        keep = order[joint[order] >= K1_CONTRACT['joint_floor']][:K1_CONTRACT['cap']]
        native = raw['pred_masks'].reshape(-1, *raw['pred_masks'].shape[-2:])
        frame = []
        for i in keep.tolist():
            m = (TF.interpolate(native[i][None, None].float(), (h, w), mode='bilinear', align_corners=False)[0, 0] > 0)
            frame.append(dict(mask=F.resize(m.cpu().numpy(), F.SHAPE), score=float(scores[i]), presence=presence))
        out.append(frame)
    return out


class StageOne:
    """propose(name) -> (candidates, inputs) and select(inputs) -> index or -1, for grounding.StageOneSocket.

    detect(name) -> one raw list per anchor frame (sam3_detect bound to this read's tower features, or a cache reader in
    tests). Every name is featurised alone (its own pool), as in the isolated K1 tables (heads/selector/
    isolate_tables.py)."""

    def __init__(self, detect, head, geometry, rule="null_argmax"):
        if rule not in ("null_argmax", "candidates_argmax"):
            raise ValueError("unknown_stage1_select_rule")
        self.rule = rule
        self.diagnostics = {}
        from student_pilot import routed_features as F
        if str(HEADS / 'selector/sl118') not in sys.path:
            sys.path.insert(0, str(HEADS / 'selector/sl118'))
        import selector_inputs as SI
        self.F, self.SI, self.detect, self.head = F, SI, detect, head
        self.geometry, self.exact = geometry, F.Geometry(geometry)
        self.grids = F.candidates.lift_grid(geometry)
        self.raw = {}

    def features(self, name):
        F = self.F
        if name not in self.raw:
            self.raw[name] = self.detect(name)
        proposals, lift_outcomes = F.candidates.lift(F.cache_for(name, self.raw[name]), name, self.geometry, floor=.3,
                                         grids=self.grids, phrase=name)
        pools = {name: F.candidates.link(proposals, name)}
        F.candidates.scene_candidates(pools, self.geometry)
        accepted = F.accept_features(pools[name], self.raw[name], self.exact)
        x = self.SI.candidate_vectors(pools[name], self.raw[name], self.exact, accepted) if accepted else []
        self.diagnostics[name] = proposal_diagnostics(
            self.rule, name, self.raw[name], proposals, lift_outcomes, accepted, x)
        return accepted, x

    def propose(self, name):
        accepted, x = self.features(name)
        cands = [dict(candidate_id=a['candidate_id'], masks=a['masks']) for a in accepted]
        return cands, dict(x=torch.tensor(x, dtype=torch.float64), name=name)

    @torch.no_grad()
    def select(self, inputs):
        rule = getattr(self, 'rule', 'null_argmax')
        if rule == 'candidates_argmax' and len(inputs['x']) == 0:
            return -1
        slots = self.head.with_null(inputs['x'], None, inputs['name'])
        k = int(torch.argmax(slots))
        choice = -1 if k == len(slots) - 1 else k
        if rule == 'candidates_argmax':
            choice = int(torch.argmax(slots[:len(inputs['x'])]))
        if inputs['name'] in getattr(self, 'diagnostics', {}):
            record = self.diagnostics[inputs['name']]
            for candidate, logit in zip(record['candidates'], slots):
                candidate['logit'] = float(logit)
            record.update(null_logit=float(slots[-1]), chosen_index=choice,
                          null_would_win=k == len(slots) - 1)
        return choice


def proposal_diagnostics(rule, name, raw, proposals, lift_outcomes, accepted, vectors):
    """Observe producers without changing any candidate, feature or response."""
    from collections import Counter
    flat = [entry for frame in raw for entry in frame]
    return dict(rule=rule, name_key=name_key(name), sam3=dict(
        kept_per_frame=[len(frame) for frame in raw],
        max_score=max((float(e['score']) for e in flat), default=None),
        max_presence=max((float(e['presence']) for e in flat), default=None),
        max_joint=max((float(e['score'])*float(e['presence']) for e in flat), default=None)),
        lift_entering=len(proposals)+len(lift_outcomes), lifted=len(proposals),
        lift_reasons=dict(Counter(entry['reason'] for entry in lift_outcomes)),
        linked_candidates=len(accepted), candidates=[dict(
            id=a['candidate_id'], frames=list(a['masks']), peak=float(a['features']['peak']),
            logit=None, inputs=np.asarray(x, dtype=np.float32).tolist())
            for a, x in list(zip(accepted, vectors))[:K1_CONTRACT['cap']]],
        null_logit=None, chosen_index=-1, null_would_win=None)


def stage1_factory(sam3_tower, selector_head, anchor_frames_of, rule='null_argmax', *, memo=None, artifact=None, read_cache=None):
    """socket(frames, geometry) for Perception: encodes the anchor frames once per read, in the call."""
    from .grounding import StageOneSocket

    def socket(frames, geometry):
        cache = {}

        def detect(name):
            if read_cache is not None:
                from .read_cache import digest, module_identity, has_hooks, execution_state, image_identity
                from .perception_memo import weight_identity, frame_indices
                from student_pilot.sam3_tower import ClipFeatures
                images = anchor_frames_of(frames)
                # Load before taking the live identity. Loading can replace the
                # backend and also establishes frozen evaluation parameters.
                sam3_tower._load()
                model = sam3_tower._backend.model
                if any(m.training for m in model.modules()) or any(p.requires_grad for p in model.parameters()):
                    raise ValueError('SAM cache requires frozen evaluation')
                if has_hooks(model):
                    info = read_cache.stats.setdefault('sam_bypass', {'calls':0})
                    info['calls'] += 1
                    return sam3_detect(sam3_tower, sam3_tower.encode(images), name)
                try:live = module_identity(model)
                except (TypeError,RecursionError):
                    info=read_cache.stats.setdefault('sam_bypass',{'calls':0});info['calls']+=1
                    return sam3_detect(sam3_tower,sam3_tower.encode(images),name)
                identity = weight_identity(artifact, 'sam3', dict(
                    device=str(sam3_tower.device), precision=sam3_tower.precision,
                    image_batch_size=sam3_tower.image_batch_size,
                    native_image_batch=sam3_tower.native_image_batch))
                backend=sam3_tower._backend
                options={k:getattr(backend,k) for k in ('resolution','confidence_threshold','device') if hasattr(backend,k)}
                options={k:str(v) if isinstance(v,torch.device) else v for k,v in options.items()}
                clip = digest((image_identity(images,frame_indices(frames),identity),live,
                               id(sam3_tower),id(backend),id(sam3_tower._owner),execution_state(),
                               getattr(sam3_tower,'settings',{}),options))
                def fresh_detection():
                    if cache.get('identity') != clip:
                        def encode():
                            f = sam3_tower.encode(images)
                            return dict(frames=f.frames, sizes=f.sizes)
                        value = read_cache.call('sam_features', clip, encode)
                        cache['features'] = ClipFeatures(value['frames'], value['sizes'], sam3_tower._owner)
                        cache['identity'] = clip
                    return sam3_detect(sam3_tower, cache['features'], name)
                return read_cache.call('sam_detections', digest((clip, name_key(name), K1_CONTRACT)), fresh_detection)
            if 'features' not in cache:
                if memo is None:
                    cache['features'] = sam3_tower.encode(anchor_frames_of(frames))
                else:
                    from .perception_memo import sam_encode
                    cache['features'] = sam_encode(memo, artifact, sam3_tower, anchor_frames_of(frames), frames)
            return sam3_detect(sam3_tower, cache['features'], name)
        s = StageOne(detect, selector_head, geometry, rule=rule)
        from .geometry import frame_count
        return StageOneSocket(s.propose, s.select, (240, 320), frame_count(geometry))
    return socket
