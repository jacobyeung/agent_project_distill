"""One-based frame slots and row-owned state at the closed tool-call boundary."""
from dataclasses import dataclass
import hashlib
import numpy as np
from .scene_state import FrameMap


@dataclass
class GroundContext:
    heads: object
    geometry: object
    mdg_states: object
    fallback: object
    clip_key: str
    frame_map: object
    frames: dict
    batch: dict
    registry: object = None
    rereader: object = None
    verify_identity: str = ''

    def frame(self,slot,source_index,rgb_sha256):
        if type(slot) is not int or not 1 <= slot <= 32:
            raise ValueError('frame_slot_requires_1_to_32')
        if self.frame_map is None or not self.frame_map.rgb_sha256:
            raise ValueError('verify_requires_source_indices_and_rgb_hashes')
        self.frame_map.require(self.batch.get('hrp_frame_indices',()))
        if source_index != self.frame_map.source_indices[slot-1]:
            raise ValueError('candidate_source_frame_mismatch')
        image=self.frames[slot]
        a=np.asarray(image)
        if a.dtype != np.uint8 or a.shape != (480,640,3):
            raise ValueError('verify_requires_native_480_640_rgb')
        actual=hashlib.sha256(a.tobytes()).hexdigest()
        if actual != rgb_sha256 or actual != self.frame_map.rgb_sha256[slot-1]:
            raise ValueError('candidate_rgb_hash_mismatch')
        return image


def from_row(heads,geometry,batch,ground_backend=None,rereader=None):
    indices=batch.get('hrp_frame_indices',batch.get('frame_indices',()))
    if hasattr(indices,'tolist'):indices=indices.tolist()
    hashes=tuple(batch.get('frame_rgb_sha256',()))
    mapping=FrameMap(tuple(indices),rgb_sha256=hashes) if len(indices)==32 else None
    frames=batch.get('ground_frames',{})
    if rereader is not None:
        frames=rereader.config.frames
    if ground_backend is not None and mapping is not None:
        ground_backend.scene.frames.require(mapping.source_indices)
    from .ground_lifting import OwnGeometryAdapter
    lift_geometry=ground_backend.geometry if ground_backend is not None else OwnGeometryAdapter(geometry)
    return GroundContext(heads,lift_geometry,heads.mdg_states,None,batch.get('video_sha256',''),
                         mapping,frames,batch,rereader=rereader)


def closed_adapters(function):
    from functools import wraps
    @wraps(function)
    def wrapped(*args,**kwargs):
        from .mdg_lora import _MASK
        token=_MASK.set(None)
        try:return function(*args,**kwargs)
        finally:_MASK.reset(token)
    return wrapped
