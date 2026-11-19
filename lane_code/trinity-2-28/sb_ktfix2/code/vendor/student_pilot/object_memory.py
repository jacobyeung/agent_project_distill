"""Bounded clip object memory. Exact legacy surfaces remain separate from samples."""
from copy import deepcopy
from dataclasses import dataclass, field
from enum import Enum
import numpy as np
from .scene_state import normalize_name


class State(str, Enum):
    RESOLVED = 'resolved'
    NOT_SEEN = 'not_seen'
    AMBIGUOUS = 'ambiguous'
    OCCLUDED = 'occluded'
    INVALID_GEOMETRY = 'invalid_geometry'


@dataclass
class ObjectSlot:
    name: str
    state: State
    reason: str
    result: dict
    candidates: list = field(default_factory=list)
    features: dict = field(default_factory=dict)
    verdict: dict = field(default_factory=dict)
    frames: tuple = ()
    masks: object = None
    probabilities: object = None
    tau: float = .5
    merged_points: object = None
    association_samples: object = None
    candidate: object = None
    values: object = None
    uncertainty: dict = field(default_factory=dict)
    visible_extent: object = None

    def finalize(self):
        arrays = [np.asarray(v, dtype=float).reshape(-1, 3)
                  for v in self.result.get('points', {}).values() if len(v)]
        self.merged_points = np.concatenate(arrays) if arrays else np.empty((0, 3))
        n = len(self.merged_points)
        self.association_samples = self.merged_points[np.linspace(0, n-1, min(512, n), dtype=int)] if n else self.merged_points.copy()
        self.frames = tuple(self.result.get('frames', []))
        self.visible_extent = self.result.get('size')
        self.uncertainty = dict(spread=self.result.get('spread'), semantic='verify_only')
        return self


class ClipMemory:
    def __init__(self, max_slots=128):
        if not 1 <= max_slots <= 128:
            raise ValueError('slot_cap_outside_1_128')
        self.max_slots = max_slots
        self.scene_identity = None
        self.slots = {}
        self.hits = self.misses = self.overflows = 0

    def bind(self, scene):
        clip_identity=(scene.video_sha256,scene.frames.source_indices)
        self.scene_identity = clip_identity
        self.video_sha256 = scene.video_sha256

    def key(self, name, config_hash, scene=None):
        clip = (scene.video_sha256, scene.frames.source_indices) if scene is not None else self.scene_identity
        return clip, normalize_name(name), config_hash

    def get(self, name, config_hash, *, scene=None):
        slot = self.slots.get(self.key(name, config_hash, scene))
        self.hits += slot is not None
        self.misses += slot is None
        return deepcopy(slot)

    def put(self, name, config_hash, slot, *, scene=None):
        key = self.key(name, config_hash, scene)
        if key not in self.slots and sum(k[0] == key[0] for k in self.slots) >= self.max_slots:
            self.overflows += 1
            return False  # Capacity limits storage; the requested name still runs.
        self.slots[key] = deepcopy(slot)
        return True
