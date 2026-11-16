"""The view-set where-provider (schema 6): WhereProvider.where(obs) -> WhereOutput, a pure function of the whitelisted
Observation and the pinned weights.

Steps (schema 6.3):
  1. phrases from the sha-pinned table;
  2. presence per view and entity: the student's P(yes); a view needs P(yes) >= tau;
  3. point per view and entity: the student's {"point_2d": [u, v]} (uv1000) or null;
  4. proposals: SAM 3 on [wrist_t, agent_t] for the entity's noun;
  5. selection: a view grounds the entity iff P(yes) >= tau, the point is not null and some proposal mask contains it
     (ties go to the higher score); otherwise low_presence, no_point or no_lift;
  6. lift per grounded view: mask eroded by erode_px, pixels with finite positive G3T depth and confidence above the
     view's median; >= min_pixels -> per-axis median and p2-p98 principal-axis extents, else no_lift;
  7. reported point: the wrist lift when the wrist grounds the entity, else the agent lift moved into view 0;
  8. cross-view rule when both views ground it: the wrist-lifted point projects inside the agent mask dilated by
     cross_view_dilate_px, and the agent-lifted point inside the dilated wrist mask whenever that projection is in
     frame; otherwise cross_view (valid = 0);
  9. scale: proprio_handeye (scale.py); X_wrist = s M X_reported when the geometry frames are mirrored (G3T on
     LIBERO's mirrored dataset images, schema 0), else s X_reported (GT); metric iff ||X_wrist|| <= max_range_m;
 10. record (types.py) and line (pline.py); reach_base uses R_eef from proprio's axis-angle.
G3T runs once per call on [wrist_t, agent_t, wrist history newest first] (schema 6.2).
"""
import hashlib
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path

import numpy as np

from . import geometry as G
from . import scale as S
from .phrases import default_table
from .pline import format_line
from .geometry_viewset import CameraCheckError
from .types import ROLES, SCHEMA, Entity, WhereOutput

PACKAGE = Path(__file__).parent
STAGE = {'low_presence': 0, 'no_point': 1, 'no_lift': 2}
MIRROR = np.diag([-1.0, 1.0, 1.0])


@dataclass
class Config:
    """schema 10 `vla.provider` keys (hand_eye is loaded separately; its sha enters provider_config_sha256)."""
    history_offsets: tuple = (8, 16, 32)
    min_motion_m: float = 0.02
    max_ratio_spread: float = 0.2
    max_range_m: float = 2.0
    presence_source: str = 'own_yes_no'
    tau: float = 0.5
    tau_source: str = 'unfitted'
    select: str = 'own_point'
    erode_px: int = 2
    min_pixels: int = 20
    cross_view_dilate_px: int = 3
    behind_z: float = 0.01
    cross_view_occlusion_rel: float = 0.05   # None = schema 6.3 step 8 as written; r = also pass when the wrist depth at
                                             # the projected pixel is nearer than (1 - r) x the point's depth (occluded)
    orientation: str = 'dataset'
    g3t_mirror_x: bool = True                  # LIBERO dataset images mirror the camera view (schema 0); ViewSetG3T flag
    hand_eye_sha256: str = 'unpinned'

    def to_json(self):
        d = asdict(self)
        d['history_offsets'] = list(d['history_offsets'])
        return json.dumps(d, sort_keys=True, separators=(',', ':'))

    def sha(self):
        return hashlib.sha256(self.to_json().encode()).hexdigest()


def package_sha():
    """sha256 over the package's source files and data, in sorted path order (the provider code sha)."""
    digest = hashlib.sha256()
    for path in sorted(p for p in PACKAGE.rglob('*') if p.is_file() and p.suffix in ('.py', '.json')):
        digest.update(str(path.relative_to(PACKAGE)).encode() + b'\0' + path.read_bytes() + b'\0')
    return digest.hexdigest()


def history_steps(t, offsets=(8, 16, 32)):
    """t - 8, t - 16, t - 32 clipped at 0, duplicates and t itself dropped, newest first."""
    out = []
    for o in offsets:
        h = max(t - int(o), 0)
        if h != t and h not in out:
            out.append(h)
    return out


def view_list(t, offsets=(8, 16, 32)):
    return [('wrist', t), ('agent', t)] + [('wrist', h) for h in history_steps(t, offsets)]


@dataclass
class ViewTrace:
    p_yes: float
    point: object = None
    reason: str = 'ok'
    mask: object = None          # selected proposal mask (not serialised)
    score: float = None
    X: object = None             # lift in the view's camera frame, G3T units
    extents: object = None
    n: int = 0

    def log(self):
        return dict(p_yes=self.p_yes, point=None if self.point is None else list(self.point), reason=self.reason,
                    score=self.score, X=None if self.X is None else np.asarray(self.X).tolist(), n=self.n)


