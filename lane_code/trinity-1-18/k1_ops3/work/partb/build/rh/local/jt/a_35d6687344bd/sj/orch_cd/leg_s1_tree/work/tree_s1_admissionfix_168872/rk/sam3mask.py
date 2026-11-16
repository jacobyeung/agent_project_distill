"""SAM 3 zero-shot masks (ttower raw caches) in the mdg-export schema, for the NO-GO fallback reads.

Default presence is SAM 3's own frozen accept rule (presence x top instance probability >= tau, nonempty top mask).
`--presence MDG_EXPORT` swaps in an MDG export's per-frame probabilities and tau (the S3P step-0 combination:
MDG presence x SAM 3 placement); SAM 3 then supplies only the top-instance mask and click of every frame.
Inference outputs only: no ground truth is read.
"""
import argparse
from functools import lru_cache
import importlib.util
import json
from pathlib import Path

import numpy as np
from scipy import ndimage

from .ground import mdg
from .programs import read_index, sha256
from . import sets

SAM3 = Path('/scratch/jjyeung/orch_cd/ttower/work/sam3')
SHAPE = (80, 112)


@lru_cache(maxsize=1)
def tower():
    spec = importlib.util.spec_from_file_location('_ttower_sam3_common', SAM3/'common.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


MIN_SCORE = [0.]   # --min-instance-score: SAM 3's native gate (0.5) drops weaker proposals before any selection


def instance_masks(record):
    """[(mask at SHAPE, instance score)] in descending score order, at or above the instance-score floor."""
    result = []
    for inst in sorted(record.get('instances') or [], key=lambda i: -float(i['score'])):
        if float(inst['score']) < MIN_SCORE[0]:
            continue
        full = tower().rle_decode(inst['mask'])
        h, w = full.shape
        result.append((ndimage.zoom(full, (SHAPE[0]/h, SHAPE[1]/w), order=0, prefilter=False), float(inst['score'])))
    return result


def choose(instances, selector=None):
    """Top-scoring instance without a selector. With a selector mask: the instance of highest IoU with it, or
    None (frame not visible) when the selector is empty or no instance overlaps it."""
    if selector is None:
        return instances[0], False
    ious = [(m & selector).sum()/max((m | selector).sum(), 1) for m, _ in instances]
    best = int(np.argmax(ious))
    return (instances[best], True) if selector.any() and ious[best] > 0 else (None, False)


def build_scene(cache, names, tau, presence=None, select='top'):
    """presence: (names, values) of an MDG export for the same scene and frames, or None.
    select='iou' picks, per frame, the SAM 3 instance that best overlaps the presence export's own mask."""
    q_n = len(names)
    masks = np.zeros((q_n, 32)+SHAPE, bool)
    prob, iou = np.zeros((q_n, 32), np.float32), np.zeros((q_n, 32), np.float32)
    uv = np.zeros((q_n, 32, 2), np.float32)
    missing, selected = [], 0
    for q, name in enumerate(names):
        text = tower().phrase(name)
        if text not in cache['phrases']:
            missing.append(name)
            continue
        if presence is not None:
            p_names, p_values = presence
            p_index = {mdg().label(n): i for i, n in enumerate(p_names)}
            pq = p_index.get(mdg().label(name))
        for k in range(32):
            record = cache['frames'][str(k)]['phrases'][text]
            instances = instance_masks(record)
            if not instances:
                continue
            selector = p_values['mask'][pq, k] if select == 'iou' and presence is not None and pq is not None else None
            if selector is not None and selector.shape != SHAPE:
                # Every mask grid spans the whole resized frame (MDG_SPEC): resample by normalized coordinates.
                selector = ndimage.zoom(selector, (SHAPE[0]/selector.shape[0], SHAPE[1]/selector.shape[1]),
                                        order=0, prefilter=False)
            chosen, by_iou = choose(instances, selector)
            selected += by_iou
            if chosen is None or not chosen[0].any():
                continue
            mask, score = chosen
            if not mask.any():
                continue
            masks[q, k], iou[q, k] = mask, score
            if record.get('click') is not None and not by_iou:
                uv[q, k] = np.clip(np.rint(record['click']), 0, 1000)
            else:
                r, c = np.unravel_index(np.argmax(ndimage.distance_transform_edt(mask)), SHAPE)
                uv[q, k] = np.rint([(c+.5)/SHAPE[1]*1000, (r+.5)/SHAPE[0]*1000])
            if presence is None:
                prob[q, k] = float(record['joint_score']) if tower().accepted(record, tau) else 0.
            elif pq is not None:
                prob[q, k] = float(p_values['prob'][pq, k])
    values = dict(prob=prob, clip_prob=np.ones(q_n, np.float32), frame_prob=prob.copy(),
                  iou=iou, uv=uv, area=masks.mean(axis=(-1, -2)).astype(np.float64), mask=masks)
    return values, missing, selected


@lru_cache(maxsize=1)
def membership():
    """Dev point-membership id -> (scene key, normalized label, 1-based frame slot)."""
    rows = json.loads(Path('/scratch/jjyeung/orch_cd/evalx/work/devpool/GROUND_MEMBERSHIP.json').read_text())['items']
    return {r['id']: (r['scene'], mdg().label(r['obj']), int(r['frame'])) for r in rows}


def clicks_presence(path, key, names):
    """An evalx ground file of point clicks (`{"point_2d": [x, y]}` or null, canvas 0..1000) as a presence export:
    prob 1 and a one-cell selector where the click lands, prob 0 where the model answered null or was not asked."""
    out = json.loads(Path(path).read_text())['out']
    index = {mdg().label(n): q for q, n in enumerate(names)}
    prob = np.zeros((len(names), 32), np.float32)
    mask = np.zeros((len(names), 32)+SHAPE, bool)
    for item_id, response in out.items():
        scene, name, frame = membership()[item_id]
        if scene != key or name not in index:
            continue
        point = (json.loads(response) if isinstance(response, str) else response).get('point_2d')
        if point is None:
            continue
        q, k = index[name], frame-1
        c, r = (min(int(point[0]/1000*SHAPE[1]), SHAPE[1]-1), min(int(point[1]/1000*SHAPE[0]), SHAPE[0]-1))
        prob[q, k], mask[q, k, r, c] = 1., True
    return dict(prob=prob, mask=mask)


def same_checkpoint(a, b):
    """A cache written on another host records its own resolved path; size and mtime (tar keeps both) identify it."""
    return a['size'] == b['size'] and a['mtime_ns'] == b['mtime_ns']


def prep(which, png_root, out, scenes=None):
    """ttower SAM 3 manifest (held-out contract) and a frames dir of <ds>__<scene>/<slot>.jpg links to the anchor PNGs
    (PIL reads by content), for `sam3_tower.py run --scenes OUT/scenes.json --frames OUT/frames --out RAW`."""
    labels = sets.scene_labels(which)
    if scenes:
        labels = {k: v for k, v in labels.items() if k in scenes or k.split('/', 1)[1] in scenes}
    out = Path(out)
    rows = []
    for key, names in sorted(labels.items()):
        target = out/'frames'/key.replace('/', '__')
        target.mkdir(parents=True, exist_ok=True)
        for slot in range(32):
            source = Path(png_root)/key/f'{slot}.png'
            if not source.is_file():
                raise FileNotFoundError(source)
            link = target/f'{slot}.jpg'
            if not link.exists():
                link.symlink_to(source.resolve())
        rows.append(dict(scene=key, phrases=sorted({tower().phrase(n) for n in names})))
    manifest = dict(phase='heldout', contract_sha256=tower().fixed_sha(), scenes=rows)
    (out/'scenes.json').write_text(json.dumps(manifest, indent=1)+'\n')
    return dict(scenes=len(rows), phrases=sum(len(r['phrases']) for r in rows))


def main(argv=None):
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument('--set', choices=['dev', 'revsi'], default='dev')
    parser.add_argument('--prep-png-root', help='Write the SAM 3 manifest + frame links for --set into --out and exit')
    parser.add_argument('--heads', help='Heads supplying the pinned 32-frame selection')
    parser.add_argument('--raw', default=str(SAM3/'raw/heldout'))
    parser.add_argument('--presence', help='MDG export dir whose per-frame probabilities and tau replace SAM 3 presence')
    parser.add_argument('--presence-oracle', action='store_true',
                        help='--presence is a GT-mask export (rk.gtmask): ORACLE ceiling of a perfect presence gate')
    parser.add_argument('--clicks', help='evalx ground dir (<ds>__<scene>.json point clicks) used as presence + selector')
    parser.add_argument('--select', choices=['top', 'iou'], default='top',
                        help='iou: per frame, the SAM 3 instance overlapping the --presence export mask most')
    parser.add_argument('--min-instance-score', type=float, default=0.,
                        help='keep SAM 3 instances with score >= this (native gate 0.5); default keeps the cache as is')
    parser.add_argument('--scenes')
    parser.add_argument('--out', required=True)
    args = parser.parse_args(argv)
    MIN_SCORE[0] = args.min_instance_score
    selected = set(args.scenes.split(',')) if args.scenes else None
    if args.prep_png_root:
        print(json.dumps(prep(args.set, args.prep_png_root, args.out, selected)))
        return
    if not args.heads:
        parser.error('--heads is required')
    frozen = json.loads((SAM3/'tau_frozen.json').read_text())
    tau = float(frozen['tau'])
    grouped = {k: v for k, v in sets.scene_labels(args.set).items()
               if not selected or k in selected or k.split('/', 1)[1] in selected}
    p_root, p_entries = read_index(args.presence) if args.presence else (None, {})
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    index, report = {}, dict(missing_phrases={}, missing_raw=[], missing_presence=[], missing_heads=[], tau_sam3=tau)
    for key, names in sorted(grouped.items()):
        stem = key.replace('/', '__')
        raw = Path(args.raw)/(stem+'.npz')
        if not raw.exists():
            report['missing_raw'].append(key)
            continue
        cache = tower().load_cache(args.raw, key)
        if not same_checkpoint(cache['checkpoint'], frozen['checkpoint']):
            raise ValueError('SAM 3 checkpoint differs from calibration')
        if not (Path(args.heads)/(stem+'.npz')).exists():
            report['missing_heads'].append(key)
            continue
        with np.load(Path(args.heads)/(stem+'.npz'), allow_pickle=False) as z:
            frames = z['anchor_frame_indices'] if 'anchor_frame_indices' in z.files else z['frame_indices']
        names = sorted(set(map(mdg().label, names)))
        presence, scene_tau, extra = None, tau, {}
        if args.clicks and args.presence:
            raise ValueError('Use --clicks or --presence, not both')
        if args.clicks:
            ground = Path(args.clicks)/(stem+'.json')
            if not ground.exists():
                report['missing_presence'].append(key)
                continue
            presence, scene_tau = (names, clicks_presence(ground, key, names)), .5
            extra = dict(presence_clicks=str(ground.resolve()), presence_sha256=sha256(ground))
        elif args.presence:
            entry = p_entries.get(key)
            if entry is None:
                report['missing_presence'].append(key)
                continue
            p_names, p_values, p_audit = mdg().read_npz(p_root/entry['npz'])
            if bool(p_audit.get('gt_substitution')) != bool(args.presence_oracle):
                raise ValueError('A GT presence export requires --presence-oracle (and only then)')
            if list(map(int, entry['frame_indices'])) != list(map(int, frames)):
                raise ValueError('Presence export frames differ from heads: '+key)
            presence, scene_tau = (p_names, p_values), float(p_audit['tau'])
            extra = dict(presence_export=str((p_root/entry['npz']).resolve()),
                         presence_sha256=sha256(p_root/entry['npz']), presence_binding=p_audit.get('binding'))
        if args.select == 'iou' and presence is None:
            raise ValueError('--select iou requires --presence')
        values, missing, selected = build_scene(cache, names, tau, presence, args.select)
        report.setdefault('selected_by_iou', {})[key] = selected
        if missing:
            report['missing_phrases'][key] = missing
        audit = dict(tau=scene_tau, gt_substitution=bool(args.presence_oracle), source='SAM 3 zero-shot top-instance masks (ttower raw cache)',
                     min_instance_score=args.min_instance_score, presence='clicks' if args.clicks else 'mdg' if args.presence else 'sam3 frozen accept rule (joint_score >= tau)', select=args.select,
                     sam3_raw=str(raw.resolve()), sam3_raw_sha256=sha256(raw), sam3_checkpoint=frozen['checkpoint'],
                     sam3_tau=tau, frame_indices=list(map(int, frames)), entry=dict(frame_indices=list(map(int, frames))),
                     mask_shape=list(SHAPE), **extra)
        dest = out/(stem+'.npz')
        mdg().save_npz(dest, names, values, audit)
        index[key] = dict(scene=key, scene_key=key, npz=dest.name, frame_indices=list(map(int, frames)))
    (out/'INDEX.json').write_text(json.dumps(index, indent=2)+'\n')
    (out/'SAM3MASK.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(dict(scenes=len(index), selected_by_iou=sum(report.get('selected_by_iou', {}).values()),
                          **{k: len(v) for k, v in report.items() if k not in ('tau_sam3', 'selected_by_iou')})))


if __name__ == '__main__':
    main()
