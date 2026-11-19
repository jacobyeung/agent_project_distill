import sys, re, json, collections
sys.dont_write_bytecode = True
sys.path.insert(0, "/scratch/jjyeung/orch_n30/swarm_an/kit")
import san_kit as K
import numpy as np
Sc = K._scorer(); S = Sc.scorers
G = {}
for step in (544, 200):
    G[step] = {}
    for r in K.routed(step, types=['object_abs_distance']):
        vals = [S.printed(c) for c in r['calls'] if c['family'] == 'gap']; vals = [v['distance'] for v in vals if v]
        fs = [re.search(r'frames ([\d,]+) \(best', c['response'] or '') for c in r['calls'] if c['family'] == 'ground']
        if vals and len(fs) == 2 and all(fs): G[step][r['id']] = (vals[-1], float(r['gt']) / S.unit_factor(r['question']))
sh = [i for i in G[200] if i in G[544]]
print('shared gaps', len(sh), '| step 544 closer', sum(abs(G[544][i][0] - G[544][i][1]) < abs(G[200][i][0] - G[200][i][1]) for i in sh), '| step 200 closer', sum(abs(G[200][i][0] - G[200][i][1]) < abs(G[544][i][0] - G[544][i][1]) for i in sh))
# candidate records: any alternative box?
try:
    for step, args in ((544, (Sc.BASE / 'b1/work/ret', Sc.BASE / 'b1', 0, 544, 'null_argmax')), (200, (Sc.O.parent / 'out3/A4/ret', Sc.O / 'A', 0, 200, 'candidates_argmax'))):
        # distance journals may sit under another read index; use the kit's rows to find ids, then the scorer's loader
        raw, items, _, _ = Sc.load(*args)
        n = c = keys = 0; ks = collections.Counter(); grounds = multi = 0
        for i, o in raw.items():
            for rec in S.records(o['output']):
                st = rec.get('stage1') if isinstance(rec, dict) else None
                if not st: continue
                cands = st.get('candidates') or []
                grounds += 1; multi += len(cands) > 1
                for cd in cands:
                    n += 1; ks.update(cd.keys()); c += any(k in cd for k in ('box', 'box3d', 'center', 'centre', 'size', 'obb'))
        print(step, 'items', len(raw), 'ground records with stage1', grounds, 'with 2+ candidates', multi, 'candidate records', n, 'with a box field', c, 'keys', dict(ks.most_common(8)))
except Exception as e:
    print('candidate check failed:', repr(e)[:300])
