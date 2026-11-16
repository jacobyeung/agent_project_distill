"""Selector masks under the fusion policy: grd_selector's routed default (price2.py, imported read-only) with the
fused boxes built by geomswap.fuse_points under a fusion rule, on GT, V-C (heads_g3s64_vcd) and G3T (heads_g3s64)
geometry. One pass per (rule, tower export); rows carry geom in {gtgeo, vcd, g3t}, rule and arm.
Arms: route (grd_selector default: accept-model top-1, depth cut; counting learned merge), route_raw (no cut), gt, gt_dc.
usage: price_sel.py --rules all,best1,voteb5 --towers vcd,g3t --out TG_SEL [--workers 12]"""
import argparse
import json
import os
import sys
from multiprocessing import Pool

import numpy as np

sys.path[:0] = ['/scratch/jjyeung/orch_cd/gt_ceiling/work/tg', '/scratch/jjyeung/orch_cd/grd_selector/work/setsel']
import price2 as P2  # noqa: E402
import price as PZ  # noqa: E402

TOWERS = dict(vcd='/scratch/jjyeung/orch_cd/ttower/work/geo/heads_g3s64_vcd/scannet__%s.npz',
              g3t='/scratch/jjyeung/orch_cd/ttower/work/geo/heads_g3s64/scannet__%s.npz',
              vcd2g3t='/scratch/jjyeung/orch_cd/gt_ceiling/work/data/heads_vcd2g3t/scannet__%s.npz')
RULE = 'all'
_BASE = PZ.PredFused


class RuleFused(_BASE):
    """price.PredFused that keeps (frame, points, pixels) per instance and fuses them with geomswap's rule."""

    def __init__(self, geom, insts, min_px=PZ.MIN_PX, mode=None):
        import scene_gt as SG
        self.SG, self.min_px, self.rule = SG, min_px, RULE
        self.pts, self.px, self._box, self._fused = {}, {}, {}, {}
        for i, fr in insts.items():
            for k, m in fr.items():
                n = int(m.sum())
                self.px.setdefault(i, {})[k] = n
                if n < min_px or k not in geom.frames:
                    continue
                Pk = PZ.lift(geom, k, m, mode)
                if Pk is not None:
                    self.pts.setdefault(i, []).append((k, Pk, n))

    def points(self, i):
        import geomswap as G
        if i not in self._fused:
            fr = self.pts.get(i)
            self._fused[i] = G.fuse_points(fr, self.rule) if fr else None
        return self._fused[i]


def init(a, rule, tower):
    global RULE
    P2.init(a)
    RULE = rule
    PZ.VCD = TOWERS[tower]
    PZ.PredFused = RuleFused


def main():
    import common as C
    import setlib as L
    import cands as CD
    ap = argparse.ArgumentParser()
    ap.add_argument('--rules', default='all,best1,voteb5')
    ap.add_argument('--towers', default='vcd,g3t')
    ap.add_argument('--arms', default='route,route_raw,gt,gt_dc')
    ap.add_argument('--out', default='TG_SEL')
    ap.add_argument('--workers', type=int, default=12)
    ap.add_argument('--scenes', nargs='*')
    a = ap.parse_args()
    cfg = json.load(open('/scratch/jjyeung/orch_cd/grd_selector/out/price2_vsi/config.json'))
    a.set, a.tau_count, a.merge, a.thr_merge, a.pair_model = 'vsi', cfg['tau_count'], cfg['merge'], cfg['thr_merge'], cfg['pair_model']
    allp = json.load(open(f'{P2.D}/probs2/probs.json'))
    a.probs = {k: allp[f'DEPLOY|{v}'] for k, v in P2.ACC.items()}
    a.pairs = json.load(open(f'{P2.D}/pairs_fit/pair_probs.json'))[f'DEPLOY|{a.pair_model}']
    objs, cands = L.load(P2.TAB['vsi'])
    qs = [q for q in C.vsi_items() if q['dataset'] == 'scannet' and q['question_type'] in CD.PROG_TYPES
          and (CD.RAW['vsi'] / f"scannet__{q['scene_name']}.npz").exists()]
    a.direct = {str(r['raw_id']): r['score'] for r in map(json.loads, open(C.D_VSI))}
    a.arms = a.arms.split(',')
    scenes = sorted({o['scene'].split('/')[-1] for o in objs.values()})
    if a.scenes:
        scenes = [s for s in scenes if s in a.scenes]
    by = {}
    for q in qs:
        by.setdefault(q['scene_name'], []).append(q)
    jobs = []
    for s in sorted(scenes, key=lambda s: -len(by.get(s, []))):
        so = {k: v for k, v in objs.items() if v['scene'] == f'scannet/{s}'}
        if by.get(s):
            jobs.append((s, by[s], so, {k: cands.get(k, []) for k in so}))
    rows = []
    for tower in a.towers.split(','):
        for rule in a.rules.split(','):
            with Pool(a.workers, initializer=init, initargs=(a, rule, tower)) as p:
                for r, _, _ in p.imap_unordered(P2.scene_job, jobs):
                    for x in r:
                        if x['geom'] == 'gtgeo' and tower != a.towers.split(',')[0]:
                            continue
                        x['geom'] = tower if x['geom'] == 'tower' else x['geom']
                        x['rule'] = rule
                        rows.append(x)
            print('DONE', tower, rule, len(rows), flush=True)
    json.dump(rows, open(C.W + f'/out/{a.out}.json', 'w'), default=float)


if __name__ == '__main__':
    os.environ.setdefault('OMP_NUM_THREADS', '1')
    main()
