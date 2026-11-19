import sys, json
sys.path.insert(0, '/scratch/jjyeung/orch_n30/swarm_an/kit'); import san_kit as K
S = K._scorer(); O = S.O
rows, items, _, src = S.load(O.parent / 'out3/A4/ret', O / 'A', 0, 200, 'candidates_argmax')
print([s['path'] for s in src][:5])
n=0
for k in sorted(rows):
    it=items[k]
    if it['question_type']!='object_abs_distance': continue
    o=rows[k]['output']
    print(k, list(rows[k].keys()), list(o.keys()))
    print(json.dumps({kk:(vv if kk not in ('tokens',) else len(vv)) for kk,vv in o.items()}, default=str)[:6000])
    n+=1
    if n>=2: break
