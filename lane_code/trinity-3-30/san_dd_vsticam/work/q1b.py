# Q1 reading aid: features that might separate right from wrong at step 200; step-544 decision list without its own distances
import sys, json, itertools
sys.path.insert(0, '/scratch/jjyeung/orch_n30/san_dd_vsticam/work'); from common import *
D = dev(); by = {(d['id'], d['step']): d for d in D}
Q = json.load(open(T + '/q1_rules.json'))
def rel(f, k): return 'none' if f is None else ('>32' if f > 32 else ('=k' if f == k else ('<k' if f < k else '>k')))
feat = defaultdict(Counter)
for d in D:
    if d['step'] != 200 or d['type'] not in CAM: continue
    v = Q['%s|200' % d['id']]; o = by[(d['id'], 544)]; a = v['a']; ok = v['score'] == 1
    fs = d['fs']; k = d['k']
    f = {}
    f['ans_fs'] = rel(fs.get(a), k)
    f['n>32'] = min(sum(x > 32 for x in fs.values()), 2)
    f['any=k'] = any(x == k for x in fs.values())
    f['=early'] = a == v['r']['early'][0]
    f['=last'] = a == v['r']['last'][0]
    f['=large'] = a == v['r']['large'][0]
    f['=room'] = 'abst' if v['r']['room'][0] is None else a == v['r']['room'][0]
    f['=544ans'] = a == (o['opts'][ord(o['pred']) - 65] if o['pred'] else None)
    srt = sorted(d['opts'], key=lambda x: (fs.get(x, 99), d['opts'].index(x)))
    f['order==fs-order'] = d['order'] == srt
    f['order==rev-fs'] = d['order'] == sorted(d['opts'], key=lambda x: (-fs.get(x, 99), d['opts'].index(x)))
    f['top_fs_rank'] = sorted(fs.values()).index(fs[a]) if a in fs else None
    f['mind|f-k|'] = min(min(abs(x - k) for x in fs.values()), 3)
    f['kband'] = (k - 1) // 8
    for n, val in f.items(): feat[(n, val)][ok] += 1
print('feature value | right | wrong | acc   (step 200, 450 camera items)')
for key in sorted(feat, key=str):
    c = feat[key]; n = c[True] + c[False]
    print(key, c[True], c[False], round(100 * c[True] / n, 1))
# step-544 decision list without its own distances
res = [v for k2, v in Q.items() if k2.endswith('|544')]
pool = ['early', 'neark', 'large', 'room', 'last', 'first']
def pick(v, n):
    w, u = v['r'][n]
    return w if n in ('last', 'first') else (w if (w is not None and u) else None)
def dl(v, order):
    for n in order:
        p = pick(v, n)
        if p is not None: return p
best = sorted(((sum(dl(v, o) == v['a'] for v in res), o) for L in range(1, 5) for o in itertools.permutations(pool, L) if o[-1] in ('last', 'first')), reverse=True)
print('544 without own distances', best[:3], 'of', len(res))
