"""Set-selector table: label-free features per linked candidate (k = all) plus scoring-only labels, kept apart.

features  work/selector/features.py object_rows (SAM 3, base presence and V3 box agreement on dev only, tower 3D
          reprojection on the vcd heads) plus set features within the name (rank, relative peak, coverage).
eval      (never a feature) per member: best IoU with a GT instance of the named category and its id; per object:
          GT frame-instances (>= 39 and >= 154 px at 240 x 320) and the GT ids any raw SAM 3 proposal matches.
          The named category = prog_v2's own resolution (GTGround + vocab) | exact label | dev provider ids.
native    the deployed selector's per-frame references (v3rank_score.native_top_fallback on the vcd heads).
usage: build.py --set dev|vsi --cands FILE --out FILE [--workers N]"""
import argparse
import json
import os
import sys
from collections import defaultdict
from multiprocessing import Pool
from pathlib import Path

import numpy as np

VK = Path('/scratch/jjyeung/orch_cd/verify_kit')
sys.path[:0] = ['/scratch/jjyeung/orch_cd/grd_selector/work/selector', '/scratch/jjyeung/orch_cd/grd_selector/work/vk',
                str(VK/'work'), '/scratch/jjyeung/orch_cd/gt_ceiling/work/tp', '/scratch/jjyeung/orch_cd/gt_ceiling/work/gl']
import features as F  # noqa: E402
from verifykit.io import rows, cache, tower, write_rows  # noqa: E402

VCD = Path('/scratch/jjyeung/orch_cd/ttower/work/geo/heads_g3s64_vcd')
GT = '/scratch/jjyeung/orch_cd/toolprog/work/gt/scannet/%s.npz'
PROVIDER = VK/'out/full589_ruler/provider_boxes.jsonl'
MIN_PX = (39, 154)
F.HEADS = VCD


class Const(dict):
    def __init__(self, v):
        super().__init__()
        self.v = v

    def __missing__(self, k):
        return self.v


def decode(raw, slot, phrase, index):
    return tower().rle_decode(raw['frames'][str(slot)]['phrases'][phrase]['instances'][index]['mask'])[::2, ::2]


def iou(a, b):
    i = np.logical_and(a, b).sum()
    return float(i/np.logical_or(a, b).sum()) if i else 0.


def match_ids(gms, preds):
    """Greedy one-to-one IoU > 0.5; gms = [(gid, mask)] -> matched gids."""
    pairs = sorted(((iou(g, p), gi, j) for gi, g in gms for j, p in enumerate(preds)), reverse=True)
    ug, up = set(), set()
    for v, gi, j in pairs:
        if v > .5 and gi not in ug and j not in up:
            ug.add(gi)
            up.add(j)
    return sorted(ug)


def category(gt, name, provider_ids):
    import programs as PR
    import prog_v2 as V
    g = PR.GTGround(gt)
    V.use_vocab(g)
    ids = set(g.instances(name))
    ids |= {int(i) for i, l in zip(gt.ids, gt.labels) if str(l).lower() == name.lower()}
    return sorted(ids | set(provider_ids))


def set_features(out, g):
    peaks = np.array([r['features']['peak'] for r in out])
    order = (-peaks).argsort(kind='stable')
    rank = np.empty(len(out))
    rank[order] = np.arange(len(out))
    for r, rk in zip(out, rank):
        f = r['features']
        f['n_cands_name'] = float(len(out))
        f['peak_rank'] = float(rk)
        f['peak_rank_frac'] = float(rk/max(len(out)-1, 1))
        f['peak_rel'] = float(f['peak']/max(peaks.max(), 1e-6))
        f['coverage'] = float(f['n_members']/max(f['reproj_vis'], 1))
        f['log_members'] = float(np.log1p(f['n_members']))


