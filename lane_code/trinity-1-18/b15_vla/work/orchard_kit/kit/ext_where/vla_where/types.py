"""The run-time input whitelist (schema 6.1) and the where record (schema 5).

Observation holds exactly the whitelisted inputs: the instruction, the time index t, the agentview RGB at t, the wrist
RGB at t and at the history steps, and the raw 8-D proprio at those steps. The hand-eye constant is provider
configuration. Nothing else reaches the provider: no simulator state, GT depth, segmentation or poses, no agentview
intrinsics or extrinsics, no episode, task or init-state id, no future frame. GT backends for the `gt_where` check and
tests read their side channel (backends/gt.py GTStore), never the Observation.

The 18 numbers per entity (schema 5.2), entity 0 = target, entity 1 = place:
  0      presence: max over the two views of P(yes)
  1      valid: grounded in >= 1 view, lifted, and the cross-view rule passed when both views ground it
  2-3    uv_agent: uv01 projection of the reported point into the agentview image (G3T frame and K), clipped to [-1, 2];
         (-1, -1) when the point lies behind the camera (z <= 0.01 in G3T units)
  4-5    uv_wrist: the same for the wrist image
  6-8    X_wrist: metres, true OpenCV wrist camera frame at t: s M X_g (M = diag(-1, 1, 1) on mirrored G3T frames)
  9-11   reach_base: metres, the point minus the end-effector position in robot base axes
  12-14  size: metres, p2-p98 principal-axis extents of the reported view's lifted points, largest first, each >= 0.02
  15-17  scale_source one-hot [proprio_handeye, vc_ratio, metric_test]; all zeros = metric scale unknown
valid = 0: the whole row is zero, presence included. valid = 1 and scale unknown: cols 0-5 filled, cols 6-17 zero.
"""
from dataclasses import asdict, dataclass, field
from typing import Optional

import numpy as np

SCHEMA = 'vla_schema_v2'
F = 18
E = 2
ROLES = ('target', 'place')
VIEWS = ('agent', 'wrist')
SCALE_SOURCES = ('proprio_handeye', 'vc_ratio', 'metric_test')
REASONS = ('ok', 'no_phrase', 'low_presence', 'no_point', 'no_lift', 'cross_view', 'behind_wrist', 'no_scale',
           'withheld')
SLICES = dict(presence=slice(0, 1), valid=slice(1, 2), uv_agent=slice(2, 4), uv_wrist=slice(4, 6),
              X_wrist=slice(6, 9), reach_base=slice(9, 12), size=slice(12, 15), scale_source=slice(15, 18))


def _image(value, name):
    a = np.asarray(value)
    if a.dtype != np.uint8 or a.ndim != 3 or a.shape[2] != 3:
        raise ValueError(f'{name} must be uint8 HxWx3 RGB')
    return a


@dataclass(frozen=True)
class Observation:
    """Whitelisted inputs at time index t. wrist and proprio map integer steps to the wrist RGB and the raw 8-D proprio
    (end-effector position 3, axis-angle 3, gripper joints 2); both must hold t. Extra keys are allowed (the online
    buffer keeps a window); the provider reads only t and the history steps of schema 6.2."""
    instruction: str
    t: int
    agent: np.ndarray
    wrist: dict
    proprio: dict

    def __post_init__(self):
        if not isinstance(self.instruction, str) or type(self.t) is not int or self.t < 0:
            raise ValueError('Observation needs a str instruction and an int t >= 0')
        _image(self.agent, 'agent')
        for k, v in self.wrist.items():
            if type(k) is not int or k > self.t:
                raise ValueError('wrist steps must be ints <= t (no future frames)')
            _image(v, f'wrist[{k}]')
        for k, v in self.proprio.items():
            if type(k) is not int or k > self.t or np.asarray(v).shape != (8,):
                raise ValueError('proprio steps must be ints <= t with 8-D values')
        if self.t not in self.wrist or self.t not in self.proprio:
            raise ValueError('Observation needs the wrist frame and proprio at t')


@dataclass
class Entity:
    role: str
    phrase: Optional[str] = None
    noun: Optional[str] = None
    presence: float = 0.0
    valid: bool = False
    reason: str = 'no_phrase'
    uv_agent: Optional[list] = None
    uv_wrist: Optional[list] = None
    X_wrist: Optional[list] = None      # metres; None when the scale is unknown
    reach_base: Optional[list] = None
    size: Optional[list] = None
    scale_source: Optional[str] = None  # None = metric scale unknown
    withheld: bool = False
    diag: dict = field(default_factory=dict)  # logged, never fed to the head

    @property
    def metric(self):
        return self.valid and self.scale_source is not None

    def vector(self):
        return self.vector64().astype(np.float32)

    def vector64(self):
        """The same numbers in float64 (conformance checks to 1e-6 before the float32 cast)."""
        v = np.zeros(F, dtype=np.float64)
        if not self.valid or self.withheld:
            return v
        v[0], v[1] = self.presence, 1.0
        v[SLICES['uv_agent']], v[SLICES['uv_wrist']] = self.uv_agent, self.uv_wrist
        if self.metric:
            v[SLICES['X_wrist']], v[SLICES['reach_base']], v[SLICES['size']] = self.X_wrist, self.reach_base, self.size
            v[15 + SCALE_SOURCES.index(self.scale_source)] = 1.0
        return v

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls, d):
        return cls(**d)


@dataclass
class WhereOutput:
    entities: list
    line: str
    meta: dict = field(default_factory=dict)

    @property
    def withheld(self):
        return any(e.withheld for e in self.entities)

    def vector(self):
        """[2, 18] float32 (schema 1 `where` before batching)."""
        return np.stack([e.vector() for e in self.entities])

    def vector64(self):
        return np.stack([e.vector64() for e in self.entities])

    def mask(self):
        """[2] bool (schema 3): valid AND not withheld."""
        return np.array([bool(e.valid and not e.withheld) for e in self.entities])

    def by_role(self, role):
        return next(e for e in self.entities if e.role == role)

    def to_dict(self):
        return dict(entities=[e.to_dict() for e in self.entities], line=self.line, meta=self.meta)

    @classmethod
    def from_dict(cls, d):
        return cls([Entity.from_dict(e) for e in d['entities']], d['line'], d.get('meta', {}))
