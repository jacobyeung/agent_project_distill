import json,hashlib,os
from pathlib import Path
K='/scratch/jjyeung/orch_cd/k1_build/work/kit_k1a'; KC='/scratch/jjyeung/orch_n30/k1_ops3/kc/k1_build/work/kit_k1a'
pins=json.load(open(K+'/out/DEPENDENCIES.json'))
def sha(p):
    h=hashlib.sha256()
    with open(p,'rb') as f:
        for b in iter(lambda:f.read(1<<20),b''): h.update(b)
    return h.hexdigest()
bad=[];kcbad=[];inkit=0;big=0
for p,e in pins.items():
    sz=os.path.getsize(p); big+=sz
    if sha(p)!=e: bad.append(p)
    if p.startswith('/scratch/jjyeung/orch_cd/'):
        q='/scratch/jjyeung/orch_n30/k1_ops3/kc/'+p[len('/scratch/jjyeung/orch_cd/'):]
        if not os.path.exists(q) or sha(q)!=e: kcbad.append(q)
    if p.startswith(K): inkit+=1
print('pins',len(pins),'bytes',big,'orch_cd mismatches',bad,'kc-copy mismatches',len(kcbad),kcbad[:10],'pins inside kit_k1a',inkit)
# kit work/ and native_kit top-level files not pinned: compare orch_cd vs kc
for sub in ('work','native_kit'):
    for n in sorted(os.listdir(K+'/'+sub)):
        p=K+'/'+sub+'/'+n
        if os.path.isfile(p):
            q=KC+'/'+sub+'/'+n
            st='same' if os.path.exists(q) and sha(p)==sha(q) else 'DIFF'
            if st!='same' or p not in pins: print(sub+'/'+n, 'pinned' if p in pins else 'UNPINNED', st, 'mtime', os.path.getmtime(p))
