"""Assemble the per-type ladder: A, B, C (any number of COND files), direct (f17 8d19426a) and the no-information
baseline (best constant answer text for multiple choice, best constant number for MRA types; fitted in-sample).
usage: ladder_table.py --cond B=out/COND_GF-mask_full_v0.json --cond C=out/COND_GF-pts-spec_full_v0.json [--pair B:D ...]"""
import argparse
import collections
import json
import sys

import numpy as np

sys.path.insert(0, '/scratch/jjyeung/orch_cd/gt_ceiling/work/gl')
import common as C  # noqa: E402
T = C.T


def load_a():
    a = {}
    for l in open(f'{C.W}/out/A_vsi.jsonl'):
        r = json.loads(l); a[('vsi', str(r['id']))] = (r['scene'], r['score'], r['type'], r['dataset'])
    for l in open(f'{C.W}/out/A_vsti_mobb_raw_px1.jsonl'):
        r = json.loads(l); a[('vsti', str(r['id']))] = (r['scene'], r['score'], r['type'], 'scannet')
    return a


def load_cond(p):
    out = {}
    for r in json.load(open(p)):
        out[(r['set'], str(r['id']))] = (r.get('scene') or '', r['score'], r['type'], r['dataset'])
    return out


def load_direct():
    d = {}
    for l in open(C.D_VSI):
        r = json.loads(l); d[('vsi', str(r['raw_id']))] = (r['scene_name'], r['score'], r['question_type'], r['dataset'])
    for i, t, s, st in json.load(open(C.D_VSTI))['items']:
        d[('vsti', str(i))] = ('', s, t, 'scannet')
    return d


def baseline(items):
    """items: list of (type, q). Returns {(set,id): score} of the best constant per type."""
    by = collections.defaultdict(list)
    for setn, q in items:
        by[q['question_type']].append((setn, q))
    out = {}
    for t, qs in by.items():
        if t in T.NUMERIC:
            g = np.array([float(q['ground_truth']) for _, q in qs])
            cands = np.unique(np.round(np.percentile(g, np.arange(1, 100)), 2))
            best = max(cands, key=lambda c: np.mean([T.mra(c, x) for x in g]))
            for s, q in qs:
                out[(s, str(q['id']))] = T.mra(best, float(q['ground_truth']))
        else:
            txt = collections.Counter(dict(T.option_texts(q['options'])).get(q['ground_truth'], '').lower() for _, q in qs)
            const, _ = txt.most_common(1)[0]
            by_text = [float(dict((v.lower(), k) for k, v in T.option_texts(q['options']).items()).get(const) == q['ground_truth']) for _, q in qs]
            let = collections.Counter(q['ground_truth'] for _, q in qs).most_common(1)[0][0]
            by_letter = [float(q['ground_truth'] == let) for _, q in qs]
            use = by_text if sum(by_text) >= sum(by_letter) else by_letter
            for (s, q), v in zip(qs, use):
                out[(s, str(q['id']))] = v
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--cond', action='append', default=[])
    ap.add_argument('--pair', action='append', default=[])
    ap.add_argument('--datasets', default='scannet')
    ap.add_argument('--out', default='')
    a = ap.parse_args()
    items = [('vsi', q) for q in C.vsi_items()] + [('vsti', q) for q in C.vsti_items()]
    items = [(s, q) for s, q in items if q['dataset'] in a.datasets.split(',')]
    scene = {(s, str(q['id'])): q['scene_name'] for s, q in items}
    typ = {(s, str(q['id'])): (s, q['question_type']) for s, q in items}
    cols = {'A': load_a()}
    for c in a.cond:
        n, p = c.split('=', 1); cols[n] = load_cond(p)
    cols['direct'] = load_direct()
    bl = baseline(items)
    cols['base'] = {k: (scene[k], v, None, None) for k, v in bl.items()}
    names = list(cols)
    lines = ['| set | type | ' + ' | '.join(f'{n} (n)' for n in names) + ' | ' + ' | '.join(a.pair) + ' |',
             '|' + '---|' * (2 + len(names) + len(a.pair))]
    for st in sorted(set(typ.values())):
        keys = [k for k in typ if typ[k] == st]
        cells = []
        for n in names:
            v = [cols[n][k][1] for k in keys if k in cols[n]]
            cells.append('%.1f (%d)' % (100 * np.mean(v), len(v)) if v else '-')
        pcs = []
        for pr in a.pair:
            x, y = pr.split(':')
            ra = {k: (scene[k], cols[x][k][1]) for k in keys if k in cols[x]}
            rb = {k: (scene[k], cols[y][k][1]) for k in keys if k in cols[y]}
            r = C.paired_ci(ra, rb)
            pcs.append('%+.1f [%+.1f, %+.1f] (%d)' % r if r else '-')
        lines.append(f'| {st[0]} | {st[1]} | ' + ' | '.join(cells) + ' | ' + ' | '.join(pcs) + ' |')
    txt = '\n'.join(lines)
    print(txt)
    if a.out:
        open(a.out, 'w').write(txt + '\n')


if __name__ == '__main__':
    main()
