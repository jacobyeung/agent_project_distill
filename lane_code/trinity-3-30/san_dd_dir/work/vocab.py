"""Object-name counts in store-v7 direction questions by family group (W = D opening, S = Seen opening), by primary key."""
import json, sqlite3, sys, ast, collections
sys.path.insert(0, '/scratch/jjyeung/orch_n30/san_dd_dir/work'); import dirparse as P
S = '/scratch/jjyeung/orch_n30/r1_ops6/store/a2_vqa_v7'
F = json.load(open(S + '/FAMILY_INDEX_RANGES.json'))['families']
db = sqlite3.connect('file:' + S + '/vqa/rows.sqlite?mode=ro', uri=True)
V = {'W': collections.Counter(), 'S': collections.Counter()}; VQ = {'W': collections.Counter(), 'S': collections.Counter()}
for t in P.T:
    ids = [i for lo, hi in F[t] for i in range(lo, hi + 1)]
    for k in range(0, len(ids), 200):
        for i, row in db.execute('select i,row from rows where i in (%s)' % ','.join(map(str, ids[k:k + 200]))):
            r = json.loads(row); si = r['student_input']; si = si if isinstance(si, dict) else ast.literal_eval(si)
            g = 'W' if r.get('pool') == 'w1g' else 'S'
            q = si['question']; tr = P.triple(q)
            if tr:
                for o in tr[:3]: V[g][o] += 1
            low = q.lower()
            VQ[g]['_n'] += 1
json.dump({g: dict(v) for g, v in V.items()}, open('/scratch/jjyeung/orch_n30/san_dd_dir/work/vocab_by_group.json', 'w'))
print({g: (len(v), sum(v.values())) for g, v in V.items()}, {g: v['_n'] for g, v in VQ.items()})
