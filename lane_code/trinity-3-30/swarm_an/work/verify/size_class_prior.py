"""Object size: does the training class median do as well as the model? Independent sample (seed 9, 5,000 of the family's rows)."""
import sys, json, sqlite3, random, re, statistics as st, collections
sys.path.insert(0, '/scratch/jjyeung/orch_n30/swarm_an/kit'); import san_kit as K
P = '/scratch/jjyeung/orch_n30/r1_ops6/store/a2_vqa_v7'
def cls(q):
    q = q.lower().strip().replace('’', "'")
    if q.startswith('measure the '): return q[12:].split(' along its ')[0]
    return re.split(r",|\?| in |'s| is | measures | measured| using ", re.split(r'(?:of|for) the ', q)[-1])[0].strip()
def unit(q):
    q = q.lower()
    if re.search(r'centimet|\bcm\b', q): return 1.
    if 'inch' in q: return 2.54
    if re.search(r'\bfeet\b|\bfoot\b|\bft\b', q): return 30.48
    return 100.
def mra(p, g): return sum(abs(p - g) / g <= 1 - t / 100 + 1e-12 for t in range(50, 100, 5)) / 10
rg = json.load(open(P + '/FAMILY_INDEX_RANGES.json'))['families']['object_size_estimation']
keys = [i for a, b in rg for i in range(a, b + 1)]; ids = sorted(random.Random(9).sample(keys, min(5000, len(keys))))
db = sqlite3.connect('file:' + P + '/vqa/rows.sqlite?mode=ro', uri=True); train = collections.defaultdict(list)
for k in range(0, len(ids), 200):
    b = ids[k:k + 200]
    for i, raw in db.execute('select i,row from rows where i in (' + ','.join('?' * len(b)) + ')', b):
        r = json.loads(raw); q = r['student_input']['question']; train[cls(q)].append(float(r['answer']) * unit(q))
med = {c: st.median(v) for c, v in train.items()}; allmed = st.median([x for v in train.values() for x in v])
print('family rows', len(keys), 'sampled', len(ids), 'classes', len(train), 'global median cm %.1f' % allmed)
out = {}
for se in ('dev-S1', 'R0-dev'):
    new = K.direct('R1', 200, se, types=['object_size_estimation']); old = {r['id']: r for r in K.direct('S1', 544, se, types=['object_size_estimation'])}
    for label, keep in (('class has >=5 sampled rows', lambda c: len(train.get(c, [])) >= 5), ('class has >=1', lambda c: c in med), ('all items (global median for unseen classes)', lambda c: True)):
        rs = [r for r in new if keep(cls(r['question']))]
        g = [float(r['gt']) * unit(r['question']) for r in rs]; c = [med.get(cls(r['question']), allmed) for r in rs]
        pm = 100 * sum(mra(a, b) for a, b in zip(c, g)) / len(rs)
        print('%-7s %-46s n=%3d class-median MRA %.1f | step 544 %.1f | step 200 %.1f | global-median MRA %.1f' % (se, label, len(rs), pm,
              100 * sum(old[r['id']]['score'] for r in rs) / len(rs), 100 * sum(r['score'] for r in rs) / len(rs), 100 * sum(mra(allmed, b) for b in g) / len(rs)))
        out[se + '|' + label] = dict(n=len(rs), class_median=round(pm, 2), s200=round(100 * sum(r['score'] for r in rs) / len(rs), 2))
json.dump(out, open('/scratch/jjyeung/orch_n30/swarm_an/work/verify/SIZE_CLASS_PRIOR.json', 'w'), indent=1)
