"""Single-thread CPU audit of each NPZ's poses, boxes, and native raster."""
import os
for key in ('OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS', 'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS'):
    os.environ[key] = '1'
os.environ['CUDA_VISIBLE_DEVICES'] = ''
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'
import itertools
import json
from pathlib import Path
import resource
import time
import numpy as np
from gt.v2 import full_box
from analyze_round5 import converted, angles, HYPOTHESES, sha

ROOT = Path(__file__).resolve().parent
OUT = ROOT.parent / 'cap/score_t2'
SIGNS = np.array(list(itertools.product((-1., 1.), repeat=3)))
EDGES = [(i, j) for i in range(8) for j in range(i+1, 8) if np.sum(SIGNS[i] != SIGNS[j]) == 1]


def read(path):
    return json.loads(Path(path).read_text())


def project_box(box, pose, K, raster, iid):
    """Pixel coordinates use edge origin; clip box edges at a positive near plane."""
    h, w = raster.shape
    center = np.array(box['center'])
    corners = center + (SIGNS * np.array(box['full_lengths']) / 2) @ np.array(box['axes'])
    world = np.vstack([center, corners])
    camera = (world-pose[:3, 3]) @ pose[:3, :3]
    front = camera[:, 2] > 1e-6
    xy = np.full((9, 2), np.nan)
    if front.any():
        q = camera[front] @ K.T
        xy[front] = q[:, :2] / q[:, 2:]
    uv = xy[0]
    in_grid = bool(front[0] and 0 <= uv[0] < w and 0 <= uv[1] < h)
    centroid_inside = bool(in_grid and raster[int(uv[1]), int(uv[0])] == iid)
    points = list(camera[1:][front[1:]])
    for i, j in EDGES:
        a, b = camera[i+1], camera[j+1]
        if (a[2] > 1e-6) != (b[2] > 1e-6):
            points.append(a + (b-a) * ((1e-6-a[2])/(b[2]-a[2])))
    bbox = None
    if points:
        q = np.array(points) @ K.T
        px = q[:, :2] / q[:, 2:]
        lo = np.maximum(px.min(0), [0, 0]); hi = np.minimum(px.max(0), [w, h])
        if np.all(hi > lo):
            bbox = [*lo.tolist(), *hi.tolist()]
    return dict(centroid_uv=uv.tolist() if front[0] else None,
                centroid_depth_m=float(camera[0, 2]), centroid_in_grid=in_grid,
                centroid_inside_mask=centroid_inside,
                corners_uv=[q.tolist() if ok else None for q, ok in zip(xy[1:], front[1:])],
                corners_depth_m=camera[1:, 2].tolist(), projected_bbox=bbox)


def box_metrics(projected, mask_bbox):
    if projected is None or mask_bbox is None:
        return dict(bbox_iou=0., mask_bbox_coverage=0.)
    p, m = np.asarray(projected), np.asarray(mask_bbox)
    intersection = float(np.prod(np.maximum(0, np.minimum(p[2:], m[2:])-np.maximum(p[:2], m[:2]))))
    pa, ma = float(np.prod(p[2:]-p[:2])), float(np.prod(m[2:]-m[:2]))
    return dict(bbox_iou=intersection/(pa+ma-intersection), mask_bbox_coverage=intersection/ma)


def summarize(rows):
    visible = [r for r in rows if r['visible_pixels'] > 0 and r['valid']]
    n = len(visible)
    metric = dict(visible_instance_frames=n)
    for key, fn in (
        ('centroid_inside', lambda r: r['centroid_inside_mask']),
        ('bbox_iou_gt_025', lambda r: r['bbox_iou'] > .25),
        ('bbox_iou_gt_05', lambda r: r['bbox_iou'] > .5),
        ('centroid_or_bbox_iou_gt_025', lambda r: r['centroid_inside_mask'] or r['bbox_iou'] > .25),
        ('bbox_coverage_ge_08', lambda r: r['mask_bbox_coverage'] >= .8),
    ):
        count = sum(fn(r) for r in visible)
        metric[key] = dict(count=count, share=count/n if n else None)
    metric['mean_bbox_iou'] = float(np.mean([r['bbox_iou'] for r in visible])) if n else None
    return metric


def pair_errors(a, b):
    i, j = np.triu_indices(len(a), 1)
    ar, br = a[:, :3, :3], b[:, :3, :3]
    ra = ar[i].transpose(0, 2, 1) @ ar[j]
    rb = br[i].transpose(0, 2, 1) @ br[j]
    rot = angles(ra @ rb.transpose(0, 2, 1))
    da, db = a[j, :3, 3]-a[i, :3, 3], b[j, :3, 3]-b[i, :3, 3]
    ta = np.einsum('ni,nij->nj', da, ar[i])
    tb = np.einsum('ni,nij->nj', db, br[i])
    trans = np.linalg.norm(ta-tb, axis=1)
    length = np.abs(np.linalg.norm(da, axis=1)-np.linalg.norm(db, axis=1))
    result = dict(pairs=len(i), definition='T_i^-1 T_j in the shared OpenCV camera axes; no scale fit')
    for k, v in [('rotation_deg', rot), ('translation_m', trans), ('baseline_length_difference_m', length)]:
        result[k] = dict(rms=float(np.sqrt(np.mean(v*v))), median=float(np.median(v)), max=float(v.max()))
    return result


