"""Export accepted clicks and selected masks in the existing routed-kit schema."""
import argparse
from collections import defaultdict
import json
from pathlib import Path
import sys

import numpy as np

from .pointing import RKIT, write
from .selector import from_points, select


def imports():
    sys.path.insert(0, str(RKIT))
    from rk.ground import mdg
    from rk.programs import load_heads, assert_frame_indices
    return mdg(), load_heads, assert_frame_indices


def export_scene(out, scene, names, candidates, selections, frame_indices, audit=None, best_only=False):
    """Point-only exports use an explicit 3x3 proxy whose erosion leaves one pixel.

    SAM candidates preserve their full masks. Proxy masks encode click surfaces,
    not object extents; use actual masks for object size or surface-distance claims.
    """
    mdg, _, _ = imports()
    names = sorted(names)
    shape = (80, 112)
    masks = np.zeros((len(names), 32)+shape, bool)
    prob = np.zeros((len(names), 32), np.float32)
    uv = np.zeros((len(names), 32, 2), np.float32)
    proxy_count = 0
    for q, name in enumerate(names):
        selection = selections[name]
        for i in selection['candidate_indices']:
            c = candidates[name][i]
            k = c.frame-1
            if best_only and c.frame != selection['best_frame']:
                continue
            if c.mask is None:
                proxy_count += 1
                col, row = np.floor(np.asarray(c.uv)/1000*[shape[1], shape[0]]).astype(int)
                row, col = np.clip(row, 0, shape[0]-1), np.clip(col, 0, shape[1]-1)
                masks[q, k, max(0,row-1):min(shape[0],row+2), max(0,col-1):min(shape[1],col+2)] = True
            else:
                if c.mask.shape != shape:
                    raise ValueError('SAM/decoder masks must use the kit 80x112 grid')
                masks[q, k] = c.mask
            prob[q, k] = float(masks[q, k].any())
            uv[q, k] = np.rint(c.uv)
    values = dict(prob=prob, frame_prob=prob.copy(), clip_prob=np.ones(len(names), np.float32),
                  iou=prob.copy(), uv=uv, area=masks.mean(axis=(-1, -2)), mask=masks)
    metadata = dict(tau=.5, source='hrp_3d_consistency', frame_indices=list(map(int, frame_indices)),
                    proxy_click_masks=proxy_count, best_only=best_only, **(audit or {}))
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    filename = scene.replace('/', '__')+'.npz'
    mdg.save_npz(out/filename, names, values, metadata)
    write(out/(scene.replace('/', '__')+'.selection.json'), selections)
    return dict(scene=scene, scene_key=scene, npz=filename, frame_indices=list(map(int, frame_indices)))


def main():
    p = argparse.ArgumentParser(__doc__)
    inputs = p.add_mutually_exclusive_group(required=True)
    inputs.add_argument('--points')
    inputs.add_argument('--sam-raw', help='Cached SAM raw directory; uses frozen frame-presence gate')
    inputs.add_argument('--decoder-export', help='Mask-decoder export directory in rk INDEX.json form')
    p.add_argument('--pairs', help='Optional [{scene,obj},...] for SAM/decoder inputs; default dev 858 labels')
    p.add_argument('--heads', required=True)
    p.add_argument('--out', required=True)
    p.add_argument('--radius', type=float, default=.5)
    p.add_argument('--best-only', action='store_true')
    a = p.parse_args()
    mdg, load_heads, assert_frames = imports()
    if not a.points:
        from rk import sets
        from rk.programs import read_index, assert_export_frames
        from rk.sam3mask import tower, SAM3
        from .sources import sam_candidates, decoder_candidates
        if a.pairs:
            names_by_scene = defaultdict(set)
            for r in json.loads(Path(a.pairs).read_text()):
                names_by_scene[r['scene']].add(mdg.label(r['obj']))
        else:
            names_by_scene = sets.scene_labels('dev')
        if a.sam_raw:
            frozen = json.loads((SAM3/'tau_frozen.json').read_text())
        else:
            root, entries = read_index(a.decoder_export)
        index = {}
        for scene, names in sorted(names_by_scene.items()):
            head = Path(a.heads)/(scene.replace('/', '__')+'.npz')
            with np.load(head, allow_pickle=False) as z:
                expected = z['anchor_frame_indices'] if 'anchor_frame_indices' in z else z['frame_indices']
            geo = load_heads(head)
            if a.sam_raw:
                cache = tower().load_cache(a.sam_raw, scene)
                if any(cache['checkpoint'][k] != frozen['checkpoint'][k] for k in ('size', 'mtime_ns')):
                    raise ValueError('SAM checkpoint differs from its threshold')
                candidates = {n: sam_candidates(cache, n, float(frozen['tau'])) for n in names}
                audit = dict(input_source='sam3_instances', sam_raw=str(Path(a.sam_raw).resolve()))
            else:
                entry = entries[scene]
                if not np.array_equal(expected, entry['frame_indices']):
                    raise ValueError('Decoder frame indices differ from heads')
                native, values, audit = mdg.read_npz(root/entry['npz'])
                assert_export_frames(root/entry['npz'], audit, expected)
                if audit.get('gt_substitution'):
                    raise ValueError('Use the explicitly marked oracle runner for GT inputs')
                candidates = {n: decoder_candidates(values, native.index(n), float(audit['tau'])) if n in native else [] for n in names}
                audit = dict(input_source='mask_decoder', input_export=str((root/entry['npz']).resolve()))
            selected = {n: select(c, geo, a.radius) for n, c in candidates.items()}
            index[scene] = export_scene(a.out, scene, names, candidates, selected, expected,
                                        audit=audit, best_only=a.best_only)
        write(Path(a.out)/'INDEX.json', index)
        return
    grouped = defaultdict(lambda: defaultdict(list))
    for line in Path(a.points).read_text().splitlines():
        r = json.loads(line)
        grouped[r['scene']][mdg.label(r['obj'])].append(r)
    index = {}
    for scene, objects in sorted(grouped.items()):
        head = Path(a.heads)/(scene.replace('/', '__')+'.npz')
        rows = [r for values in objects.values() for r in values]
        expected = rows[0]['frame_indices']
        if any(r['frame_indices'] != expected or r['source_index'] != expected[r['frame']-1] for r in rows):
            raise ValueError('Point cache contains conflicting frame indices')
        assert_frames(head, expected)
        geo = load_heads(head)
        candidates = {name: from_points(values) for name, values in objects.items()}
        selected = {name: select(values, geo, a.radius) for name, values in candidates.items()}
        index[scene] = export_scene(a.out, scene, objects, candidates, selected, expected, best_only=a.best_only)
    write(Path(a.out)/'INDEX.json', index)


if __name__ == '__main__':
    main()
