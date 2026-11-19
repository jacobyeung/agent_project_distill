"""Q6: dev-S1 vs R0-dev toward items: rooms, timing, vocabulary; store v7 direction rows' sources (200 + 2,000 rows by primary key)."""
import sys, json, sqlite3, random, re, collections, statistics as stt
sys.path.insert(0, '/scratch/jjyeung/orch_n30/san_dd_dirtw/work'); from tw_lib import *
def q(x, p): s = sorted(x); return s[int(p * (len(s) - 1))]
TM = {st: K.timing('R1', 200, st) for st in ('R0-dev', 'dev-S1')}
for st in ('R0-dev', 'dev-S1'):
    rr = [r for r in K.direct('R1', 200, st, types=T) if (st == 'dev-S1' or r['subtype'] == 'toward')]
    pre = collections.Counter(re.sub(r'[0-9a-f]', 'h', r['room']) if st == 'R0-dev' else r['room'].split('/')[0] for r in rr)
    tm = [TM[st][r['id']] for r in rr if r['id'] in TM[st]]
    print(st, 'toward', len(rr), 'room formats', pre.most_common(4))
    print('   fps', collections.Counter(t['fps'] for t in tm).most_common(4), 'video s (q10,q50,q90)', [round(q([t['total_frames'] / t['fps'] for t in tm], p)) for p in (.1, .5, .9)],
          'spacing s (q10,q50,q90)', [round(q([t['spacing_s'] for t in tm], p), 1) for p in (.1, .5, .9)])
    if st == 'dev-S1':
        for pfx in ('d1', 'd2', 'd3'):
            sub = [r for r in rr if r['room'].startswith(pfx)]
            if sub: print('   ', pfx, len(sub), 'items, score@200 %.1f' % (100 * sum(r['score'] for r in sub) / len(sub)), 'video s q50', round(q([TM[st][r['id']]['total_frames'] / TM[st][r['id']]['fps'] for r in sub if r['id'] in TM[st]], .5)))
F = json.load(open('/scratch/jjyeung/orch_n30/r1_ops6/store/a2_vqa_v7/FAMILY_INDEX_RANGES.json'))['families']
did = [i for t in T for a, b in F[t] for i in range(a, b + 1)]; random.seed(7); S2 = sorted(random.sample(did, 2000))
con = sqlite3.connect('file:/scratch/jjyeung/orch_n30/r1_ops6/store/a2_vqa_v7/vqa/rows.sqlite?mode=ro', uri=True)
rows = []
for k in range(0, 2000, 200):
    for i, r in con.execute('select i,row from rows where i in (%s)' % ','.join(map(str, S2[k:k + 200]))):
        j = json.loads(r); si = j['student_input']; ts = si.get('timestamps') or []
        rows.append(dict(ds=j.get('dataset'), scene=j.get('scene'), fps=si.get('fps'), nf=si.get('total_num_frames'), q=si['question'].split('\n')[0].lower(),
                         sp=(ts[-1] - ts[0]) / (len(ts) - 1) if len(ts) > 1 else None, keys=sorted(k for k in j if k not in ('student_input', 'target'))))
print('store v7 direction rows (2,000):', collections.Counter(r['ds'] for r in rows).most_common(), 'scene format', collections.Counter(re.sub(r'[0-9a-f]', 'h', r['scene']) for r in rows).most_common(2))
for ds in ('d1', 'd2', 'd3'):
    sub = [r for r in rows if r['ds'] == ds]
    print('  ', ds, len(sub), 'fps', collections.Counter(r['fps'] for r in sub).most_common(2), 'video s q50', round(q([r['nf'] / r['fps'] for r in sub], .5)), 'q90', round(q([r['nf'] / r['fps'] for r in sub], .9)), 'spacing s q50', round(q([r['sp'] for r in sub if r['sp']], .5), 1))
print('  rows at 60 fps with video > 150 s:', sum(1 for r in rows if r['fps'] == 60 and r['nf'] / 60 > 150), 'of', len(rows))
keys = collections.Counter(k for r in rows[:200] for k in r['keys']); print('  row keys in the first 200 rows:', sorted(keys))
# vocabulary overlap
for st in ('R0-dev', 'dev-S1'):
    rr = [r for r in K.direct('R1', 200, st, types=T) if (st == 'dev-S1' or r['subtype'] == 'toward')]
    names = set()
    for r in rr:
        o = names3(r['question'])
        if None not in o: names |= {n.lower() for n in o}
    hit = {ds: sum(1 for n in names if any(re.search(r'\bthe ' + re.escape(n) + r'(?![a-z])', x['q']) for x in rows if x['ds'] == ds)) for ds in ('d1', 'd2', 'd3')}
    anyh = sum(1 for n in names if any(re.search(r'\bthe ' + re.escape(n) + r'(?![a-z])', x['q']) for x in rows))
    print(st, 'distinct names (template-parsed items)', len(names), 'present in the 2,000 rows', anyh, 'by source', hit)
