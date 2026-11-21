"""fix8: build W/w30f1/n_go from W/w28fix/n_go with F1 (vqa receipt a7682dae) and the receipt preflight in b/pf.py."""
import sys, os, json, shutil, hashlib, base64, subprocess
from pathlib import Path
W=Path('/scratch/jjyeung/orch_n30/tree_rebuild10_w'); F=W/'w30f1'; OLD=W/'w28fix/n_go'; NEW=F/'n_go'
SUP=W/'w24z11b/work/build24m4x2'
sys.path[:0]=[str(SUP)]
from support import J, cap, reseal, scan
OLDSEAL='9e809db4e0817adfad3d4ebd74fb39a6d15b39aea8f0cb129a0da5c4ecaf3405'
NEWR='a7682dae68defb91ed5e19120e8f53c149016d70728c417c817c6c408020a22a'; OLDR='e3ee51daa46af30fa8e84a05c12448d7fc3dc9cade05284707f9df322bbe44d0'
P_DIV='/lustre/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/e84d901c/z/4c230a7e.json'
def sha(p): return J.sha(p)
out={}
assert J.seal(OLD)==OLDSEAL and J.load(OLD/'BUILD.json')['kit_sha256']==OLDSEAL; out['old_seal']=OLDSEAL
# tree of the kit, for the tree's own functions
T=F/'tree'
if not T.exists():
    T.mkdir(parents=True); subprocess.run(['tar','xf',str(OLD/'k/t_e047002134f979bd.tar'),'-C',str(T)],check=True)
out['tree_tar']=sha(OLD/'k/t_e047002134f979bd.tar')
sys.path.insert(0,str(T))
# 1. the receipt, reproduced from the Trinity source of e3ee51da
src=W/'w18/work/build18/inputs/v7_receipt.json'; assert sha(src)==OLDR
v=json.loads(src.read_bytes()); assert (json.dumps(v,sort_keys=True,indent=2)+'\n').encode()==src.read_bytes()
v['division']=dict(path=P_DIV,sha256=v['division']['sha256'])
raw=(json.dumps(v,sort_keys=True,indent=2)+'\n').encode(); assert hashlib.sha256(raw).hexdigest()==NEWR,hashlib.sha256(raw).hexdigest()
(F/'u').mkdir(exist_ok=True); (F/'u'/NEWR).write_bytes(raw); (F/'u'/NEWR).chmod(0o644)
assert (F/'u'/NEWR).read_bytes()==(F/'ship'/NEWR).read_bytes()
out['receipt']=dict(sha256=NEWR,bytes=len(raw),same_as_shipped=True)
# 2. copy the kit
if NEW.exists():
    # an earlier run of this script made NEW; restore every member from OLD (same file set) and rebuild
    a={str(p.relative_to(OLD)) for p in OLD.rglob('*') if p.is_file()}; b={str(p.relative_to(NEW)) for p in NEW.rglob('*') if p.is_file()}
    assert a==b,(a^b)
    for n in sorted(a): shutil.copy2(OLD/n,NEW/n)
    out['restored_from_old_before_rebuild']=True
else:
    shutil.copytree(OLD,NEW,copy_function=shutil.copy2)
assert J.seal(NEW)==OLDSEAL
# capsule round trip with the kit tool (cap reproduces the old capsule bytes)
tmp=F/'rt';tmp.mkdir(exist_ok=True)
for n in ('k/c.json','k/n.json','k/p.json','BUILD.json'):
    cap(tmp/'x.json',J.load(OLD/n)); out.setdefault('cap_roundtrip',{})[n]=(tmp/'x.json').read_bytes()==(OLD/n).read_bytes()
# 3. c.json and n.json through the tree's configure_store
os.chdir(F)
from student_pilot.r1_training import configure_store
from student_pilot import r1_persisted
pin=dict(path='u/'+NEWR,sha256=NEWR)
def diff(a,b,p=''):
    if isinstance(a,dict) and isinstance(b,dict):
        r=[]
        for k in sorted(set(a)|set(b)): r+=diff(a.get(k,'<absent>'),b.get(k,'<absent>'),p+'.'+k)
        return r
    return [] if a==b else [(p,a,b)]
