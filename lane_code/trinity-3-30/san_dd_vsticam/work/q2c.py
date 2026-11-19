# Q2(c): fixed order per scene (leave one row out; siblings at the same k excluded) on rows, and the same on dev from dev truths
import sys, json
sys.path.insert(0, '/scratch/jjyeung/orch_n30/san_dd_vsticam/work'); from common import *
R = rows(); allrows = [r for f in R for r in R[f]]
sc = defaultdict(list)
for r in allrows: sc[r['canonical']].append(r)
def row_prefs(r):
    ids = [(r['canonical'], x['id']) for x in r['inst']]; g = r['gv']
    return [((ids[i], ids[j]) if g[i] < g[j] else (ids[j], ids[i])) for i in range(len(ids)) for j in range(i + 1, len(ids)) if g[i] != g[j]]
out = {}
for fam in CAM:
    c = Counter()
    for r in R[fam]:
        ids = [(r['canonical'], x['id']) for x in r['inst']]; win = ids[0]
        sib = [o for o in sc[r['canonical']] if o['qid'] != r['qid'] and o['k'] != r['k']]
        prefs = [p for o in sib for p in row_prefs(o)]
        w, u, n = copeland(ids, prefs)
        cov = set(i for p in prefs for i in p if i in ids)
        c['rows'] += 1; c['siblings>=1 (other k)'] += bool(sib)
        if w is not None: c['info'] += 1; c['hit|info'] += w == win
        if cov == set(ids): c['all covered'] += 1; c['hit|all covered'] += w == win
        c['exp x1000'] += 1000 * ((w == win) if w is not None else 1 / len(ids))
        out[r['qid']] = (w == win) if w is not None else None
    print(fam[-2:], dict(c), 'expected score %.1f%%' % (c['exp x1000'] / 10 / c['rows']))
# dev: fixed order from the truths of the room's other items (other k only), then the model's accuracy split by that rule
D = dev(); D2 = [d for d in D if d['step'] == 200]
rooms = defaultdict(list)
for d in D2: rooms[d['room']].append(d)
def truth_prefs(e):
    if e['type'] == NF:
        near = e['opts'][ord(e['gt']) - 65] == 'Near'
        return [(e['subj'], e['ref']) if near else (e['ref'], e['subj'])]
    t = e['opts'][ord(e['gt']) - 65]
    return [(t, o) for o in e['opts'] if o != t]
tab = Counter()
for d in D2:
    if d['type'] not in CAM: continue
    sib = [e for e in rooms[d['room']] if e['id'] != d['id'] and e['k'] != d['k']]
    prefs = [p for e in sib for p in truth_prefs(e)]
    w, u, n = copeland(d['opts'], prefs)
    t = d['opts'][ord(d['gt']) - 65]; ty = d['type'][-2:]
    tab[(ty, 'items')] += 1
    if w is None: tab[(ty, 'abstain')] += 1; tab[(ty, 'model right | abstain')] += d['score'] == 1; continue
    tab[(ty, 'info')] += 1; fo = w == t; tab[(ty, 'fixed-order right')] += fo
    tab[(ty, 'model right | fixed-order right' if fo else 'model right | fixed-order wrong')] += d['score'] == 1
    tab[(ty, 'n fixed-order right' if fo else 'n fixed-order wrong')] += 1
    tab[(ty, 'model answer == fixed-order pick')] += (d['opts'][ord(d['pred']) - 65] == w)
for k in sorted(tab): print(' ', k, tab[k])
