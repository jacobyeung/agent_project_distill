"""Camera fixtures produced from explicit synthetic geometry."""
import numpy as np
from generator.derivgen_v7.derivgen.camera_rows import _row,_Geometry


def camera_row(frames=None,kind='camera_displacement'):
    count=len(frames) if frames is not None else 32
    codes=np.tile([0.,0.,0.,0.,0.,0.,1.,.8,1.],(count,1))
    for i in range(count):
        angle=(i/24)*np.pi/4;distance=i/24
        codes[i,:3]=[-np.cos(angle)*distance,0.,-np.sin(angle)*distance]
        codes[i,3:7]=[0.,-np.sin(angle/2),0.,np.cos(angle/2)]
    clip=dict(dataset='d1',scene='fixture_clean',recording_id='fixture',
        frames=[dict((frames[i] if frames else {}),source_index=i*2) for i in range(count)],
        gt_pose9=codes.tolist(),gt_up=[0.,-1.,0.],rgb_manifest=dict(path='fixture-only',sha256='a'*64))
    return _row(clip,kind,1,25,_Geometry(clip).pair(1,25))
