"""Row audit, appearance order: the row's stated order against the labeller's first-seen frames, split by whether every cited first-seen frame
shows the object at 1% or more of the frame (raster share) and whether a named object has a sibling label (same head noun) in the scene.
Also the distinct (capture, object) first-seen comparison against the raster. usage: /usr/bin/python3 audit_order.py [TAG=audit_astra]"""
import json, collections, sys
KD = '/scratch/jjyeung/orch_n30/swarm_an/work/pilot_key/'; P = '/scratch/jjyeung/orch_n30/swarm_an/work/pilot/'
tag = sys.argv[1] if len(sys.argv) > 1 else 'audit_astra'
A = json.load(open(P + 'results/ROW_AUDIT_%s.json' % tag)); rows = json.load(open(KD + 'audit_rows.json')); rast = json.load(open(KD + 'audit_raster.json'))
ds = dict((kq.split('/')[0], k['dataset']) for kq, k in json.load(open(KD + 'key_k1.json')).items())
def sing(l): return l[:-1] if l.endswith('s') and not l.endswith('ss') else l
def head(l): return sing(l.split()[-1])
def sib(alias, o):
    L = set(rast[alias]['labels']); me = set(l for l in L if l == o or sing(l) == sing(o))
    return sorted(l for l in L - me if head(l) == head(o))
first = dict(((f['alias'], f['obj']), f) for f in A['first'])
c = collections.Counter(); early = collections.Counter()
for (a, o), f in first.items():
    if f['raster'] in (None, 0) or f['labeller'] is None: continue
    if f['labeller'] == 0: c['never'] += 1; continue
    d = f['labeller'] - f['raster']; k = 'same' if d == 0 else 'within one' if abs(d) == 1 else 'labeller 2+ earlier' if d < 0 else 'labeller 2+ later'; c[k] += 1
    if d <= -2:
        s = rast[a]['objs'][o]['share'][f['labeller'] - 1]; early['raster 0 px at the labeller frame' if s == 0 else 'sliver under 0.2%'] += 1; early[ds[a]] += 1
print('distinct (capture, object) with a raster first-seen frame:', sum(c.values()), dict(c)); print('labeller earlier:', dict(early))
rev = collections.Counter(); byds = collections.Counter()
for i, r in rows.items():
    if r['category'] != 'obj_appearance_order' or len(r['pairs']) != 4: continue
    lf = {}
    for o, k in r['pairs']:
        f = first.get((r['alias'], o))
        if f and f['labeller'] not in (None, 0): lf[o] = f['labeller']
    if len(lf) != 4: rev['labeller missing or never'] += 1; continue
    cf = dict((o, k) for o, k in r['pairs']); objs = list(cf)
    bad = any((cf[x] - cf[y]) * (lf[x] - lf[y]) < 0 for x in objs for y in objs if x < y)
    hs = any(sib(r['alias'], o) for o in objs)
    low = any((rast[r['alias']]['objs'].get(o) or {}).get('share', [1] * 32)[k - 1] < 0.01 for o, k in r['pairs'])
    rev[('sibling label' if hs else 'no sibling label', 'a cited frame under 1%' if low else 'all cited frames 1%+', 'reversed' if bad else 'consistent')] += 1
    byds[(ds[r['alias']], 'reversed' if bad else 'consistent')] += 1
for k, v in sorted(rev.items(), key=str): print('  ', k, v)
print('by dataset', dict(byds))
