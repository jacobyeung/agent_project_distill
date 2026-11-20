M=/scratch/jjyeung/orch_n30/n_review/r1c; mkdir -p $M
cat > $M/hc.py <<'PYEOF'
import sys,json,hashlib,os
W='/scratch/jjyeung/orch_n30/tree_rebuild10_w'
def sha(p): 
    h=hashlib.sha256(); f=open(p,'rb')
    for b in iter(lambda:f.read(1<<20),b''): h.update(b)
    return h.hexdigest()
def man(p):
    d={}
    for l in open(p):
        l=l.rstrip('\n')
        if len(l)>66 and l[64:66]=='  ': d[l[66:]]=l[:64]
    return d
out={}
trees={'launch':W+'/w24c/work/tree_r1','run4':W+'/w24/work/build24f/rehearsal3/p2/s','run5':W+'/w24/work/build24f/rehearsal5/p2/s'}
sys.path.insert(0,trees['launch'])
from student_pilot.source_seal import inventory
from student_pilot.p3_provenance import digest
inv={}
for k,t in trees.items():
    cwd=os.getcwd(); os.chdir(t); f=inventory('.'); os.chdir(cwd)
    inv[k]=f; out['seal_'+k]=[len(f),digest(f)]
# inventory form
def flat(f):
    if isinstance(f,dict): return {k:(v if isinstance(v,str) else (v.get('sha256') if isinstance(v,dict) else str(v))) for k,v in f.items()}
    return {x['path']:x['sha256'] for x in f}
F={k:flat(v) for k,v in inv.items()}
for r in ('run4','run5'):
    a,b=F['launch'],F[r]
    out['tree_diff_'+r]=sorted([p for p in set(a)|set(b) if a.get(p)!=b.get(p)])
# kit manifests
kits={'launch':W+'/w24c/out/kit_n_go/SHA256SUMS.txt','run4':W+'/w24/work/build24i/armed_fixture_final/SHA256SUMS.txt','run5':W+'/work/hash24h1/RUN5_RECOVERED_SHA256SUMS.txt'}
M={}
for k,p in kits.items():
    out['kitman_'+k]=sha(p); M[k]=man(p)
# verify launch kit file bytes vs manifest
bad=[f for f,h in M['launch'].items() if sha(W+'/w24c/out/kit_n_go/'+f)!=h]
out['launch_kit_bytes_mismatch']=bad
for r in ('run4','run5'):
    a,b=M['launch'],M[r]
    out['kit_diff_'+r]=sorted([p for p in set(a)|set(b) if a.get(p)!=b.get(p) and p.startswith(('b/','job.sh'))])
    out['kit_cfg_diff_'+r]=sorted([p for p in set(a)|set(b) if a.get(p)!=b.get(p) and not p.startswith(('b/','job.sh'))])
for f in ('rehearsal4/PREPARED.json','rehearsal5/RUN_STARTED.json','rehearsal5/PREPARED.json'):
    p=W+'/w24/work/build24f/'+f
    out[f]=open(p).read()[:700] if os.path.exists(p) else 'MISSING'
print(json.dumps(out,indent=1))
PYEOF
cd $M && nice -n 10 env OMP_NUM_THREADS=2 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B hc.py > hc_out.json 2>&1; sha256sum hc_out.json; cat hc_out.json
