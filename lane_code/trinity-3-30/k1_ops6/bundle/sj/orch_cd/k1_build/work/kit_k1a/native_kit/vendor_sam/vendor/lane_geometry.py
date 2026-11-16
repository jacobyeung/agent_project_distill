"""Minimal adaptation of the frozen geometry executor for arbitrary GT rasters."""
import numpy as np
import geomswap as G
import prog_v2 as V
import programs as PR

class Fused(G.Fused):
    def __init__(self,gt,*args,**kwargs):
        # The lane is deliberately sequential; the reference has module-level raster dimensions.
        G.H,G.W=gt.depth.shape[1:]
        super().__init__(gt,*args,**kwargs)

def install():
    G.install()
    V.Fused=Fused

def load_base(path,expected_indices):
    base=PR.GTSource(path)
    with np.load(path,allow_pickle=False) as z:
        if not np.array_equal(z['frame_indices'],expected_indices):raise ValueError('GT/PLAN frame mismatch')
        Ks=z['K_frames'].copy() if 'K_frames' in z else np.tile(base.K,(len(base.depth),1,1))
    if len(base.depth)!=32 or base.inst.shape!=base.depth.shape:raise ValueError('Unexpected GT raster layout')
    if not np.isfinite(Ks).all() or not np.isfinite(base.c2w[base.valid]).all():raise ValueError('Nonfinite GT calibration')
    return base,Ks

def ctx(base,depth,pose,Ks,policy,absolute=False):
    rule=('best1' if absolute else 'voteb5') if policy=='frozen' else 'all'
    geo=G.Geo(base,depth,pose,Ks,rule,('dc',) if policy=='frozen' else ())
    fixes='frameidx,axes,memory,extent,identity,round,gbox0'.split(',')
    # The reference vocabulary pools raw ScanNet labels; do not apply it to other datasets.
    if getattr(base,'dataset',None)=='scannet':fixes.append('vocab')
    return V.Ctx(geo,fixes,'B')
