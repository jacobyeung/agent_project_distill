import sys,json,hashlib
from pathlib import Path
N=Path('/scratch/jjyeung/orch_n30/tree_rebuild_w')
P=Path('/scratch/jjyeung/orch_n30/review_tree11/pkg/work/tree_r1')
sys.path.insert(0,str(P))
from student_pilot.source_seal import inventory
from student_pilot.p3_provenance import digest
def lst(p):
    d={}
    for l in open(p):
        h,f=l.rstrip('\n').split('  ',1); d[f]=h
    return d
inv11=inventory(P); seal11=digest(inv11)
base=lst(N/'w9f/out/TREE_FILES.sha256')
inv10=inventory(N/'w10/work/tree_r1'); invn=inventory(N/'wn2/work/tree_r1')
out=dict(seal11=seal11,n11=len(inv11),seal10=digest(inv10),n10=len(inv10),sealn=digest(invn),nn=len(invn),seal9=digest(base),n9=len(base))
out['wm_list_eq']=lst(N/'wm/out/TREE_FILES.sha256')==inv11
out['wm_tree_eq']=inventory(N/'wm/work/tree_r1')==inv11
def ch(a):
    return sorted(set(a)^set(base)|{f for f in a if f in base and a[f]!=base[f]})
c10=set(ch(inv10)); cn=set(ch(invn)); c11=set(ch(inv11))
out['c10']=sorted(c10); out['cn']=sorted(cn); out['both']=sorted(c10&cn)
rows={}
for f in sorted(c10|cn|c11):
    s10=f in c10; sn=f in cn
    h=inv11.get(f)
    if s10 and not sn: ok = 'eq10' if h==inv10.get(f) else 'DIFF10'
    elif sn and not s10: ok = 'eqN' if h==invn.get(f) else 'DIFFN'
    elif s10 and sn: ok='both'
    else: ok='EXTRA11' if h!=base.get(f) else 'eqbase'
    rows[f]=ok
out['rows']=rows
removed=[f for f in base if f not in inv11]; out['removed_from_base']=removed
json.dump(out,open('/scratch/jjyeung/orch_n30/review_tree11/work/cs/CS.json','w'),indent=1)
print(json.dumps({k:v for k,v in out.items() if k not in('rows','c10','cn')},indent=1))
for f,v in rows.items():
    if v not in('eq10','eqN'): print(v,f)
