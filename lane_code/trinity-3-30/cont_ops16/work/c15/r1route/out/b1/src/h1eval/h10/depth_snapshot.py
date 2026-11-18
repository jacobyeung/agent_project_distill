"""Persist own geometry after generation, outside the reader's audited decision path."""
import hashlib
from pathlib import Path
import numpy as np


def save(output, item_id, mode, state):
    geometry = state.get('geometry')
    if geometry is None:
        from h1eval.perception import own_profile
        geometry = own_profile(state['heads'], state['frames'])
    heads = state['heads']
    key = hashlib.sha256((item_id + '\0' + mode).encode()).hexdigest()
    path = Path(output) / 'own_depth' / (key + '.npz')
    path.parent.mkdir(parents=True, exist_ok=True)
    np.savez(path, depth_grid=np.asarray(geometry.depth_grid, dtype=np.float16),
             grid_uv=np.asarray(geometry.grid_uv), pose9=np.asarray(heads.pose9),
             gravity=np.asarray(heads.gravity), K=geometry.contract.K,
             canvas_to_source=geometry.contract.canvas_to_source,
             camera_to_world=geometry.contract.camera_to_world,
             anchor_frame_indices=geometry.contract.frame_map.source_indices)
    return dict(path=str(path.relative_to(output)), sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                dtype='float16', shape=list(geometry.depth_grid.shape))
