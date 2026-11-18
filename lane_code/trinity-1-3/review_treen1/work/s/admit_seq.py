import json,os,sys,base64,hashlib
from pathlib import Path
from copy import deepcopy
W=Path('/scratch/jjyeung/orch_n30/review_treen1/work');KIT=W/'restage_r1';ROOT=W/'tmp/admit_root'
sys.path[:0]=[str(W/'pkg/work/tree_r1')];os.environ['R2_FIXTURES']=str(W/'pkg/fixtures')
def read(p):
    v=json.loads(p.read_text());r=base64.b64decode(v['payload']);assert hashlib.sha256(r).hexdigest()==v['sha256'];return json.loads(r)
cfg=read(KIT/'k/c.json');s=read(KIT/'k/s.json')
ROOT.mkdir(parents=True,exist_ok=True)
for k,v in s['entries'].items():
    if 'payload' in v:
        p=ROOT/k;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(base64.b64decode(v['payload']))
def loc(x):
    if isinstance(x,dict):return {k:loc(v) for k,v in x.items()}
    if isinstance(x,list):return [loc(v) for v in x]
    if isinstance(x,str) and x.startswith(('u/','k/')):return str((ROOT if x.startswith('u/') else KIT)/x)
    return x
cfg=loc(cfg)
from launch_r1.entry import admit
from student_pilot import r1_training
out=[]
def step(name,c):
    try:r=admit(deepcopy(c));out.append((name,'ADMIT',r))
    except Exception as e:out.append((name,type(e).__name__+': '+str(e)[:160]))
    print(out[-1],flush=True)
step('kit config as bound',cfg)
c=deepcopy(cfg);c.update(max_pixels=401408,min_pixels=3136);step('+ GUESS processor pins (to reach next gate)',c)
c['r1_training']['store_hashes'].update(pose='1'*64,routing='2'*64,pointing='3'*64);step('+ placeholder store hashes',c)
c['r1_training'].update(continuation_identity='4'*64,row_plan_sha256='5'*64);step('+ placeholder continuation ids',c)
# registry: which components does training_components read? report each slot refusal
from student_pilot.r2_policy import slots,CHOICES
from student_pilot.r2_portable import bound
from student_pilot.p3_provenance import load
reg=load(bound(cfg['r1_training']['registry'],None))
res={}
for name,spec in slots().items():
    e=reg.get(name,{})
    if name in CHOICES or name=='heads_gf1_connector':res[name]='skipped (not read by R1)';continue
    try:
        from student_pilot.r2_policy import record
        record(e,None);res[name]='PASS'
    except Exception as x:res[name]=type(x).__name__+': '+str(x)[:100]
print(json.dumps(res,indent=1))
(W/'ADMIT_SEQ.json').write_text(json.dumps(dict(sequence=out,registry=res),indent=1,default=str))
