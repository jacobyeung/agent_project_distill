"""Clip identity and exact source-to-LM frame mapping; no question answers."""
from dataclasses import dataclass
import hashlib
import json
import re


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
                                    allow_nan=False).encode()).hexdigest()


def normalize_name(name):
    if not isinstance(name, str) or not name.strip() or any(
            ord(c) < 32 or ord(c) == 127 or c in '<>"' for c in name):
        raise ValueError('invalid_object_name')
    return ' '.join(name.lower().split())


@dataclass(frozen=True)
class FrameMap:
    """All arrays use 32 displayed slots; indices refer to decoded source frames."""
    source_indices: tuple
    dense_indices: tuple = ()
    anchor_slots: tuple = ()
    rgb_sha256: tuple = ()
    n_frames: int = 32

    def __post_init__(self):
        for key in ('source_indices', 'dense_indices', 'anchor_slots', 'rgb_sha256'):
            object.__setattr__(self, key, tuple(getattr(self, key)))
        x = self.source_indices
        if len(x) != self.n_frames or self.n_frames not in (32, 64, 94) or any(type(i) is not int or i < 0 for i in x):
            raise ValueError('expected_32_source_indices')
        if any(a >= b for a, b in zip(x, x[1:])):
            raise ValueError('source_indices_not_strictly_increasing')
        if self.rgb_sha256 and (len(self.rgb_sha256) != self.n_frames or any(
                not re.fullmatch('[0-9a-f]{64}', h) for h in self.rgb_sha256)):
            raise ValueError('expected_32_rgb_hashes')
        if bool(self.dense_indices) != bool(self.anchor_slots):
            raise ValueError('dense_frames_require_anchor_slots')
        if self.dense_indices:
            d, a = self.dense_indices, self.anchor_slots
            if (len(a) != self.n_frames or a[0] != 0 or any(type(i) is not int for i in d+a)
                    or any(i < 0 or i >= len(d) for i in a)
                    or any(i >= j for i, j in zip(d, d[1:]))
                    or any(i >= j for i, j in zip(a, a[1:]))
                    or tuple(d[i] for i in a) != x):
                raise ValueError('anchor_frame_mismatch')

    def require(self, indices):
        if tuple(indices) != self.source_indices:
            raise ValueError('source_frame_mismatch')


@dataclass(frozen=True)
class SceneState:
    video_sha256: str
    frames: FrameMap
    geometry_identity: str

    def __post_init__(self):
        if not re.fullmatch('[0-9a-f]{64}', self.video_sha256):
            raise ValueError('video_sha256_required')
        if not self.geometry_identity:
            raise ValueError('geometry_identity_required')

    @property
    def identity(self):
        return digest(dict(video=self.video_sha256, frames=self.frames.source_indices,
                           geometry=self.geometry_identity))
