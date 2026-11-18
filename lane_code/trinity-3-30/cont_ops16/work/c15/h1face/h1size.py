"""Object size split by question unit (metric vs imperial) and relative size, from raw main-family journals.
Usage: h1size.py --a DIR_A --b DIR_B [--output OUT.json]   (DIR = fetched/x of a return; reports B minus A)
Paired room bootstrap: item-weighted mean of per-item differences, rooms resampled with replacement, 10,000 draws, seed 20261115."""
import argparse, glob, json, random, re

METRIC, IMPERIAL = ('cm', 'mm', 'm'), ('in', 'ft', 'yd')
UNITS = [('centimet', 'cm'), ('millimet', 'mm'), ('meter', 'm'), ('metre', 'm'), ('inch', 'in'), ('feet', 'ft'), ('foot', 'ft'), ('yard', 'yd')]


def unit(q):
    ql = q.lower()
    for k, u in UNITS:
        if k in ql: return u
    for u in ('cm', 'mm', 'm'):
        if re.search(r'\b%s\b' % u, ql): return u
    return '?'


def load(root):
    rows = {}
    for f in sorted(glob.glob(root + '/main/a0/results/budget_2048/*/items_a0.jsonl')):
        for line in open(f):
            d = json.loads(line)
            if d.get('question_type') not in ('object_size_estimation', 'relative_size_object'): continue
            if d['id'] in rows: raise ValueError('duplicate id ' + d['id'])
            rows[d['id']] = dict(room=d['room'], type=d['question_type'], score=float(d['score']),
                                 unit=unit(d['question']) if d['question_type'] == 'object_size_estimation' else None)
    if not rows: raise ValueError('no size rows under ' + root)
    return rows


def paired(a, b, keys, draws=10000, seed=20261115):
    rooms = {}
    for k in keys: rooms.setdefault(a[k]['room'], []).append(b[k]['score'] - a[k]['score'])
    names = sorted(rooms); rng = random.Random(seed); est = []
    for _ in range(draws):
        s = n = 0
        for r in (rng.choice(names) for _ in names): s += sum(rooms[r]); n += len(rooms[r])
        est.append(100 * s / n)
    est.sort()
    mean = lambda side: 100 * sum(side[k]['score'] for k in keys) / len(keys)
    return dict(items=len(keys), rooms=len(names), a_pct=round(mean(a), 2), b_pct=round(mean(b), 2),
                delta_pp=round(mean(b) - mean(a), 2), ci95_pp=[round(est[int(.025 * draws)], 2), round(est[int(.975 * draws) - 1], 2)])


def main():
    p = argparse.ArgumentParser(); p.add_argument('--a', required=True); p.add_argument('--b', required=True); p.add_argument('--output')
    x = p.parse_args(); a, b = load(x.a), load(x.b)
    if set(a) != set(b): raise ValueError('item sets differ: %d vs %d' % (len(a), len(b)))
    for k in a:
        if (a[k]['room'], a[k]['type'], a[k]['unit']) != (b[k]['room'], b[k]['type'], b[k]['unit']): raise ValueError('metadata differs ' + k)
    groups = dict(size_all=[k for k in a if a[k]['type'] == 'object_size_estimation'],
                  size_metric=[k for k in a if a[k]['unit'] in METRIC],
                  size_imperial=[k for k in a if a[k]['unit'] in IMPERIAL],
                  size_unknown_unit=[k for k in a if a[k]['type'] == 'object_size_estimation' and a[k]['unit'] == '?'],
                  relative_size=[k for k in a if a[k]['type'] == 'relative_size_object'])
    out = {g: paired(a, b, ks) for g, ks in groups.items() if ks}
    print(json.dumps(out, indent=1))
    if x.output: json.dump(out, open(x.output, 'w'), indent=1)


if __name__ == '__main__': main()
