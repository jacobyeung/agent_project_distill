"""Run prog_v2 (VSI_FIX / VSTI_FIX, counting also with the 3D merge) on GT masks under geometry conditions
(geomswap.parse), VSI-Bench ScanNet (no appearance order / route) + VSTI, every condition on the same items.
usage: run_tg.py run --conds gt,dT+pT+kT,... --tag X [--workers 16] [--scenes ...]
       run_tg.py agg --tags X,Y --ref gt --out TG_TABLE.md"""
import argparse
import collections
import json
import sys
import time
from multiprocessing import Pool

import numpy as np

sys.path[:0] = ['/scratch/jjyeung/orch_cd/gt_ceiling/work/tg', '/scratch/jjyeung/orch_cd/gt_ceiling/work/gl',
                '/scratch/jjyeung/orch_cd/gt_ceiling/work/tp']
import common as C  # noqa: E402

VSI_FIX = 'frameidx,axes,memory,extent,identity,round,vocab,gbox0'
VSI_MERGE = 'frameidx,axes,memory,extent,merge,round,vocab,gbox0'
VSTI_FIX = 'frameidx,axes,memory,extent,identity,round'
SKIP = {'obj_appearance_order', 'route_planning'}
OUT = C.W + '/out/'
ARGS = None


def items():
    qs = [('vsi', q) for q in C.vsi_items() if q['dataset'] == 'scannet' and q['question_type'] not in SKIP]
    return qs + [('vsti', q) for q in C.vsti_items()]


def run_scene(job):
    import programs as PR
    import prog_v2 as V
    import geomswap as G
    G.install()
    scene, qs = job
    base = PR.GTSource(C.GTNPZ % scene)
    sg = G.SceneGeo(scene, base)
    rows = []
    for cond in ARGS.conds:
        gt = sg.make(cond)
        G.ROOM_VOTE = {'rv': (2, .05), 'rv10': (2, .10), 'rv3': (3, .05), 'rv4': (4, .05)}.get(next((m for m in gt.mods if m.startswith('rv')), None))
        ctxs = {'vsi': V.Ctx(gt, VSI_FIX.split(','), 'B'), 'vsti': V.Ctx(gt, VSTI_FIX.split(','), 'B')}
        merge = None
        for setn, q in qs:
            arms = [('main', ctxs[setn])]
            if q['question_type'] == 'object_counting':
                merge = merge or V.Ctx(gt, VSI_MERGE.split(','), 'B')
                arms.append(('merge', merge))
            for arm, ctx in arms:
                try:
                    pred, _ = (V.run_vsi if setn == 'vsi' else V.run_vsti)(q, ctx)
                    pred = V.finalize(q['question_type'], pred, ctx.fixes)
                except Exception:  # noqa: BLE001 - scored as no answer
                    pred = None
                rows.append(dict(set=setn, id=str(q['id']), type=q['question_type'], scene=scene, cond=cond, arm=arm,
                                 pred=pred, score=C.score(q['question_type'], pred, q['ground_truth'])))
    return rows


def init(a):
    global ARGS
    ARGS = a


def run(a):
    a.conds = a.conds.split(',')
    by = collections.defaultdict(list)
    for s, q in items():
        if a.scenes and q['scene_name'] not in a.scenes:
            continue
        if a.types and q['question_type'] not in a.types:
            continue
        by[q['scene_name']].append((s, q))
    rows, t0 = [], time.time()
    with Pool(a.workers, initializer=init, initargs=(a,)) as p:
        for i, r in enumerate(p.imap_unordered(run_scene, sorted(by.items(), key=lambda kv: -len(kv[1]))), 1):
            rows += r
            if i % 20 == 0:
                print('SCENE', i, len(by), '%.0fs' % (time.time() - t0), flush=True)
    json.dump(rows, open(OUT + f'TG_{a.tag}.json', 'w'), default=float)
    per = collections.defaultdict(list)
    for r in rows:
        per[(r['set'], r['type'], r['arm'], r['cond'])].append(r['score'])
    for k in sorted(per):
        print('%-4s %-30s %-5s %-34s n=%4d %.1f' % (*k, len(per[k]), 100 * np.mean(per[k])), flush=True)


# ------------------------------------------------------------------------------------------------ aggregation

def load(tags, fallback):
    import ladder_table as LT
    D = LT.load_direct() if fallback else {}
    tm = collections.defaultdict(list)
    for k, v in D.items():
        tm[(k[0], v[2])].append(v[1])
    tm = {k: float(np.mean(v)) for k, v in tm.items()}
    col = collections.defaultdict(dict)
    for tag in tags:
        for r in json.load(open(OUT + f'TG_{tag}.json')):
            key = (r['set'], r['id'], r['arm'])
            s = r['score']
            if fallback and r['pred'] is None:
                s = D[key[:2]][1] if key[:2] in D else tm.get((r['set'], r['type']), 0.)
            t = r['type'] + ('/merge' if r['arm'] == 'merge' else '')
            col[r['cond']][key] = (r['scene'], s, (r['set'], t))
    return col


def table(col, conds, ref, fmt_ci=True):
    types = sorted({v[2] for v in col[ref].values()})
    lines = ['| set | type | n | ' + ' | '.join(conds) + ' |', '|' + '---|' * (3 + len(conds))]
    res = {}
    for st in types:
        keys = [k for k, v in col[ref].items() if v[2] == st]
        cells = []
        for c in conds:
            ks = [k for k in keys if k in col[c]]
            if not ks:
                cells.append('-')
                continue
            m = 100 * np.mean([col[c][k][1] for k in ks])
            res[(st, c)] = m
            if c == ref or not fmt_ci:
                cells.append('%.1f' % m)
                continue
            ci = C.paired_ci({k: (col[c][k][0], col[c][k][1]) for k in ks}, {k: (col[ref][k][0], col[ref][k][1]) for k in ks})
            res[(st, c, 'ci')] = ci
            cells.append('%.1f (%+.1f [%+.1f, %+.1f])' % (m, *ci[:3]))
        lines.append(f'| {st[0]} | {st[1]} | {len(keys)} | ' + ' | '.join(cells) + ' |')
    return '\n'.join(lines), res


def agg(a):
    col = load(a.tags.split(','), a.fallback)
    conds = a.conds.split(',') if a.conds else sorted(col)
    txt, res = table(col, conds, a.ref)
    open(OUT + a.out, 'w').write(txt + '\n')
    json.dump({'|'.join(map(str, k)): v for k, v in res.items()}, open(OUT + a.out.replace('.md', '.json'), 'w'), default=float)
    print(txt)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('mode', choices=['run', 'agg'])
    ap.add_argument('--conds', default='')
    ap.add_argument('--tag')
    ap.add_argument('--tags')
    ap.add_argument('--ref', default='gt')
    ap.add_argument('--out', default='TG_TABLE.md')
    ap.add_argument('--fallback', action='store_true')
    ap.add_argument('--workers', type=int, default=16)
    ap.add_argument('--scenes', nargs='*')
    ap.add_argument('--types', nargs='*')
    a = ap.parse_args()
    run(a) if a.mode == 'run' else agg(a)


if __name__ == '__main__':
    import os
    os.environ.setdefault('OMP_NUM_THREADS', '1')
    main()