for n in ('k/c.json','k/n.json'):
    cfg=J.load(OLD/n)
    with r1_persisted.scope({NEWR:str(F/'u'/NEWR)}): new=configure_store(cfg,pin)
    d=diff(cfg,new)
    out.setdefault('config_diff',{})[n]=[(p,a,b) for p,a,b in d]
    assert sorted(p for p,_,_ in d)==['.r1_training.store_parameter.path','.r1_training.store_parameter.sha256','.streams.vqa.path','.streams.vqa.sha256'],d
    cap(NEW/n,new)
# 4. p.json: stage the receipt (uploads and pin_paths by the arm rule)
spec=J.load(OLD/'k/p.json')
assert spec['pin_paths']=={u['sha256']:spec['namespace']+'/u/'+u['sha256'] for u in spec['uploads']}
staged={u['sha256']:u for u in spec['uploads']}; assert NEWR not in staged
staged[NEWR]=dict(sha256=NEWR,bytes=len(raw),opaque_name='u/'+NEWR)
new=dict(spec); new['uploads']=[staged[h] for h in sorted(staged)]
new['pin_paths']={h:spec['namespace']+'/u/'+h for h in sorted(staged)}
d=diff({k:v for k,v in spec.items() if k not in ('uploads','pin_paths')},{k:v for k,v in new.items() if k not in ('uploads','pin_paths')}); assert not d
out['p_json']=dict(uploads_added=[staged[NEWR]],pin_paths_added={NEWR:new['pin_paths'][NEWR]},uploads=len(new['uploads']),other_keys_changed=d)
cap(NEW/'k/p.json',new)
# 5. preflight
shutil.copyfile(F/'ship/pf.py',NEW/'b/pf.py'); os.chmod(NEW/'b/pf.py',0o644)
# 6. BUILD.json (config_sha256 as launch_r1.build writes it) and the seal with the kit tool
b=J.load(OLD/'BUILD.json'); b['config_sha256']=sha(NEW/'k/c.json'); cap(NEW/'BUILD.json',b)
seal=reseal(NEW); out['new_seal']=seal
# the 24m4 decoded-scan helper predates b/a.py of 9e809db4; record its result on both kits
for tag,k in (('old',OLD),('new',NEW)):
    try: s=scan(k,'n_go'); out.setdefault('decoded_scan_24m4_helper',{})[tag]='PASS'
    except Exception as e: out.setdefault('decoded_scan_24m4_helper',{})[tag]=type(e).__name__+':'+str(e)[:160]
from launch_r1.build import verify
out['verify_kit_tree']=verify(NEW)==seal
# 7. member diff
def inv(k): return {str(p.relative_to(k)):(sha(p),p.stat().st_mode&0o777) for p in sorted(k.rglob('*')) if p.is_file()}
a,bb=inv(OLD),inv(NEW); assert set(a)==set(bb)
out['changed_members']=[n for n in a if a[n]!=bb[n]]
out['config_sha256']=dict(old=J.load(OLD/'BUILD.json')['config_sha256'],new=b['config_sha256'],old_payload=json.loads((OLD/'k/c.json').read_text())['sha256'],new_payload=json.loads((NEW/'k/c.json').read_text())['sha256'])
out['k_file_sha256']={n:dict(old=sha(OLD/n),new=sha(NEW/n)) for n in ('k/c.json','k/n.json','k/p.json','BUILD.json','SHA256SUMS.txt','b/pf.py','k/t_e047002134f979bd.tar')}
(F/'BUILD_F1.json').write_text(json.dumps(out,indent=1,sort_keys=True,default=str)+'\n')
print(json.dumps(out,indent=1,sort_keys=True,default=str)[:6000])
