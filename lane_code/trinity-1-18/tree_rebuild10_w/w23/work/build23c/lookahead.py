from pathlib import Path
import datetime,json,subprocess,sys,os
L=Path(__file__).resolve().parents[2];B=L/'work/build21';D=L/'work/build23c';K=B/'kits/q'
sys.path[:0]=[str(B),str(L/'work/tree_r1')]
import joblib as J
old=str(L.parent/'w21');new=str(L)
args=[x.replace(old,new) for x in J.load(L/'work/build21g/proofs/view/after.json')]
view=J.load(L/'work/build21g/VIEW.json');node=Path(view['variables']['Q_ROOT'].replace(old,new));ns=view['variables']['Q_NS']
paths={}
for item in J.load(B/'UPLOADS.json')['files']:
 p=B/'upload'/item['opaque_name']
 if not p.is_file():p=Path(item['local_path'].replace(old,new))
 if p.is_file():
  assert J.sha(p)==item['sha256'],str(p)
  paths[item['sha256']]=str(p)
cfg=J.load(K/'k/n.json');cfgpin=J.write(node/'kitq23c_config.json',cfg)
assert cfgpin['sha256']==J.load(L/'work/build23b/LOOKAHEAD_AFTER.json')['decoded_config_sha256']
request=J.load(K/'k/r.json');spec=J.load(K/'k/p.json')
request.update(config=cfgpin,staged_pins=[dict(path=p,sha256=h) for h,p in paths.items()]+[cfgpin],room_audit=cfg['r1_training']['room_audit'],frame_roots=spec['frame_roots'],milestone=400,device='cpu',memory_gib=16,_paths=paths)
J.write(node/'kitq23c_request.json',request)
records=[]
commands=[('view',args+['/usr/bin/true']),
 ('gpu_guard_cpu',args+[sys.executable,'-s','-B',str(K/'b/g.py')]),
 ('gpu_guard_stand_in',args+[sys.executable,'-s','-B',str(D/'view_guard.py')]),
 ('native_kitq',args+[sys.executable,'-s','-B',str(K/'b/a.py'),'q',ns+'/minimal23c',ns+'/kitq23c_request.json'])]
for label,cmd in commands:
 p=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
 records.append(dict(stage=label,returncode=p.returncode,stdout=p.stdout,stderr=p.stderr))
 print(label,p.returncode,flush=True)
 if label in ('view','gpu_guard_stand_in'):assert p.returncode==0,p.stderr
 if label=='gpu_guard_cpu':assert p.returncode!=0 and 'RuntimeError: E42' in p.stderr and json.loads(p.stdout)['a'] is False
result=J.load(node/'minimal23c/q/RESULT.json')
assert result['refusal']=='ValueError:R1_PROOF_FRAME_HOST_REQUIRED',result
J.write(D/'LOOKAHEAD.json',dict(timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat(),GO=False,kit_seal=J.seal(K),config_source='work/build21/kits/q/k/n.json',decoded_config_sha256=cfgpin['sha256'],config_unchanged=True,request=request,command=args,runs=records,result=result,stand_ins=['CPU Python instead of staged GPU environment','Stubbed torch only for the guard pass; real CPU torch for native entry','Empty source directories and prefixed AS/AL/P destinations as in build21g','No production model/store substitution; frame-host boundary remains']))
print(json.dumps(dict(refusal=result['refusal'],status='PASS')))
