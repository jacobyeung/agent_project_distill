"""Unmodified audit functions extracted from staged round-6/9 sources."""

import hashlib, json, itertools, zlib

from pathlib import Path

from collections import defaultdict

import numpy as np

from scipy import ndimage

LUT=np.array([int(i).bit_count() for i in range(256)],dtype=np.uint8)

MODES=['same','shift_-2','shift_-1','shift_+1','shift_+2','rot180','flip_h','flip_v']

SIGNS=np.array(list(itertools.product((-1.,1.), repeat=3)))

EDGES=[(i,j) for i in range(8) for j in range(i+1,8) if np.sum(SIGNS[i]!=SIGNS[j])==1]

# Source: /scratch/jjyeung/orch_n30/cont_ops24_c/gbuild/project_round6.py

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

# Source: /scratch/jjyeung/orch_n30/cont_ops24_c/gbuild/project_round6.py

def box_metrics(projected, mask_bbox):
    if projected is None or mask_bbox is None:
        return dict(bbox_iou=0., mask_bbox_coverage=0.)
    p, m = np.asarray(projected), np.asarray(mask_bbox)
    intersection = float(np.prod(np.maximum(0, np.minimum(p[2:], m[2:])-np.maximum(p[:2], m[:2]))))
    pa, ma = float(np.prod(p[2:]-p[:2])), float(np.prod(m[2:]-m[:2]))
    return dict(bbox_iou=intersection/(pa+ma-intersection), mask_bbox_coverage=intersection/ma)

# Source: /scratch/jjyeung/orch_n30/cont_ops24_c/gbuild/analyze_round9.py

def median(v):
    return float(np.median(v)) if len(v) else None

# Source: /scratch/jjyeung/orch_n30/cont_ops24_c/gbuild/analyze_round9.py

def packed(mask):
    return np.packbits(mask.reshape(-1)),int(mask.sum())

# Source: /scratch/jjyeung/orch_n30/cont_ops24_c/gbuild/analyze_round9.py

def iou(a,aa,b,ba):
    inter=int(LUT[np.bitwise_and(a,b)].sum())
    union=aa+ba-inter
    return inter/union if union else 0.

# Source: /scratch/jjyeung/orch_n30/cont_ops24_c/gbuild/analyze_round9.py

def variants(mask):
    out={'same':mask,'rot180':np.rot90(mask,2),'flip_h':np.fliplr(mask),'flip_v':np.flipud(mask)}
    if mask.shape==(320,240):
        out.update(rot90_ccw=np.rot90(mask,1),rot90_cw=np.rot90(mask,-1))
    return out

# Source: /scratch/jjyeung/orch_n30/cont_ops24_c/gbuild/analyze_round9.py

def summary(frames,modes):
    result={}
    for mode in modes:
        rows=[r for r in frames if r['gt_visible'] and r['best_iou'][mode] is not None]
        vals=[r['best_iou'][mode] for r in rows]
        base=[r['best_iou']['same'] for r in rows]
        active=[r for r in rows if r['proposal_count']>0]
        own_visible=[r for r in frames if r['gt_pixels_by_mode'][mode] and r['best_iou'][mode] is not None]
        result[mode]=dict(n=len(rows),median=median(vals),paired_same_median=median(base),
            median_gain=(median(vals)-median(base)) if vals else None,
            n_with_proposals=len(active),median_with_proposals=median([r['best_iou'][mode] for r in active]),
            all_anchor_median=median([r['best_iou'][mode] for r in frames if r['best_iou'][mode] is not None]),
            own_visible_n=len(own_visible),own_visible_median=median([r['best_iou'][mode] for r in own_visible]),
            fraction_gt_05=sum(v>.5 for v in vals)/len(vals) if vals else None)
    alternatives=[m for m in modes if m!='same' and result[m]['median'] is not None]
    best=max(alternatives,key=lambda m:result[m]['median']) if alternatives else None
    gain=max(alternatives,key=lambda m:result[m]['median_gain']) if alternatives else None
    same=result['same']['median']
    return dict(modes=result,same_median=same,best_alternative=best,
                best_alternative_median=result[best]['median'] if best else None,
                best_mode=max([m for m in modes if result[m]['median'] is not None],key=lambda m:result[m]['median']) if same is not None else None,
                gain_mode=gain,max_paired_median_gain=result[gain]['median_gain'] if gain else None,
                changed=bool(gain and result[gain]['median_gain']>.2),
                changed_vs_full_same=bool(best and same is not None and result[best]['median']-same>.2))

# Source: /scratch/jjyeung/orch_n30/cont_ops24_c/gbuild/analyze_round9.py

