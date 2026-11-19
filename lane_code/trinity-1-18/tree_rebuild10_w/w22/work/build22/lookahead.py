from pathlib import Path
import datetime,json,subprocess,sys,os
L=Path(__file__).resolve().parents[2]; B=L/'work/build21'; D=L/'work/build22';K=B/'kits/q'
sys.path[:0]=[str(B),str(L/'work/tree_r1')]
import joblib as J
old=str(L.parent/'w21'); new=str(L)
args=[x.replace(old,new) for x in J.load(L/'work/build21g/proofs/view/after.json')]
for i,x in enumerate(args):
 if x in ('--bind','--ro-bind'):
  for raw in args[i+1:i+3]:
   p=Path(raw)
   if p.is_relative_to(L):p.mkdir(parents=True,exist_ok=True)
view=J.load(L/'work/build21g/VIEW.json');node=Path(view['variables']['Q_ROOT'].replace(old,new));ns=view['variables']['Q_NS']
paths={}
for item in J.load(B/'UPLOADS.json')['files']:
 p=B/'upload'/item['opaque_name']
 if not p.is_file():p=Path(item['local_path'].replace(old,new))
 if p.is_file():
  assert J.sha(p)==item['sha256'],str(p)
  paths[item['sha256']]=str(p)
cfg=J.load(K/'k/n.json');cfgpin=J.write(node/'kitq_config.json',cfg)
request=J.load(K/'k/r.json');spec=J.load(K/'k/p.json')
request.update(config=cfgpin,staged_pins=[dict(path=p,sha256=h) for h,p in paths.items()]+[cfgpin],room_audit=cfg['r1_training']['room_audit'],frame_roots=spec['frame_roots'],milestone=600,device='cpu',memory_gib=16,_paths=paths)
J.write(node/'kitq_request.json',request)
records=[]
for label,cmd in [('view',args+['/usr/bin/true']),('gpu_guard',args+[sys.executable,'-s','-B',str(K/'b/g.py')]),('native_kitq',args+[sys.executable,'-s','-B',str(K/'b/a.py'),'q',ns+'/kitq',ns+'/kitq_request.json'])]:
 p=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
 records.append(dict(stage=label,returncode=p.returncode,stdout=p.stdout,stderr=p.stderr))
result=J.load(node/'kitq/q/RESULT.json') if (node/'kitq/q/RESULT.json').is_file() else None
J.write(D/'LOOKAHEAD_KITQ.json',dict(timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat(),GO=False,kit_seal=J.seal(K),config_source='work/build21/kits/q/k/n.json',decoded_config_sha256=cfgpin['sha256'],config_unchanged=True,request=request,command=args,runs=records,result=result,stand_ins=['CPU Python instead of staged GPU environment','Empty source directories and prefixed AS/AL/P destinations as in build21g','No production model or store content replaced; boundaries are reported']))
print(json.dumps(dict(runs=records,result=result),indent=2))
