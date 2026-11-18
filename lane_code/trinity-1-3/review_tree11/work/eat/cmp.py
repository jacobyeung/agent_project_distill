import json,sys,re
def load(p): return json.load(open(p+'/EAT1_REPORT.json'))
rs=[load(p) for p in sys.argv[1:4]]
def norm(x):
    s=json.dumps(x,sort_keys=True)
    s=re.sub(r'/scratch/jjyeung/orch_n30/[A-Za-z0-9_./-]*?/(tree_r1|eat1|c8r)/', r'<\1>/', s)
    return s
c=[r['clauses'] for r in rs]
print(type(c[0]), list(c[0])[:10] if isinstance(c[0],dict) else len(c[0]))
for k in (c[0] if isinstance(c[0],dict) else range(len(c[0]))):
    v=[x[k] for x in c]
    st=[ (y.get('status') if isinstance(y,dict) else y) for y in v]
    print(k, st, 'eq_rev10', norm(v[0])==norm(v[1]), 'eq_builder', norm(v[0])==norm(v[2]), [len(norm(y)) for y in v])
