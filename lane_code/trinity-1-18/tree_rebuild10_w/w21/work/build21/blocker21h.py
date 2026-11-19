"""Prove the full-intake flag boundary without changing sealed code or stores."""
from pathlib import Path
from unittest.mock import patch
import ast,datetime,hashlib,json,os,sys
L=Path(__file__).resolve().parents[2];B=L/'work/build21';D=L/'work/build21h';T=L/'work/tree_r1'
D.mkdir(exist_ok=True)
sys.path[:0]=[str(B),str(T)]
import joblib as J
from student_pilot.p3_provenance import load,pinned,file_pin
from student_pilot.r1_persisted import scope
from student_pilot.r2_intake import intake
from student_pilot.r1_routing import compose_native
from launch_r2.build import bad_string
from naming21 import scan_python_environment
from student_pilot.job_env import key
print(datetime.datetime.now(datetime.timezone.utc).isoformat(),flush=True)
uploads=J.load(B/'UPLOADS.json');paths={}
for item in uploads['files']:
    p=Path(item['local_path'])
    if p.is_file():paths[item['sha256']]=str(p)
cfg=J.load(B/'proofs/capacity/400/request_config.json')
seen=set()
def collect(v):
    if isinstance(v,dict):
        h=v.get('sha256');raw=v.get('path')
        if isinstance(h,str) and isinstance(raw,str) and h not in seen:
            seen.add(h);p=Path(paths.get(h,raw))
            if not p.is_relative_to(L) and '/work/' in raw:p=L/'work'/raw.split('/work/',1)[1]
            if p.is_relative_to(L) and p.is_file():
                paths[h]=str(p)
                if p.suffix=='.json' and p.stat().st_size<4_000_000:
                    try:collect(J.load(p))
                    except (ValueError,UnicodeError):pass
        for x in v.values():collect(x)
    elif isinstance(v,list):
        for x in v:collect(x)
collect(cfg)
host=os.uname();remote=os.uname_result((host.sysname,'fixture-frame-host',host.release,host.version,host.machine))
records=[]
with scope(paths):
    manifest=cfg['r1_training']['routing_inputs']['units']
    m=load(pinned(manifest));assert m['count']==0
    for label,env in [('no_flag',{}),('opaque_flag',{'Q_E7':'1','K6':'1'}),('native_flag',{'STUDENT_R2_FRAME_HOST':'1'})]:
        with patch.object(os,'uname',return_value=remote),patch.dict(os.environ,env,clear=True):
            try:
                items,report=intake(pinned(manifest),limit=None)
                result=dict(status='PASS',admitted=len(items))
            except ValueError as error:result=dict(status='REFUSE',error=str(error))
            records.append(dict(case=label,environment=env,alias=key('STUDENT_R2_FRAME_HOST'),**result))
    with patch.object(os,'uname',return_value=remote),patch.dict(os.environ,{'Q_E7':'1','K6':'1'},clear=True):
        try:
            compose_native(cfg,cfg['streams']['routing'],D/'proofs/compose')
        except ValueError as error:
            records.append(dict(case='real_compose_native_with_opaque_flag',status='REFUSE',error=str(error)))
        else:raise AssertionError('Expected full-intake host admission refusal')
assert [x['status'] for x in records[:3]]==['REFUSE','REFUSE','PASS']
assert all(x['error']=='Local slices must contain at most 2000 rows per family' for x in records if x['status']=='REFUSE')
hashes=J.load(B/'kits/q/b/wh.json')
def name(v,where):
    if bad_string(v,hashes):raise ValueError('INPUT_NAME:'+where+':'+v)
scans=[]
for label,source in [('native',"import os\nos.environ['STUDENT_R2_FRAME_HOST']='1'\n"),
                     ('opaque',"import os\nos.environ['Q_E7']='1'\n"),
                     ('computed',"import os\nk='STU'+'DENT_R2_FRAME_HOST'\nos.environ[k]='1'\n")]:
    try:scan_python_environment(ast.parse(source),name,'b/h.py');result=dict(status='PASS')
    except ValueError as error:result=dict(status='REFUSE',error=str(error))
    scans.append(dict(case=label,source=source,**result))
assert [x['status'] for x in scans]==['REFUSE','PASS','REFUSE']
result=dict(timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat(),GO=False,
    fixture='work/build21/proofs/capacity/400/request_config.json',
    stand_in='Only uname reports a frame host. Empty existing fixture envelopes prevent all row, RGB and store reads. No sealed function is substituted.',
    intake=records,scanner=scans,tree_change_required=True,
    proposed='Add STUDENT_R2_FRAME_HOST -> Q_E7 and STUDENT_R2_LOCAL_NODE -> Q_E8 in job_env.ALIASES; use job_env.key for both lookups in r2_intake.intake (and r2_materialize.materialize for the full producer). Keep all host/local/limit predicates identical.',
    sealed_sources={str(p.relative_to(T)):J.sha(p) for p in (T/'student_pilot/job_env.py',T/'student_pilot/r2_intake.py',T/'student_pilot/r2_materialize.py',T/'student_pilot/r1_routing.py')})
J.write(D/'HOST_FLAG_BLOCKER.json',result)
print(json.dumps(result,indent=2))