def main():
    started = time.monotonic()
    r5 = read(OUT/'CAMERA_CONVENTIONS_T2.json')
    cameras = read(OUT/'CAMERAS_T2_R5.json')['captures']
    summaries, compressed_bytes = [], 0
    details_path = OUT/'NPZ_PROJECTIONS_R6.jsonl'
    with details_path.open('x') as detail:
        for old in r5['captures']:
            capture = old['capture']; dataset = old['dataset']
            with np.load(old['npz_path'], allow_pickle=False) as z:
                keys = ('inst', 'ids', 'labels', 'frame_indices', 'valid', 'c2w', 'K_frames', 'obb_centroid', 'obb_lengths', 'obb_axes')
                data = {k:z[k] for k in keys}
                compressed_bytes += sum(z.zip.getinfo(k+'.npy').compress_size for k in keys)
            inst = data['inst']; h, w = inst.shape[1:]
            # K_frames is already raster-scaled: principal point is near (W/2,H/2).
            # Record the evidence rather than fitting a scale to the boxes/masks.
            K = data['K_frames'].astype(float)
            principal = K[:, :2, 2]
            assert np.all(np.abs(principal-[w/2, h/2]) < np.array([w, h])*.1), (capture, principal)
            boxes = [full_box(data, index, dataset) for index in range(len(data['ids']))]
            hypotheses = dict(HYPOTHESES)
            if dataset == 'scannet':
                hypotheses['c2w_cv_scannet_half'] = {}
            sums = {}
            for hypothesis in hypotheses:
                poses = converted(data['c2w'], 'c2w_cv' if hypothesis == 'c2w_cv_scannet_half' else hypothesis)
                rows = []
                for f, raster in enumerate(inst):
                    for j, iid in enumerate(data['ids']):
                        ys, xs = np.nonzero(raster == iid)
                        bbox = [int(xs.min()), int(ys.min()), int(xs.max()+1), int(ys.max()+1)] if len(xs) else None
                        box = boxes[j][2] if hypothesis == 'c2w_cv_scannet_half' else boxes[j][0]
                        assert box is not None, (capture, int(iid))
                        row = dict(capture=capture, hypothesis=hypothesis, frame=f+1,
                                   source_index=int(data['frame_indices'][f]), instance_id=int(iid),
                                   label=str(data['labels'][j]), valid=bool(data['valid'][f]),
                                   visible_pixels=len(xs), mask_bbox=bbox)
                        row.update(project_box(box, poses[f], K[f], raster, int(iid)))
                        row.update(box_metrics(row['projected_bbox'], bbox))
                        detail.write(json.dumps(row, allow_nan=False, separators=(',', ':'))+'\n')
                        rows.append(row)
                sums[hypothesis] = dict(overall=summarize(rows),
                    by_frame=[dict(frame=f+1, source_index=int(data['frame_indices'][f]),
                                   **summarize([r for r in rows if r['frame']==f+1])) for f in range(len(inst))],
                    by_instance=[dict(instance_id=int(iid), label=str(label),
                                     **summarize([r for r in rows if r['instance_id']==iid])) for iid, label in zip(data['ids'], data['labels'])])
            a = np.asarray(next(r['geometry']['camera_to_world_metric'] for r in cameras[capture] if r['geometry']))
            invariant = old['hypotheses']['c2w_cv']['pairwise_rotation_invariant']
            summaries.append(dict(capture=capture, dataset=dataset, raster_hw=[h, w],
                K_scale_xy=[1., 1.], K_principal_xy_min=principal.min(0).tolist(), K_principal_xy_max=principal.max(0).tolist(),
                K_scale_evidence='K_frames already at native raster scale; principal point within 10% of raster center; no fitted scaling or portrait rotation',
                instances=len(data['ids']), hypotheses=sums,
                reader_pair_errors=pair_errors(a, data['c2w']),
                reader_rigid_fit=old['hypotheses']['c2w_cv']['rigid'],
                fixed_axis_exclusion=invariant))
            cv=sums['c2w_cv']['overall']
            print(json.dumps(dict(capture=capture, centroid=cv['centroid_inside']['share'],
                                  bbox025=cv['bbox_iou_gt_025']['share'], either=cv['centroid_or_bbox_iou_gt_025']['share'])), flush=True)
    result = dict(schema='npz-self-consistency-r6', captures=summaries,
        definitions=dict(visible='valid frame and at least one pixel bearing this instance ID; equal instance-frame weight',
            extent='adapter gt/v2.py unchanged: ARKit full, ScanNet full plus half diagnostic, ScanNet++ doubled',
            clipping='12 box edges clipped at z=1e-6 before projecting; bbox clipped to raster; positive-depth center and eight corners recorded',
            pixel='edge-origin coordinates; floor projected centroid to native raster cell',
            hypotheses='c2w_cv baseline, c2w_gl camera Y/Z flip, w2c_cv pose inverse, w2c_gl inverse plus camera flip',
            limits='OBB centers can fall in holes or behind occluders; projected boxes enclose more than visible object masks. Internal NPZ agreement does not independently hash-bind the reader RGB.'),
        projection_details=str(details_path),
        provenance={str(p):sha(p) for p in (Path(__file__), ROOT/'gt/v2.py', OUT/'CAMERA_CONVENTIONS_T2.json')},
        resources=dict(seconds=time.monotonic()-started, max_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                       compressed_npz_member_bytes=compressed_bytes, threads=1, gpu_used=False))
    with (OUT/'NPZ_SELF_CONSISTENCY_R6.json').open('x') as f:
        json.dump(result, f, indent=2, allow_nan=False); f.write('\n')


if __name__ == '__main__':
    main()
