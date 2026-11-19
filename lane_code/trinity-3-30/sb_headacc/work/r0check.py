import sys, re, json, collections
sys.path.insert(0, '/scratch/jjyeung/orch_n30/swarm_an/kit'); import san_kit as K
R=K.direct('R1', 200, 'R0-dev')
print(len(R), sorted(R[0].keys()))
by=collections.defaultdict(list)
for r in R: by[r['type']].append(r)
for t,v in sorted(by.items()): print('%-30s n=%4d score=%.1f' % (t, len(v), 100*sum(float(x['score'] or 0) for x in v)/len(v)))
rd=by['object_rel_distance']
tk=[k for k in rd[0] if 'text' in k or 'trace' in k or 'think' in k]; print('text keys', tk)
txt=lambda r: next((r[k] for k in ('trace','text','think','full_text') if r.get(k)), '')
print(txt(rd[0])[:500].replace('\n',' | '))
n=sum(bool(re.search(r'nearest to farthest[^:]*: *(.+)', txt(r))) for r in rd); print('rel traces with a stated order:', n, 'of', len(rd))
ap=by['obj_appearance_order']; print(txt(ap[0])[:400].replace('\n',' | '))
