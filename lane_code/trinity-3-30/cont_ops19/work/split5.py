"""Counting split (true count, dataset) and relative size, export vs step 544, paired by item; room bootstrap 10,000 draws.
usage: split.py --x <fetched/x of the export read> --label R1m200 [--out file.json]"""
import argparse, json, random, collections
K = '/scratch/jjyeung/orch_n30/cont_ops/work/h1read/kit/build'
BASE = dict(main='/scratch/jjyeung/orch_n30/evalx27/work/pull/x27/res/e193/merged/main/results/budget_2048/0/items_leg_m544_main.jsonl',
            a7=K + '/adff67f7ae9/fetched/x/a7/a0/results/budget_2048/0/items_a0.jsonl')
SET = dict(main='dev-S1', a7='R0-dev')

def raw(p, types):
    d = {}
    for l in open(p):
        r = json.loads(l)
        if r.get('question_type') in types: d[r['id']] = r
    return d

def boot(pairs, n=10000, seed=20261118):
    """pairs: list of (room, delta); percentile 95% over rooms."""
    by = collections.defaultdict(list)
    for room, x in pairs: by[room].append(x)
    rooms = sorted(by); rng = random.Random(seed); ms = []
    for _ in range(n):
        s = c = 0
        for _ in rooms:
            v = by[rooms[rng.randrange(len(rooms))]]; s += sum(v); c += len(v)
        ms.append(100.0 * s / c)
    ms.sort(); m = 100.0 * sum(x for _, x in pairs) / len(pairs)
    return round(m, 2), round(ms[int(0.025 * n)], 2), round(ms[int(0.975 * n) - 1], 2)

def bins(gt):
    g = int(float(gt))
    return str(g) if g <= 4 else '5+'

def main():
    a = argparse.ArgumentParser(); a.add_argument('--x', required=True); a.add_argument('--label', required=True); a.add_argument('--out')
    a = a.parse_args(); res = {}; lines = []
    for fam in ('main', 'a7'):
        b = raw(BASE[fam], ('object_counting', 'relative_size_object'))
        e = raw(a.x + '/%s/a0/results/budget_2048/0/items_a0.jsonl' % fam, ('object_counting', 'relative_size_object'))
        for qt in ('object_counting', 'relative_size_object'):
            ids = sorted(i for i in e if e[i]['question_type'] == qt)
            if not ids: continue
            miss = [i for i in ids if i not in b]
            assert not miss, (fam, qt, len(miss))
            groups = collections.defaultdict(list)
            for i in ids:
                d = float(e[i]['score']) - float(b[i]['score']); room = b[i]['room']
                groups['all'].append((room, d))
                if qt == 'object_counting':
                    groups['true=' + bins(b[i]['ground_truth'])].append((room, d))
                    if fam == 'main': groups['dataset=' + (b[i].get('dataset') or b[i]['scene'].split('/')[0])].append((room, d))
            for g, pr in sorted(groups.items()):
                eb = [float(e[i]['score']) for i in ids if (g == 'all' or (g.startswith('true=') and 'true=' + bins(b[i]['ground_truth']) == g) or (g.startswith('dataset=') and 'dataset=' + (b[i].get('dataset') or b[i]['scene'].split('/')[0]) == g))]
                bb = [float(b[i]['score']) for i in ids if (g == 'all' or (g.startswith('true=') and 'true=' + bins(b[i]['ground_truth']) == g) or (g.startswith('dataset=') and 'dataset=' + (b[i].get('dataset') or b[i]['scene'].split('/')[0]) == g))]
                m, lo, hi = boot(pr)
                row = dict(set=SET[fam], type=qt, group=g, n=len(pr), rooms=len({r for r, _ in pr}), base=round(100 * sum(bb) / len(bb), 2), export=round(100 * sum(eb) / len(eb), 2), delta=m, ci95=[lo, hi])
                res.setdefault(SET[fam] + '/' + qt, []).append(row)
                lines.append('%-7s %-21s %-17s n%4d r%3d  544 %6.2f  %s %6.2f  d %+6.2f [%+.2f,%+.2f]' % (SET[fam], qt, g, len(pr), row['rooms'], row['base'], a.label, row['export'], m, lo, hi))
    print('\n'.join(lines))
    if a.out: json.dump(dict(label=a.label, x=a.x, base=BASE, rows=res, note='raw journal scores at B2048; room bootstrap 10,000 draws, seed 20261118, percentile 95%'), open(a.out, 'w'), indent=1)

main()
