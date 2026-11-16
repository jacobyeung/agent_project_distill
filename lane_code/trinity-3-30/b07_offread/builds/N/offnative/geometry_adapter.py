"""Separate dense reconstruction coordinates from model prompt coordinates."""
from pathlib import Path

def relabel(path, indices):
    import numpy as np
    from student_pilot.ground_profiles import load_geometry
    from student_pilot.scene_state import FrameMap
    with np.load(path, allow_pickle=False) as z:
        arrays={k:z[k] for k in z.files}
    arrays['anchor_frame_indices']=np.asarray(indices)
    arrays['reference_source_frame']=np.asarray(indices[0])
    target=Path(path).with_name(Path(path).stem+'_m.npz')
    with target.open('xb') as f:np.savez(f,**arrays)
    geometry=load_geometry(target,FrameMap(tuple(indices)),'tower_scaled')
    return target,geometry.identity

def install_e2e():
    from e2e_reader.real import TowerG3T
    if getattr(TowerG3T,'_n4',False):return
    original=TowerG3T.__call__
    def call(self,frames):
        if 'geometry_anchor_indices' not in frames:return original(self,frames)
        value=original(self,dict(frames,anchor_indices=frames['geometry_anchor_indices']))
        indices=value['frame_indices'].copy()
        indices[value['anchor_slots']]=frames['anchor_indices']
        return dict(value,frame_indices=indices)
    TowerG3T.__call__=call
    TowerG3T._n4=True