def analyze_object(obj,key,iid,raster,sources,arm):
    modes=MODES+(['rot90_ccw','rot90_cw'] if raster.shape[1:]==(320,240) else [])
    masks=[variants(frame==iid) for frame in raster]
    truth=[{m:packed(a) for m,a in row.items()} for row in masks]
    proposals=defaultdict(list)
    if arm=='points_selected':
        for f,m in obj['selected_masks'].items(): proposals[int(f)-1].append(dict(mask=m))
    else:
        for p in obj['proposals']:
            k=int(p['frame'])-1
            assert 0<=k<32
            if 'source_index' in p: assert p['source_index']==sources[k]
            proposals[k].append(p)
    frames=[]
    for k in range(32):
        prepared=[]
        for p in proposals[k]:
            raw=unrle(p['mask'])
            shapes={a.shape for a in masks[k].values()}
            prepared.append({shape:packed(resize(raw,shape)) for shape in shapes})
        values={};areas={};winners={};gt_slots={}
        for mode in modes:
            shift=int(mode.split('_')[1]) if mode.startswith('shift_') else 0
            j=k+shift; transform='same' if shift else mode
            gt_slots[mode]=j if 0<=j<32 else None
            if not 0<=j<32:
                values[mode]=None;areas[mode]=None;winners[mode]=None;continue
            target,area=truth[j][transform];shape=masks[j][transform].shape
            vals=[iou(target,area,*p[shape]) for p in prepared]
            values[mode]=max(vals,default=0.);areas[mode]=area
            winners[mode]=int(np.argmax(vals)) if vals else None
        frames.append(dict(anchor_slot=k,reader_frame=k+1,source_index=sources[k],gt_visible=areas['same']>0,
                           proposal_count=len(prepared),best_iou=values,gt_pixels_by_mode=areas,
                           gt_slot_by_mode=gt_slots,best_proposal_index_in_frame=winners))
    return dict(key=key,arm=arm,instance_id=iid,frames=frames,summary=summary(frames,modes))

# Source: /scratch/jjyeung/orch_n30/cont_ops24_c/gbuild/gpkg/runtime/c.py

def unrle(value):
    h, w = value['size']; counts = value['counts']
    if value.get('order') != 'F' or any(type(n) is not int or n < 0 for n in counts) or sum(counts) != h*w:
        raise ValueError('invalid RLE')
    return np.repeat(np.arange(len(counts)) % 2, counts).astype(bool).reshape((h, w), order='F')

# Source: /scratch/jjyeung/orch_n30/cont_ops24_c/gbuild/work/payload/tree/student_pilot/routed_features.py

def resize(mask, shape):
    mask = np.asarray(mask, bool)
    if mask.ndim != 2 or not all(mask.shape):
        raise ValueError("Routed policy requires a nonempty two-dimensional mask")
    return (mask.copy() if mask.shape == shape else
            ndimage.zoom(mask, (shape[0]/mask.shape[0], shape[1]/mask.shape[1]), order=0, prefilter=False))

# Source: /scratch/jjyeung/orch_n30/cont_ops24_c/gbuild/gpkg/capture_io.py

class Records:
    def __init__(self, path, receipt):
        self.path = Path(path)
        if not isinstance(receipt, dict):
            receipt = json.loads(Path(receipt).read_text())
        expected = receipt.get('sha256', receipt.get('capture_sha256'))
        if not expected:
            raise ValueError('capture raw SHA256 is required')
        with self.path.open('rb') as f:
            actual = hashlib.file_digest(f, 'sha256').hexdigest()
        if actual != expected:
            raise ValueError('capture raw SHA256 differs')
        size = self.path.stat().st_size
        expected_size = receipt.get('bytes', receipt.get('capture_bytes'))
        if expected_size is not None and expected_size != size:
            raise ValueError('capture raw byte count differs')
        self.report = dict(raw_sha256=actual, raw_bytes=size, sha256_verified=True,
                           salvaged=False, records=0, discarded_partial_line_bytes=0)

    def __iter__(self):
        codec = zlib.decompressobj(wbits=16+15)
        pending = b''
        with self.path.open('rb') as f:
            while True:
                chunk = f.read(1024*1024)
                if not chunk:
                    break
                if codec.eof:
                    raise ValueError('unexpected bytes after gzip stream')
                # Bound each decompression allocation; a record may span chunks.
                while chunk:
                    data = codec.decompress(chunk, 1024*1024)
                    chunk = codec.unconsumed_tail
                    pending += data
                    lines = pending.split(b'\n')
                    pending = lines.pop()
                    for line in lines:
                        row = json.loads(line)
                        self.report['records'] += 1
                        yield row
                if codec.unused_data:
                    raise ValueError('unexpected bytes after gzip stream')
        self.report.update(salvaged=not codec.eof, discarded_partial_line_bytes=len(pending))
        if codec.eof and pending:
            raise ValueError('complete capture lacks final JSONL newline')