class WhereProvider:
    def __init__(self, presence, pointer, proposals, geometry, hand_eye, config=None, *, table=None):
        self.presence, self.pointer, self.proposals, self.geometry = presence, pointer, proposals, geometry
        self.hand_eye = hand_eye
        self.cfg = config or Config()
        if self.cfg.hand_eye_sha256 != hand_eye.sha256:
            self.cfg = Config(**{**asdict(self.cfg), 'hand_eye_sha256': hand_eye.sha256})
        if self.cfg.presence_source != 'own_yes_no' or self.cfg.select != 'own_point':
            raise ValueError('v1 provider: presence.source own_yes_no and select own_point')
        self.table = table or default_table()
        self.code_sha = package_sha()
        self.last_trace = None

    def sha(self):
        parts = dict(schema=SCHEMA, code=self.code_sha, config=self.cfg.sha(), table=self.table.sha256,
                     presence=self.presence.sha(), pointer=self.pointer.sha(), proposals=self.proposals.sha(),
                     geometry=self.geometry.sha())
        return hashlib.sha256(json.dumps(parts, sort_keys=True).encode()).hexdigest()

    def pins(self):
        """The schema 9 pins: code, config, student export, G3T, SAM 3, hand-eye and phrase table."""
        def pin(b):
            return b.pin() if hasattr(b, 'pin') else b.sha()
        student = pin(self.presence) if self.presence is self.pointer else hashlib.sha256(
            f'{pin(self.presence)}|{pin(self.pointer)}'.encode()).hexdigest()
        return dict(provider_code_sha=self.code_sha, provider_config_sha256=self.cfg.sha(),
                    student_export_sha256=student, g3t=pin(self.geometry), sam3_checkpoint_sha256=pin(self.proposals),
                    hand_eye_sha256=self.hand_eye.sha256, phrase_table_sha256=self.table.sha256)

    # -- one view ---------------------------------------------------------------------------------------------------
    def _ground(self, image, phrase, view, proposals, depth, conf, K):
        tr = ViewTrace(float(self.presence.p_yes(image, phrase, view)))
        if tr.p_yes < self.cfg.tau:
            tr.reason = 'low_presence'
            return tr
        tr.point = self.pointer.point(image, phrase, view)
        if tr.point is None:
            tr.reason = 'no_point'
            return tr
        uv = ((min(tr.point[0], 999) + 0.5) / 1000, (min(tr.point[1], 999) + 0.5) / 1000)   # code 1000 clamps to 999
        hits = [p for p in proposals if G.mask_contains(p.mask, uv)]
        if not hits:
            tr.reason = 'no_lift'
            return tr
        best = max(hits, key=lambda p: p.score)
        tr.mask, tr.score = best.mask, float(best.score)
        lift = G.lift_mask(best.mask, depth, conf, K, self.cfg.erode_px, self.cfg.min_pixels)
        if lift is None:
            tr.reason = 'no_lift'
            return tr
        tr.X, tr.extents, _, tr.n = lift
        return tr

    # -- one entity -------------------------------------------------------------------------------------------------
    def _entity(self, role, phrase, obs, geo, iw, ia, props, s, s_flag):
        if phrase is None:
            return Entity(role), {}
        e = Entity(role, phrase.phrase, phrase.noun)
        traces = {}
        for name, i in (('wrist', iw), ('agent', ia)):
            image = obs.wrist[obs.t] if name == 'wrist' else obs.agent
            traces[name] = self._ground(image, phrase.phrase, geo.views[i], props[name], geo.depth[i],
                                        None if geo.conf is None else geo.conf[i], geo.K[i])
        e.presence = max(tr.p_yes for tr in traces.values())
        e.diag = dict(views={k: tr.log() for k, tr in traces.items()})
        lifted = {k: tr for k, tr in traces.items() if tr.X is not None}
        if not lifted:
            e.reason = max((tr.reason for tr in traces.values()), key=STAGE.get)
            return e, traces
        T_wa = geo.T0[ia]                      # T_view0<-agent
        T_aw = G.inv(T_wa)
        Kw, Ka = geo.K[iw], geo.K[ia]
        (hw, ww), (ha, wa) = geo.depth[iw].shape, geo.depth[ia].shape
        if 'wrist' in lifted:
            X0, main = np.asarray(lifted['wrist'].X, dtype=np.float64), lifted['wrist']
        else:
            X0, main = G.apply(T_wa, lifted['agent'].X), lifted['agent']
        if len(lifted) == 2:
            uv_a, za = G.project(G.apply(T_aw, X0)[None], Ka, wa, ha)
            ok_a = za[0] > 0 and G.mask_contains(G.dilate(lifted['agent'].mask, self.cfg.cross_view_dilate_px), uv_a[0])
            Xa0 = G.apply(T_wa, lifted['agent'].X)
            uv_w, zw = G.project(Xa0[None], Kw, ww, hw)
            ok_w = (not (zw[0] > 0 and G.in_frame(uv_w[0]))
                    or G.mask_contains(G.dilate(lifted['wrist'].mask, self.cfg.cross_view_dilate_px), uv_w[0]))
            occluded = False
            if not ok_w and self.cfg.cross_view_occlusion_rel is not None:
                d = geo.depth[iw][int(uv_w[0][1] * hw), int(uv_w[0][0] * ww)]
                occluded = bool(np.isfinite(d) and d < (1 - self.cfg.cross_view_occlusion_rel) * zw[0])
                ok_w = occluded
            e.diag['cross_view'] = dict(wrist_in_agent=uv_a[0].tolist(), agent_in_wrist=uv_w[0].tolist(),
                                        ok_agent=bool(ok_a), ok_wrist=bool(ok_w), occluded=occluded)
            if not (ok_a and ok_w):
                e.reason = 'cross_view'
                return e, traces
        if X0[2] <= self.cfg.behind_z:
            e.reason = 'behind_wrist'
            return e, traces
        e.valid, e.reason = True, 'ok'
        e.uv_wrist = G.record_uv(X0, Kw, ww, hw, self.cfg.behind_z)
        e.uv_agent = G.record_uv(G.apply(T_aw, X0), Ka, wa, ha, self.cfg.behind_z)
        e.diag['X_view0'] = X0.tolist()
        if s is None:
            e.reason = 'no_scale'
            return e, traces
        Xm = s * (MIRROR @ X0 if geo.mirror else X0)     # true OpenCV wrist frame (schema 0: G3T frames are mirrored)
        e.diag['range_m'] = float(np.linalg.norm(Xm))
        if e.diag['range_m'] > self.cfg.max_range_m:
            e.reason = 'no_scale'
            return e, traces
        e.X_wrist = Xm.tolist()
        e.reach_base = S.reach_base(Xm, obs.proprio[obs.t], self.hand_eye).tolist()
        e.size = np.maximum(s * np.asarray(main.extents, dtype=np.float64), 0.02).tolist()
        e.scale_source = s_flag
        return e, traces

    def _failed(self, obs, step, views, subgoal, why):
        entities = [Entity(r) if getattr(step, r) is None else
                    Entity(r, getattr(step, r).phrase, getattr(step, r).noun, reason='no_lift', diag=dict(camera=why))
                    for r in ROLES]
        self.last_trace = None
        meta = dict(schema=SCHEMA, t=obs.t, subgoal=subgoal, views=[list(v) for v in views], scale=None,
                    scale_info=dict(camera_check=why), tau=self.cfg.tau, reasons=[e.reason for e in entities])
        return WhereOutput(entities, format_line(entities), meta)

    def where(self, obs, subgoal=0):
        step = self.table.step(obs.instruction, subgoal)
        views = view_list(obs.t, self.cfg.history_offsets)
        missing = [v for v in views if v[0] == 'wrist' and (v[1] not in obs.wrist or v[1] not in obs.proprio)]
        if missing:
            raise ValueError(f'Observation lacks the history views {missing}')
        images = [obs.wrist[k] if r == 'wrist' else obs.agent for r, k in views]
        try:
            geo = self.geometry.run(images, views)
        except CameraCheckError as exc:
            return self._failed(obs, step, views, subgoal, str(exc))
        if list(geo.views) != views:
            raise ValueError('Geometry returned another view order')
        iw, ia = 0, 1
        if geo.metric_flag is not None:
            s, s_flag, info = 1.0, geo.metric_flag, dict(metric=geo.metric_flag)
        else:
            hist = {k: obs.proprio[k] for r, k in views[2:]}
            centres = {k: geo.centre(i) for i, (r, k) in enumerate(views) if i >= 2}
            s, info = S.proprio_handeye(obs.proprio[obs.t], hist, centres, self.hand_eye,
                                        min_motion_m=self.cfg.min_motion_m,
                                        max_ratio_spread=self.cfg.max_ratio_spread)
            s_flag = 'proprio_handeye'
        props = {}
        entities, traces = [], {}
        for role in ROLES:
            phrase = getattr(step, role)
            if phrase is not None and phrase.noun not in props:
                found = self.proposals.propose([obs.wrist[obs.t], obs.agent], phrase.noun, views[:2])
                props[phrase.noun] = dict(wrist=found[0], agent=found[1])
            e, tr = self._entity(role, phrase, obs, geo, iw, ia, props.get(phrase.noun if phrase else None),
                                 s, s_flag)
            entities.append(e)
            traces[role] = tr
        self.last_trace = dict(traces=traces, geometry=geo, proposals=props)
        meta = dict(schema=SCHEMA, t=obs.t, subgoal=subgoal, views=[list(v) for v in views], scale=s,
                    scale_info=_jsonable(info), tau=self.cfg.tau, reasons=[e.reason for e in entities])
        return WhereOutput(entities, format_line(entities), meta)


def _jsonable(value):
    if isinstance(value, dict):
        return {str(k): _jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(v) for v in value]
    if isinstance(value, (np.floating, np.integer)):
        return value.item()
    return value
