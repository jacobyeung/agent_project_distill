import sys, re, collections
sys.path.insert(0, '/scratch/jjyeung/orch_n30/swarm_an/kit'); import san_kit as K
rows = K.direct('R1', 200, 'R0-dev', types=['obj_appearance_order'])
def frames(r):
    th = (r['text'] or '').split('</think>')[0]; m = re.search(r'Step 1:[^\n]*?:(.*)', th)
    if not m: return None
    out = {}
    for part in m.group(1).split(';'):
        mm = re.match(r'\s*(.+?)\s+frame\s+([\d.]+)', part.strip().rstrip('.'))
        if mm: out[mm.group(1).strip().lower()] = float(mm.group(2))
    return out
def opts(r): return {o[0]: [x.strip().lower() for x in o.split('.', 1)[1].split(',')] for o in r['options']}
def lcp(a, b):
    n = 0
    for x, y in zip(a, b):
        if x != y: break
        n += 1
    return n
agree = right = n = 0; first = collections.Counter(); byroom = collections.defaultdict(dict)
for r in rows:
    f = frames(r); oo = opts(r); truth = oo[str(r['gt']).strip()[0]]
    if not f or set(f) != set(truth): continue
    n += 1; order = sorted(f, key=lambda x: f[x])
    best = max(lcp(order, o) for o in oo.values()); cands = [k for k, o in oo.items() if lcp(order, o) == best]
    if len(cands) > 1:  # tie-break by pairwise agreement
        def pa(o): return sum(order.index(o[i]) < order.index(o[j]) for i in range(4) for j in range(i + 1, 4))
        m = max(pa(oo[k]) for k in cands); cands = [k for k in cands if pa(oo[k]) == m]
    pl = str(r['pred']).strip()[:1]
    agree += (pl in cands) / float(len(cands)) if pl in cands else 0; right += (str(r['gt']).strip()[0] in cands) / float(len(cands)) if str(r['gt']).strip()[0] in cands else 0
    first[(r['score'] >= 1, f[truth[0]] <= 2)] += 1
    for k, v in f.items(): byroom[(r['room'], k)][r['id']] = v
print('parsed', n, 'prefix decoder on stated frames: equals the answer %.1f, equals the truth %.1f' % (agree, right))
print('truly-first object cited at frame 1 or 2: wrong items', first[(False, True)], 'of', first[(False, True)] + first[(False, False)], '| right items', first[(True, True)], 'of', first[(True, True)] + first[(True, False)])
multi = {k: v for k, v in byroom.items() if len(v) >= 2}
print('room-object pairs asked in two or more items', len(multi), 'identical stated frame', sum(len(set(v.values())) == 1 for v in multi.values()))
