"""Seal the real m400 bindings and the four-rank launch configuration."""
from pathlib import Path
from copy import deepcopy
import base64,hashlib,json,shutil,sys,ast
L=Path(__file__).resolve().parents[2];D=L/'work/build24b';B=L/'work/build24';T=L/'work/tree_r1';A=L/'attic/build24b'
sys.path[:0]=[str(B),str(T)]
import joblib as J
from student_pilot.source_seal import inventory,archive,create,check_archive
from student_pilot.p3_provenance import digest,file_pin,source_files
from student_pilot.r1_persisted import INIT_POLICY
from launch_r2.build import capsule_json

def cap(k,n,v):(k/n).write_bytes(capsule_json(v))
def reseal(k):
 fs={str(p.relative_to(k)):J.sha(p) for p in k.rglob('*') if p.is_file() and p.name not in ('SHA256SUMS.txt','BUILD.json')}
 (k/'SHA256SUMS.txt').write_text(''.join(f'{h}  {n}\n' for n,h in sorted(fs.items())))
 b=J.load(k/'BUILD.json');b.update(GO=False,kit_sha256=J.seal(k));cap(k,'BUILD.json',b);return J.seal(k)
def main():
 real=L.parent/'ext/m400real';receipt=J.load(real/'e.json');run=J.load(real/'r.json');assert receipt['pins']['artifact']['sha256'].startswith('5083243c')
 prep=J.load(real/('files'+run['preparation']['path']));model=J.load(real/('files'+prep['model']['path']));manifest=J.load(real/'MANIFEST.json')
 m4={key:J.sha(real/name) for key,name in [('d','DONE.json'),('e','e.json'),('r','r.json'),('p','RP.json'),('v','MANIFEST.json')]}
 m4.update(a=receipt['pins']['artifact']['sha256'],t='dcd49569e1555e18c403207f429de7b352f806bb11827fb57aa9973f4ceec7b5',b=21583032320)
 files=inventory(T);tree=digest(files);J.write(D/'TREE_FILES.json',files);J.write(L/'out/TREE_SEAL.json',dict(tree_sha256=tree,files=len(files)))
 closure={str(p.relative_to(T)):J.sha(p) for p in source_files([T/'student_pilot/carrier_c1_run.py'])};records={}
 for name in ('q','n'):
  k=B/'kits'/name
  save=A/('kit_'+name)
  if not save.exists():shutil.copytree(k,save)
  ns=J.load(k/'k/p.json')['namespace'];control=J.load(k/'k/a.json');old=k/control['source']['path']
  old.rename(A/(name+'_'+old.name))
  target=k/'k'/('t_'+tree[:16]+'.tar');archive(T,target,files,compress=True);check_archive(file_pin(target),files)
  source=dict(path=str(target.relative_to(k)),sha256=J.sha(target),tree_sha256=tree)
  cap(k,'k/7.json',dict(schema='c1-sealed-source-v1',commit='sha256:'+tree,tree_sha256=tree,files=files,
    archive={key:source[key] for key in ('path','sha256')},sources=closure,operation_sources=closure))
  code=create(T,target,closure,{},archive_path=ns+'/t.tar');raw=(json.dumps(code,sort_keys=True,indent=2)+'\n').encode()
  (k/'k/c0.json').write_bytes(json.dumps(dict(encoding='base64',payload=base64.b64encode(raw).decode(),sha256=hashlib.sha256(raw).hexdigest())).encode())
  spec=J.load(k/'k/p.json');spec.update(step=400,milestone='h_6ed2c7aa/m400',p_run=run,m4=m4,code_sha256=hashlib.sha256(raw).hexdigest());spec.pop('handover',None)
  for filename in ('k/n.json','k/c.json'):
   cfg=J.load(k/filename);cfg['init_artifact']['artifact']=receipt['pins']['artifact'];cfg['routing_opener_init']='keep';cfg['world_size']=4
   cfg['r1_training'].update(p_run=run,handover_receipt=dict(path=ns+'/e.json',sha256=m4['e']),persisted_files={p['sha256']:ns+'/u/'+p['sha256'] for p in receipt['pins'].values()},
    proof_mode='train' if name=='n' else 'q',donor_config_sha256=spec['p_runtime_identity'])
   if name=='n':cfg['r1_training']['init_policy']=INIT_POLICY
   else:cfg['r1_training'].pop('init_policy',None)
   if filename=='k/c.json':cfg['code']=dict(path='k/7.json',sha256=J.sha(k/'k/7.json'))
   cap(k,filename,cfg)
  cap(k,'k/p.json',spec);r=J.load(k/'k/r.json');r['milestone']=400;cap(k,'k/r.json',r)
  control.update(source=source,GO=False);cap(k,'k/a.json',control)
  (k/'b/z.py').write_bytes((B/'joblib.py').read_bytes());(k/'b/g.py').write_bytes((D/'g.py').read_bytes())
  s=(k/'b/resolve.py').read_text().replace("p.add_argument('--listing',required=True)","p.add_argument('--listing')");(k/'b/resolve.py').write_text(s)
  build=J.load(k/'BUILD.json');build.update(GO=False,source_seal=tree);build['resource_request']['minimum_gpu_gib']=75
  if name=='n':
   build['resource_request'].update(partition='advanced',gpus=4,ranks=4)
   # The launch remains gated by the existing GO and native host/review admission.
   (k/'b/t.py').write_text('''import sys,subprocess
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from z import load,seal
k=Path(__file__).resolve().parents[1];seal(k)
if load(k/'k/a.json')['GO'] is not True:raise SystemExit(0)
if len(sys.argv)!=3:raise ValueError('E80')
raise SystemExit(subprocess.run([sys.executable,'-s','-B','-m','torch.distributed.run','--standalone','--nnodes=1','--nproc_per_node=4',str(k/'b/u.py'),*sys.argv[1:]],check=False).returncode)
''')
   (k/'b/u.py').write_text('''import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from z import load,seal
k=Path(__file__).resolve().parents[1];seal(k)
if load(k/'k/a.json')['GO'] is not True:raise ValueError('E03')
r=Path(sys.argv[1]);q=load(r/'q/RESULT.json')
if q.get('status')!='ADMIT' or q.get('init_milestone')!=400:raise ValueError('E81')
sys.path.insert(0,str(r/'s'))
from student_pilot.p3_provenance import load as read,pinned
from student_pilot.carrier_c1_run import identity,train
from student_pilot.r1_persisted import scope
cfg=read(sys.argv[2]);before=read(pinned(q['config']))
if identity(cfg)!=identity(before) or cfg['world_size']!=4:raise ValueError('E82')
from launch_r1.entry import admit
with scope(cfg['r1_training']['persisted_files']):
 admit(cfg)
 train(cfg)
''')
   rawj=json.loads((k/'k/j.json').read_text());shell=base64.b64decode(rawj['payload']).decode()
   marker='/usr/bin/python3 "$Q_KIT/b/o.py" "$Q_ROOT" "$rc" "$rr"'
   addition='''if [[ "$rc" == 0 && "$rr" == 0 ]]; then
"${BW[@]}" "$PILOT_VENV/bin/python" -s -B "$Q_KIT/b/t.py" "$Q_NS/p" "$Q_NS/v.json" 2>&1 | /usr/bin/python3 "$Q_KIT/b/l.py" "$Q_KIT" > "$Q_ROOT/t.log"
rc=${PIPESTATUS[0]}
fi
'''
   assert shell.count(marker)==1;shell=shell.replace(marker,addition+marker)
   payload=shell.encode();rawj.update(payload=base64.b64encode(payload).decode(),sha256=hashlib.sha256(payload).hexdigest());(k/'k/j.json').write_text(json.dumps(rawj))
  cap(k,'BUILD.json',build);seal=reseal(k)
  oldlist=J.load(B/('UPLOADS_'+name+'.json'))
  uploads=[x for x in oldlist['files'] if x['opaque_name'].startswith('u/')]
  uploads += [dict(local_path=str(p),opaque_name=name+'/'+str(p.relative_to(k)),sha256=J.sha(p),bytes=p.stat().st_size,needed_minimal=True) for p in k.rglob('*') if p.is_file()]
  J.write(D/('UPLOADS_'+name+'.json'),dict(files=uploads,total_bytes=sum(x['bytes'] for x in uploads)))
  records[name]=dict(step=400,tree_seal=tree,kit_seal=seal,GO=False,proof_mode='train' if name=='n' else 'q')
 J.write(D/'KIT.json',records)
 J.write(L/'out/M400_PINS.json',dict(schema='build24b-m400-bound-v1',GO=False,files=m4,receipt_pins=receipt['pins'],run=run,model_manifest=prep['model'],model_files=model['files'],
  artifact=receipt['pins']['artifact'],step=400,optimizer='fresh',training_start_step=0,init_policy=INIT_POLICY,
  tar=dict(sha256=m4['t'],bytes=m4['b'],parts=[f"/project/community/jjyeung/okh7/x_22c714e1/w/{i}" for i in range(4)]),
  archive=dict(path='/project/community/jjyeung/okh7/h_6ed2c7aa/m400/s.tar',manifest_sha256=m4['v'],local_archive_present=(real/'s.tar').is_file()),
  no_fill_step=True,ignored='RP checkpoint_000414 is pinned transport provenance only; no checkpoint or post-400 state enters initialization.'))
 print(json.dumps(records,indent=2))
if __name__=='__main__':main()
