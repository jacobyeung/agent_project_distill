import json,sys,re,difflib
def norm(x):
    s=json.dumps(x,sort_keys=True,indent=0)
    s=re.sub(r'/scratch/jjyeung/orch_n30/[A-Za-z0-9_./-]*?/(tree_r1|eat1|c8r)/', r'<\1>/', s)
    return s.splitlines()
a,b,c=[json.load(open(p+'/EAT1_REPORT.json'))['clauses']['A3'] for p in sys.argv[1:4]]
for x,n in ((b,'rev10'),(c,'builder')):
    print('vs',n); print('\n'.join(l for l in difflib.unified_diff(norm(x),norm(a),lineterm='',n=0) if not l.startswith(('---','+++'))))
print(len(a.get('offenders',[])) if isinstance(a,dict) else '')
