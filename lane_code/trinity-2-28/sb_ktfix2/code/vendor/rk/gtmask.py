"""ScanNet GT-mask substitution for explicitly marked oracle checks."""
import argparse
from collections import defaultdict
import json
from pathlib import Path

import numpy as np
from scipy import ndimage

from .ground import mdg
from .programs import T, sha256, scene_key
from .sets import dev_items, labels

GT_ROOT = Path('/scratch/jjyeung/orch_cd/toolprog/work/gt/scannet')


def build_scene(source, names, output, frame_indices):
    names = sorted(set(map(mdg().label, names)))
    with np.load(source, allow_pickle=False) as z:
        inst, ids, native_labels = z['inst'], z['ids'], z['labels'].tolist()
        if 'frame_indices' in z and not np.array_equal(z['frame_indices'], frame_indices):
            raise ValueError('GT raster frame indices do not match heads')
    if inst.shape[0] != 32:
        raise ValueError('GT rasters must have 32 frames')
    masks = np.zeros((len(names), 32, 80, 112), bool)
    prob = np.zeros((len(names), 32), np.float32)
    uv = np.zeros((len(names), 32, 2), np.float32)
    for q, name in enumerate(names):
        matched = T.match_labels(name, native_labels)
        instance_ids = [i for i, l in zip(ids, native_labels) if l in matched]
        union = np.isin(inst, instance_ids)
        for k, mask in enumerate(union):
            h, w = mask.shape
            small = ndimage.zoom(mask, (80/h, 112/w), order=0, prefilter=False)
            masks[q, k] = small
            prob[q, k] = float(mask.mean() >= .002 and small.any())
            if small.any():
                r, c = np.unravel_index(np.argmax(ndimage.distance_transform_edt(small)), small.shape)
                uv[q, k] = np.rint([(c+.5)/112*1000, (r+.5)/80*1000])
    values = dict(prob=prob, clip_prob=np.ones(len(names), np.float32), frame_prob=prob.copy(),
                  iou=prob.copy(), uv=uv, area=masks.mean(axis=(-1, -2)).astype(np.float32), mask=masks)
    audit = dict(tau=.5, gt_substitution=True, source_gt=str(source), source_gt_sha256=sha256(source),
                 frame_indices=list(map(int, frame_indices)), mask_shape=[80, 112],
                 visibility='native instance union area >= 0.002', source='ScanNet GT rasters')
    mdg().save_npz(Path(output), names, values, audit)
    return audit


def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument('--out', required=True)
    parser.add_argument('--heads', required=True, help='Heads supplying the pinned source-frame selection')
    parser.add_argument('--gt-root', default=str(GT_ROOT))
    parser.add_argument('--scenes')
    args = parser.parse_args()
    grouped = defaultdict(set)
    selected = set(args.scenes.split(',')) if args.scenes else None
    for item in dev_items():
        if selected and item['scene'] not in selected:
            continue
        grouped[item['scene']].update(labels(item))
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    index = {}
    for scene, names in sorted(grouped.items()):
        key = scene_key('scannet', scene)
        head = Path(args.heads)/(key.replace('/', '__')+'.npz')
        with np.load(head, allow_pickle=False) as z:
            frames = z['anchor_frame_indices'] if 'anchor_frame_indices' in z else z['frame_indices']
        dest = out/(key.replace('/', '__')+'.npz')
        build_scene(Path(args.gt_root)/(scene+'.npz'), names, dest, frames)
        index[key] = dict(scene=key, scene_key=key, npz=dest.name,
                          frame_indices=frames.tolist(), gt_substitution=True)
        print(scene, flush=True)
    (out/'INDEX.json').write_text(json.dumps(index, indent=2)+'\n')


if __name__ == '__main__':
    main()
