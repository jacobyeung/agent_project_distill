"""Read one dev-S1 head file for gt_ceiling after an explicit GT frame-index join."""
from pathlib import Path
import numpy as np

def tower_raw(root,dataset,scene,group,depth,expected_indices,hw=(240,320)):
    if group not in ('g3s32','g3s64') or depth not in ('vcd','g3t'):raise ValueError('Explicit group and depth required')
    if dataset not in ('scannet','scannetppv2','scannetpp','arkitscenes') or Path(scene).name!=scene:raise ValueError('Invalid scene')
    path=Path(root)/('heads_'+group+('_vcd' if depth=='vcd' else ''))/(dataset+'__'+scene+'.npz')
    with np.load(path,allow_pickle=False) as z:
        if expected_indices is None or not np.array_equal(z['anchor_frame_indices'],expected_indices):raise ValueError('GT/tower anchor indices differ; re-render or explicitly join before scoring')
        if str(z['layout'])!='per_frame':raise ValueError('Expected per_frame heads')
        grid=z['depth_grid'].astype(np.float32);r=z['r_grav'];t=z['t_grav'];fov=z['fov_hw']
    H,W=hw;G=grid.shape[1];ys,xs=np.mgrid[0:H,0:W]
    x=np.clip((xs+.5)/W*(G-1),0,G-1);y=np.clip((ys+.5)/H*(G-1),0,G-1)
    x0,y0=np.floor(x).astype(int),np.floor(y).astype(int);x1,y1=np.minimum(x0+1,G-1),np.minimum(y0+1,G-1);fx,fy=x-x0,y-y0
    D=(grid[:,y0,x0]*(1-fx)*(1-fy)+grid[:,y0,x1]*fx*(1-fy)+grid[:,y1,x0]*(1-fx)*fy+grid[:,y1,x1]*fx*fy).astype(np.float32)
    c2w=np.tile(np.eye(4),(32,1,1));c2w[:,:3,:3]=r;c2w[:,:3,3]=t
    K=np.tile(np.eye(3),(32,1,1));K[:,0,0]=W/2/np.tan(fov[:,1]/2);K[:,1,1]=H/2/np.tan(fov[:,0]/2);K[:,0,2]=W/2;K[:,1,2]=H/2
    return D,c2w,K
