"""The live-extraction gate, adapted from the independent review's live_parity.py.

Exit 0 PASS, 1 FAIL, 2 PENDING-INPUT. All paths are caller supplied.
The cache identifies the exact 64 RGB frames and LM anchors of the reference run.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import sys
import time

import numpy as np


def quat_R(q):
    x, y, z, w = np.asarray(q, float) / np.linalg.norm(q)
    return np.array([[1-2*(y*y+z*z), 2*(x*y-z*w), 2*(x*z+y*w)],
                     [2*(x*y+z*w), 1-2*(x*x+z*z), 2*(y*z-x*w)],
                     [2*(x*z-y*w), 2*(y*z+x*w), 1-2*(x*x+y*y)]])


def decode(video, indices):
    import av
    want, got = set(map(int, indices)), {}
    with av.open(str(video)) as container:
        stream = container.streams.video[0]
        stream.thread_count = 8
        for n, frame in enumerate(container.decode(stream)):
            if n in want:
                got[n] = frame.to_ndarray(format='rgb24')
            if n >= max(want):
                break
    if set(got) != want:
        raise ValueError('Video lacks cached native frames')
    return [got[int(i)] for i in indices]


def check(tree, device, weights_dir, video, cache, own, heads, *, context=None):
    sys.path.insert(0, str(Path(tree).resolve()))
    from tests.tower_live_grids import compare_auxiliary_grids
    paths = list(map(Path, (video, cache, own, heads)))
    missing = [str(p) for p in paths if not p.is_file()]
    if missing:
        return dict(status='PENDING-INPUT', expected=missing)
    with np.load(cache, allow_pickle=False) as z:
        ref = {k: z[k] for k in z.files}
    frames = decode(video, ref['frame_indices'])
    ident = [hashlib.sha256(np.ascontiguousarray(f).tobytes()).digest() for f in frames]
    identity = len(ident) == 64 and len(ref['frame_identity']) == 64 and all(
        bytes(r) == i for r, i in zip(ref['frame_identity'], ident))
    report = dict(frames=len(frames), frame_identity_sha256_rgb24_match=bool(identity))
    # Frame identity is an assertion, including when weights are absent.
    if not identity or list(frames[0].shape[:2]) != ref['source_hw'].tolist():
        return dict(report, status='FAIL', reason='Reference RGB inputs differ')
    from student_pilot.tower_read import FrozenG3TTower, WEIGHTS_SHA256, _hash
    weights, config = Path(weights_dir) / 'model.safetensors', Path(weights_dir) / 'config.json'
    if not weights.is_file() or weights.stat().st_size == 0:
        return dict(report, status='PENDING-INPUT', expected=[str(weights)], expected_sha256=WEIGHTS_SHA256)
    actual = _hash(weights)
    if actual != WEIGHTS_SHA256:
        return dict(report, status='PENDING-INPUT', expected=[str(weights)],
                    expected_sha256=WEIGHTS_SHA256, actual_sha256=actual, reason='Weights incomplete or ungoverned')
    import torch
    torch.set_num_threads(min(8, torch.get_num_threads()))
    tower = FrozenG3TTower(dict(weights_path=str(weights), config_path=str(config), device=device, dense_frames=64))
    batch = dict(tower_native_frames=frames, tower_frame_indices=ref['frame_indices'],
                 tower_anchor_slots=ref['anchor_slots'],
                 tower_lm_frame_indices=ref['frame_indices'][ref['anchor_slots']])
    gpu = str(device).startswith('cuda')
    if gpu:
        torch.cuda.reset_peak_memory_stats(device)
        torch.cuda.synchronize(device)
    t0 = time.monotonic()
    state = tower.run(batch)
    if gpu:
        torch.cuda.synchronize(device)
    elapsed = time.monotonic() - t0
    rot = [math.degrees(math.acos(np.clip((np.trace(quat_R(a[3:7]).T @ quat_R(b[3:7]))-1)/2, -1, 1)))
           for a, b in zip(state.raw_pose9, ref['raw_pose'])]
    trans = np.linalg.norm(state.raw_pose9[:, :3]-ref['raw_pose'][:, :3], axis=1) / np.maximum(
        np.linalg.norm(ref['raw_pose'][:, :3], axis=1), 1e-3)
    with np.load(own, allow_pickle=False) as v:
        _, scale = state.scaled_pose9(v['depth_grid'].astype(float))
    with np.load(heads, allow_pickle=False) as h:
        scale_ref = float(h['scale'])
    depth_rel = np.abs(state.depth_grid/ref['depth_grid']-1)
    fov = float(np.degrees(np.abs(state.raw_pose9[:, 7:9]-ref['raw_pose'][:, 7:9])).max())
    tol = (0.5, .03, .03, .02) if gpu else (.2, .01, .01, .01)
    auxiliary = compare_auxiliary_grids(state, ref, tol[2])
    report.update(auxiliary)
    report.update(rot_err_deg_max=max(rot), trans_rel_err_med=float(np.median(trans[1:])),
                  depth_rel_err_med=float(np.median(depth_rel)), fov_err_deg_max=fov,
                  scale=scale, scale_ref=scale_ref, scale_rel_err=abs(scale/scale_ref-1),
                  anchors_equal=bool(np.array_equal(state.anchor_slots, ref['anchor_slots'])),
                  tower_seconds=elapsed, weights_sha256=actual,
                  tower_peak_allocated_bytes=torch.cuda.max_memory_allocated(device) if gpu else None,
                  tolerances=dict(rot_deg=tol[0], trans_rel=tol[1], depth_rel=tol[2], scale_rel=tol[3], fov_deg=tol[0],
                                  points_rel=tol[2], depth_conf_rel=tol[2]))
    ok = (max(rot) <= tol[0] and report['trans_rel_err_med'] <= tol[1]
          and report['depth_rel_err_med'] <= tol[2] and report['scale_rel_err'] <= tol[3]
          and fov <= tol[0] and report['anchors_equal'] and auxiliary['auxiliary_grids_pass'])
    report['status'] = 'PASS' if ok else 'FAIL'
    if context is not None:
        context.update(tower=tower, state=state, batch=batch, frames=frames)
    return report


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for key in ('tree', 'weights-dir', 'video', 'cache', 'own', 'heads'):
        p.add_argument('--'+key, required=True, type=Path)
    p.add_argument('--device', default='cpu')
    args = p.parse_args()
    report = check(**vars(args))
    print(json.dumps(report, indent=2))
    return {'PASS': 0, 'FAIL': 1, 'PENDING-INPUT': 2}[report['status']]


if __name__ == '__main__':
    raise SystemExit(main())
