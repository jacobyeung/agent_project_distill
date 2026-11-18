"""R0-dev (a7) per-type scores of B and paired differences A minus B, room bootstrap (10,000 draws, seed 20261115).
Usage: r0cmp.py --b DIR_B --a NAME=DIR ... [--output OUT.json]   (DIR = fetched/x of a return)
Also splits object_size_estimation by question unit (metric cm/mm/m vs imperial in/ft/yd) from the a7 B2048 journals."""
import argparse, glob, json, random

import os
MAP = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'evidence/ID_MAP.json')))
METRIC, IMPERIAL = {'cm', 'mm', 'm', 'meter', 'meters', 'centimeter', 'centimeters'}, {'in', 'ft', 'yd', 'inch', 'inches', 'feet', 'foot', 'yard', 'yards'}


def load(root):
    rows = {}
    for line in open(root + '/a7/ITEMS.jsonl'):
        d = json.loads(line)
        if d['id'] in rows: raise ValueError('duplicate ' + d['id'])
        rows[d['id']] = dict(room=d['room'], type=d['task_type'], score=float(d['score']))
    units = {}
    for f in glob.glob(root + '/a7/a0/results/budget_2048/*/items_a0.jsonl'):
        for line in open(f):
            d = json.loads(line)
            if d.get('question_type') == 'object_size_estimation':
                units[MAP[d['id']]['id']] = str(d.get('unit', '')).lower()
    for i, r in rows.items():
        if r['type'] == 'object_size_estimation':
            u = units.get(i, '?')
            r['split'] = 'size_metric' if u in METRIC else 'size_imperial' if u in IMPERIAL else 'size_unit_' + u
    if len(rows) not in (2169, 1781): raise ValueError('expected 2169 (all) or 1781 (direct filter) a7 items, got %d' % len(rows))
    return rows


def groups(rows):
    g = {}
    for i, r in rows.items():
        g.setdefault(r['type'], []).append(i)
        if 'split' in r: g.setdefault(r['split'], []).append(i)
    g['ALL_items'] = list(rows)
    return g


def boot(ids, va, vb, rooms, draws=10000, seed=20261115):
    by = {}
    for i in ids: by.setdefault(rooms[i], []).append(i)
    keys = sorted(by); rng = random.Random(seed); out = []
    sums = {k: (sum(va[i] - vb[i] for i in by[k]), len(by[k])) for k in keys}
    for _ in range(draws):
        s = n = 0
        for k in (rng.choice(keys) for _ in keys): s += sums[k][0]; n += sums[k][1]
        out.append(100 * s / n)
    out.sort()
    return out[int(0.025 * draws)], out[int(0.975 * draws) - 1]


def main():
    p = argparse.ArgumentParser(); p.add_argument('--b', required=True); p.add_argument('--a', nargs='+', required=True); p.add_argument('--output')
    x = p.parse_args(); B = load(x.b); G = groups(B); res = {'b': x.b, 'per_group': {}}
    vb = {i: r['score'] for i, r in B.items()}; rooms = {i: r['room'] for i, r in B.items()}
    As = {}
    for spec in x.a:
        name, d = spec.split('=', 1); A = load(d)
        if not set(B) <= set(A): raise ValueError(name + ' lacks items of B')
        As[name] = {i: A[i]['score'] for i in B}
    print('%-30s %5s %7s' % ('group', 'n', 'B%') + ''.join('  %-28s' % (n + ' - B') for n in As))
    for k in sorted(G):
        ids = G[k]; row = dict(n=len(ids), b_pct=100 * sum(vb[i] for i in ids) / len(ids))
        line = '%-30s %5d %7.1f' % (k, len(ids), row['b_pct'])
        for n, va in As.items():
            dv = 100 * sum(va[i] - vb[i] for i in ids) / len(ids); lo, hi = boot(ids, va, vb, rooms)
            row[n] = dict(a_pct=100 * sum(va[i] for i in ids) / len(ids), diff=dv, ci95=[lo, hi], differs=lo > 0 or hi < 0)
            line += '  %+6.1f [%+5.1f,%+5.1f]%s' % (dv, lo, hi, ' *' if row[n]['differs'] else '  ')
        res['per_group'][k] = row; print(line)
    if x.output: json.dump(res, open(x.output, 'w'), indent=1, sort_keys=True)


if __name__ == '__main__':
    main()
