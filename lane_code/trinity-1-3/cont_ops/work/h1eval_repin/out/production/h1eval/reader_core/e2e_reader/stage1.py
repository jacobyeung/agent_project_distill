"""In-call heads of the real reader: the stage-1 grounding socket and the scale-head adapter.

Stage 1 (ground/gap): the frozen SAM 3 tower runs inside the call on this read's anchor frames with the name as
written (lowercase and strip only; the tree's `normalize_phrase` singular map is bypassed). Its proposals are
lifted, linked and featurised by the runtime's unchanged producers (`routed_features`, `routed_candidates`), the
selector head's inputs come from `selector_inputs.candidate_vectors`, and the head's argmax over
[candidates, null] picks one candidate or none. Proposal retention is the K1 cache contract the head was trained
on (joint >= 0.05, at most 100 per frame, mask logit > 0), not the tree's live contract (joint >= 0.2, 10).

Scale: `ScaleHeadCall(head)(tower)` maps the tower dict of `Perception` onto ScaleHead's tensors.
"""
import sys
from pathlib import Path

import numpy as np
import torch

HEADS = Path(__file__).resolve().parents[1] / 'heads'
K1_CONTRACT = dict(joint_floor=.05, cap=100)


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
    """Scale from the checkpoint's own depth head: the tree's frozen estimator, median(own depth / G3T depth) on
    grid points whose tower confidence is above the clip median (student_pilot.tower_scale_rule.estimate, the
    deployed C8r rule). Own depth is the depth head queried at the tower's 51x51 grid of every anchor frame, from
    the heads of this read's prefill. No parameters of its own: it reads the depth head inside the checkpoint."""

    reads_prefill = True

    def forward(self, tower, prefill_state):
        from student_pilot.tower_scale_rule import estimate
        heads = prefill_state.heads
        if heads.depth_map is None:
            raise ValueError('checkpoint_lacks_depth_head')
        axis = torch.as_tensor(np.asarray(tower['grid_uv']).copy(), device=heads.depth_map.device)
        yy, xx = torch.meshgrid(axis, axis, indexing='ij')
        n = np.asarray(tower['depth_grid']).shape[0]
        uv = torch.stack((xx, yy), -1).reshape(1, -1, 2).expand(n, -1, -1)
        with torch.no_grad():
            own = heads.depth_head.query(heads.depth_map, uv).double().cpu().numpy().reshape(np.asarray(tower['depth_grid']).shape)
        scale, _, _ = estimate(tower['depth_grid'], tower['depth_conf_grid'], own)
        return torch.tensor(float(np.log(scale)), dtype=torch.float64)


def sam3_detect(tower, features, name):
    """32 lists of dict(mask bool[480,640], score, presence) for the raw name: Sam3Tower._detect's forward with the
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

    detect(name) -> 32 raw frame lists (sam3_detect bound to this read's tower features, or a cache reader in
    tests). Names asked earlier in the read stay in the pool, so cross-name exclusivity sees them, as the K1
    tables saw every named object of the capture."""

    def __init__(self, detect, head, geometry):
        from student_pilot import routed_features as F
        if str(HEADS / 'selector/sl118') not in sys.path:
            sys.path.insert(0, str(HEADS / 'selector/sl118'))
        import selector_inputs as SI
        self.F, self.SI, self.detect, self.head = F, SI, detect, head
        self.geometry, self.exact = geometry, F.Geometry(geometry)
        self.grids = F.candidates.lift_grid(geometry)
        self.raw, self.pools = {}, {}

    def features(self, name):
        F = self.F
        if name not in self.raw:
            self.raw[name] = self.detect(name)
        proposals, _ = F.candidates.lift(F.cache_for(name, self.raw[name]), name, self.geometry, floor=.3,
                                         grids=self.grids, phrase=name)
        self.pools[name] = F.candidates.link(proposals, name)
        F.candidates.scene_candidates(self.pools, self.geometry)
        accepted = F.accept_features(self.pools[name], self.raw[name], self.exact)
        x = self.SI.candidate_vectors(self.pools[name], self.raw[name], self.exact, accepted) if accepted else []
        return accepted, x

    def propose(self, name):
        accepted, x = self.features(name)
        cands = [dict(candidate_id=a['candidate_id'], masks=a['masks']) for a in accepted]
        return cands, dict(x=torch.tensor(x, dtype=torch.float64), name=name)

    @torch.no_grad()
    def select(self, inputs):
        slots = self.head.with_null(inputs['x'], None, inputs['name'])
        k = int(torch.argmax(slots))
        return -1 if k == len(slots) - 1 else k


def stage1_factory(sam3_tower, selector_head, anchor_frames_of):
    """socket(frames, geometry) for Perception: encodes the anchor frames once per read, in the call."""
    from .grounding import StageOneSocket

    def socket(frames, geometry):
        cache = {}

        def detect(name):
            if 'features' not in cache:
                cache['features'] = sam3_tower.encode(anchor_frames_of(frames))
            return sam3_detect(sam3_tower, cache['features'], name)
        s = StageOne(detect, selector_head, geometry)
        return StageOneSocket(s.propose, s.select, (240, 320))
    return socket