def scene_job(args):
    os.chdir(VK)
    import programs as PR
    import v3rank_score as V3
    from rk.programs import load_heads
    scene, groups, setname, presence_path, v3_paths = args
    presence = defaultdict(lambda: .5, F.load_presence(presence_path)) if presence_path else Const(.5)
    boxes = F.load_boxes(v3_paths) if v3_paths else {}
    provider = {r['object_id']: [b['instance_id'] for b in r['boxes']] for r in rows(PROVIDER)} if setname == 'dev' else {}
    sc = F.Scene(scene, groups[0]['candidates'][0]['mask_ref']['path'])
    raw = sc.raw
    gt = PR.GTSource(GT % scene.split('/')[-1])
    assert list(np.load(GT % scene.split('/')[-1])['frame_indices']) == list(groups[0]['frame_indices'])
    geo = load_heads(VCD/(scene.replace('/', '__')+'.npz'))
    v1 = {ck: Const(.5) for ck in ('base', 't0')}
    v2 = {ck: {} for ck in ('base', 't0')}
    out_rows = []
    for g in sorted(groups, key=lambda g: g['name']):
        rng = np.random.default_rng(17)
        out = F.object_rows(g, sc, v1, v2, presence, boxes, rng)
        set_features(out, g)
        phrase = g['candidates'][0]['mask_ref']['phrase']
        cat = category(gt, g['name'], provider.get(g['object_id'], []))
        gmask = {k: [(i, gt.inst[k] == i) for i in cat] for k in range(32)}
        gt_frames = {str(k): [[i, int(m.sum())] for i, m in gmask[k] if m.sum() >= MIN_PX[0]] for k in range(32)}
        gt_frames = {k: v for k, v in gt_frames.items() if v}
        allgt = [int(i) for i in np.unique(gt.inst) if i >= 0]
        by_id = {c['candidate_id']: c for c in g['candidates']}
        for r in out:
            c = by_id[r['candidate_id']]
            mem = []
            for m in (c.get('members') or [c]):
                k, ii = m['slot'], m['mask_ref']['instance_index']
                pm = decode(raw, k, phrase, ii)
                best = max([(iou(pm, gm), i) for i, gm in gmask[k]], default=(0., -1))
                anyb = max([(iou(pm, gt.inst[k] == i), i) for i in allgt if (gt.inst[k][pm] == i).any()], default=(0., -1))
                mem.append(dict(slot=k, ii=ii, score=float(raw['frames'][str(k)]['phrases'][phrase]['instances'][ii]['score']),
                                px=int(pm.sum()), gid=best[1] if best[0] > .5 else -1, iou=best[0],
                                any_gid=anyb[1], any_iou=anyb[0],
                                any_label=gt.labels[list(gt.ids).index(anyb[1])] if anyb[1] >= 0 else None))
            hit = np.mean([m['gid'] >= 0 for m in mem])
            r.update(kind='candidate', members=mem, y=int(hit >= .5), hit_frac=float(hit))
            out_rows.append(r)
        prop = {}
        for k in range(32):
            gms = [(i, m) for i, m in gmask[k] if m.sum() >= MIN_PX[0]]
            if not gms:
                continue
            ni = len(raw['frames'][str(k)]['phrases'][phrase]['instances'])
            prop[str(k)] = match_ids(gms, [decode(raw, k, phrase, j) for j in range(ni)])
        fb = V3.native_top_fallback(raw, g, geo)
        native = []
        for x in fb['refs']:
            k, ii = x['slot'], x['instance_index']
            pm = decode(raw, k, phrase, ii)
            best = max([(iou(pm, gm), i) for i, gm in gmask[k]], default=(0., -1))
            native.append(dict(slot=k, ii=ii, score=float(raw['frames'][str(k)]['phrases'][phrase]['instances'][ii]['score']),
                               px=int(pm.sum()), gid=best[1] if best[0] > .5 else -1, iou=best[0]))
        top = max(g['candidates'], key=lambda c: (c['peak'], c['candidate_id']))['candidate_id']
        out_rows.append(dict(kind='object', object_id=g['object_id'], scene=scene, name=g['name'], phrase=phrase, cat=cat,
                             cat_labels=sorted({gt.labels[list(gt.ids).index(i)] for i in cat}), gt_frames=gt_frames,
                             prop_hit=prop, native=native, sam3_top=top,
                             n_candidates=len(g['candidates'])))
    return scene, out_rows


def main():
    ap = argparse.ArgumentParser(__doc__)
    ap.add_argument('--set', choices=('dev', 'vsi'), required=True)
    ap.add_argument('--cands', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--workers', type=int, default=8)
    ap.add_argument('--scenes', nargs='*')
    ap.add_argument('--presence', help='PRES32 JSONL for this set (default: the dev receipt on dev, none on VSI)')
    ap.add_argument('--v3', nargs='*', help='V3 box JSONL(s) for this set (default: the dev receipts on dev, none on VSI)')
    a = ap.parse_args()
    by = defaultdict(list)
    for g in rows(a.cands):
        by[g['scene']].append(g)
    if a.scenes:
        by = {s: v for s, v in by.items() if s in a.scenes}
    pres = a.presence or (str(F.PRESENCE) if a.set == 'dev' else None)
    v3 = a.v3 or ([str(p) for p in F.V3] if a.set == 'dev' else None)
    jobs = sorted(((s, g, a.set, pres, v3) for s, g in by.items()), key=lambda j: -sum(len(g['candidates']) for g in j[1]))
    allrows = []
    with Pool(a.workers) as p:
        for i, (scene, rr) in enumerate(p.imap_unordered(scene_job, jobs), 1):
            allrows += rr
            print('SCENE', i, len(jobs), scene, len(rr), flush=True)
    F.check([r for r in allrows if r['kind'] == 'candidate'])
    allrows.sort(key=lambda r: (r['object_id'], r['kind'], r.get('candidate_id', '')))
    write_rows(a.out, allrows)
    print(json.dumps(dict(rows=len(allrows), objects=sum(r['kind'] == 'object' for r in allrows), scenes=len(jobs))))


if __name__ == '__main__':
    main()
