"""Clean-room T1 raster rebuild: r1313 scene assets -> dose_pool t1_gt npz."""
import ctypes
ctypes.CDLL(None).prctl(41, 1, 0, 0, 0)  # PR_SET_THP_DISABLE: THP compaction stalls on this node
import numpy as np, json, hashlib, sys, time
sys.path.insert(0, '/scratch/jjyeung/orch_cd/integ_v3/work/generator')
from derivgen.native import native_mesh
from raycast_cr import first_hits

def build(asset_dir, out_path, hw=(240, 320)):
    c = np.load(f'{asset_dir}/official_cameras.npz')
    FI, F, V = native_mesh(f'{asset_dir}/instance_mesh.npz', raster_compatible=True)
    meta = json.load(open(f'{asset_dir}/instances.json'))
    sg = {g['id']: g for g in meta['segGroups']}
    lscale = 2.0 if meta.get('provider_axesLengths') == 'half_extents' else 1.0
    H, W = hw
    raster = c['raster_hw']
    scale = np.diag([W / float(raster[1]), H / float(raster[0]), 1.])
    scaled = np.asarray([scale @ K for K in c['intrinsics']])
    depth = np.zeros((32, H, W), np.float32); inst = np.full((32, H, W), -1, np.int32)
    for f in range(32):
        d, fc = first_hits(V, F, c['camera_poses'][f], scaled[f], hw, off=0.5, mode='z')
        hit = fc >= 0
        depth[f] = np.where(hit, d, 0).astype(np.float32)
        inst[f][hit] = FI[fc[hit]]
    inst[depth <= 0] = -1
    ids = np.array([g['id'] for g in meta['segGroups']], dtype=np.int32)
    with open(out_path, 'xb') as fh:
        np.savez_compressed(fh, depth=depth, inst=inst, K=scaled[0], K_frames=scaled,
            c2w=c['camera_poses'], valid=np.ones(32, dtype=bool), ids=ids,
            labels=np.array([sg[i]['label'] for i in ids]),
            obb_centroid=np.array([sg[i]['obb']['centroid'] for i in ids]),
            obb_lengths=np.array([[lscale * x for x in sg[i]['obb']['axesLengths']] for i in ids]),
            obb_axes=np.array([np.asarray(sg[i]['obb']['normalizedAxes'], float).reshape(9) for i in ids]),
            frame_indices=c['indices'])
    return hashlib.sha256(open(out_path, 'rb').read()).hexdigest()

if __name__ == '__main__':
    t = time.time(); h = build(sys.argv[1], sys.argv[2]); print(h, '%.1fs' % (time.time() - t))
