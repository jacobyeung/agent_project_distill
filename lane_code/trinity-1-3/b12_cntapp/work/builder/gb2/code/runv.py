"""usage: runv.py NAME 'B2OPT json' [CID...]  (default: all 160 plain-mappable ARKit + t10 ones from arkit_src_t10). <=14 procs."""
import json, os, subprocess, sys, hashlib
from concurrent.futures import ThreadPoolExecutor
G='/scratch/jjyeung/orch_n30/gt_build'; W=G+'/work'; L2='/scratch/jjyeung/orch_n30/gt_build2'; PY='/scratch/jjyeung/envs/p1cpu/bin/python'
name,opt=sys.argv[1],sys.argv[2]; cids=sys.argv[3:]
P={r['canonical']:r for r in json.load(open(W+'/cr/PILOT300_INPUTS.json'))}
C={p['canonical']:p['gt']['expected_sha256'] for p in json.load(open('/scratch/jjyeung/orch_cd/k1_build/work/kit_k1a/out/CAPTURES.json'))['pilot']}
FR=json.load(open(W+'/ARKIT_FRAMES.json'))
if not cids: cids=[k.split('/')[1] for k in P if k.startswith('arkit')]
od=f'{L2}/out/variants/{name}'; os.makedirs(od,exist_ok=True)
env=dict(os.environ,OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',PYTHONDONTWRITEBYTECODE='1',B2OPT=opt)
def run(c):
    srcset='arkit_src_t10' if FR[c]['plain'] is None else 'arkit_src'
    out=f'{od}/{c}.npz'
    if not os.path.exists(out):
        p=subprocess.run([PY,L2+'/work/b2.py',c,f'{W}/{srcset}/{c}/src',out,json.dumps(P['arkitscenes/'+c]['grid'])],env=env,capture_output=True,text=True)
        if p.returncode: return dict(c=c,rc=p.returncode,err=p.stderr[-300:])
    h=hashlib.sha256(open(out,'rb').read()).hexdigest()
    return dict(c=c,sha=h,match=h==C['arkitscenes/'+c])
with ThreadPoolExecutor(14) as ex: res=list(ex.map(run,cids))
os.makedirs(L2+'/logs',exist_ok=True)
with open(f'{L2}/logs/VARIANT_{name}.jsonl','w') as log:
    log.write(json.dumps(dict(opt=opt))+'\n')
    for x in res: log.write(json.dumps(x)+'\n')
bad=set(open('/tmp/gb2_bad.txt').read().split())
m=[x['c'] for x in res if x.get('match')]
print(name,opt,'match',len(m),'of',len(res),'| of the 40 bad:',len([c for c in m if c in bad]),'| prev-good lost:',sorted(c for c in (x['c'] for x in res if not x.get('match')) if c not in bad),'| fail',[x for x in res if x.get('rc')])
