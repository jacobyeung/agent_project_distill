import sys
sys.path[:0]=['/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24c/work/build24m4c', '/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24/work/build24', '/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24/work/build21', '/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24/work/build22', '/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24/work/build24f', '/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24/work/build24d', '/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24c/work/tree_r1']
from pathlib import Path
import base64,hashlib,importlib.util,json,os,shutil,signal,sqlite3,subprocess,sys,time
L=Path(__file__).resolve().parents[2];D=L/'work/build24m4c';F=D/'review_tests';F.mkdir(exist_ok=True)
sys.path[:0]=[str(L/'work/build24'),str(Path('/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24')/'work/build24f'),str(L/'work/tree_r1'),str(D)]
sys.path.insert(0,str(Path(__file__).resolve().parent))
import joblib as J
from kit24f import reseal
from student_pilot.carrier_c1_run import identity
def kitcopy(src,dst):
 p=Path(src)
 if p.name in ('BUILD.json','SHA256SUMS.txt','p.json','a.json','rv.py','h.py','t.py','x.py','job.sh','pc.sh'):return shutil.copyfile(src,dst)
 os.link(src,dst);return dst

def capsule(v):
 raw=(json.dumps(v,sort_keys=True,indent=2)+'\n').encode()
 return json.dumps(dict(encoding='base64',payload=base64.b64encode(raw).decode(),sha256=hashlib.sha256(raw).hexdigest())).encode()

def fixture(name,kind='pass',go=False,legacy=False):
 root=F/name;root.mkdir();k=root/'kit';shutil.copytree(L/('out/kit_n_go' if go else 'work/build24/kits/n'),k,copy_function=kitcopy)
 target=root/'target';target.mkdir();private=target/'n_r';private.mkdir(mode=0o700)
 spec=J.load(k/'k/p.json');spec['n_root']=str(target);(k/'k/p.json').write_bytes(capsule(spec))
 c=J.load(k/'k/a.json');c['review_wait_seconds']=2 if kind=='timeout' else 30;(k/'k/a.json').write_bytes(capsule(c))
 # Test-only fast polling on a resealed writable kit; production remains 30 s.
 p=k/'b/rv.py';p.write_text(p.read_text().replace('interval=30','interval=0.05'))
 if legacy:(k/'b/h.py').write_bytes((Path('/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24')/'attic/build24i/work/build24/kits/n/b/h.py').read_bytes())
 node=root/'node/q_22c714e1_91';(node/'p/q').mkdir(parents=True);(node/'p/s').symlink_to(L/'work/tree_r1',target_is_directory=True)
 receipt={'streams':{}}
 for stream in ('pose','vqa','routing','pointing'):
  db=node/(stream+'.sqlite')
  with sqlite3.connect(db) as con:
   con.execute('create table rows (i integer primary key,row text,target text)')
   for i in range(64):
    thought='\t \n' if ((kind=='answer_only' and stream=='vqa') or kind=='empty_'+stream) and i==63 else 'The synthetic fixture contains the printed observation.'
    row=dict(canonical=('scannet/scene0000_00' if kind=='bench' else 'scannet/scene0155_00') if kind in ('bench','dev') and stream=='vqa' and i==63 else 'scannet/scene9999_00',qid=stream+str(i),question_type='fixture',form='direct',target='<think>'+thought+'</think>\nA',student_input=dict(frames=[{'path':'fixture','sha256':'0'*64}],frame_indices=[0],timestamps=[0.0]))
    con.execute('insert into rows values (?,?,?)',(i,json.dumps(row),'{}'))
  receipt['streams'][stream]=dict(database=dict(path=str(db),sha256=J.sha(db)),count=64)
 cfg=dict(world_size=4,r1_training=dict(init_policy='step400_export_weights_fresh_v1'),preparation=J.write(node/'prep.json',receipt))
 production=J.load(L/'work/build24/kits/n/k/n.json')
 paths={v['sha256']:v['local_path'] for v in J.load(Path('/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24')/'work/build24i/UPLOADS_n.json')['files'] if v['opaque_name'].startswith('u/')}
 def local(v):
  if isinstance(v,dict):return {key:(paths[v['sha256']] if key=='path' and 'sha256' in v else local(x)) for key,x in v.items()}
  return v
 cfg['r1_training']['room_authority']=local(production['r1_training']['room_authority'])
 for field in ('dev_scene_exclusions','benchmark_scene_exclusions'):cfg[field]=local(production[field])

 J.write(node/'rooms.json',dict(status='PASS',scope='synthetic reader fixture'))
 value=identity(cfg)
 from launch_r1.entry import ASSERTIONS
 hostpin=J.write(node/'p/q/host.json',dict(status='PASS',config_identity=value,assertions=dict.fromkeys(ASSERTIONS,True),loader_audit={'complete':True}))
 J.write(node/'p/q/RESULT.json',dict(status='ADMIT',init_milestone=400,config=J.write(node/'prepared.json',cfg),host_receipt=hostpin))
 if legacy:shutil.copyfile(node/'p/q/host.json',node/'p/host.json')
 # x.py supplies only the already-prepared boundary. Execute the exact decoded
 # h/rv/t shell segment; the real batch shell and copier traps surround it.
 decoded=base64.b64decode(json.loads((k/'k/j.json').read_text())['payload']).decode()
 start=decoded.index('"${BW[@]}" "$PILOT_VENV/bin/python" -B -s "$Q_KIT/b/h.py"')
 end=decoded.index('/usr/bin/python3 -B "$Q_KIT/b/o.py"',start)
 tail=decoded[start:end]
 # The last fi closes the canary/room predicate supplied by the boundary.
 tail=tail.rsplit('fi',1)[0]
 script=root/'prepared.sh'
 import shlex
 prefix='set -uo pipefail\nBW=()\nPILOT_VENV='+shlex.quote(str(Path(sys.executable).parent.parent))+'\nQ_KIT='+shlex.quote(str(k))+'\nQ_ROOT='+shlex.quote(str(node))+'\nQ_NS="$Q_ROOT"\n'
 script.write_text(prefix+tail+'\nexit "$rc"\n')
 (k/'b/t.py').write_text('from pathlib import Path\nimport sys\nPath(sys.argv[2]).with_name("T_STARTED").write_text("t.py boundary; no training executed\\n")\n')
 (k/'b/x.py').write_text('import subprocess\nraise SystemExit(subprocess.run(["/bin/bash",'+repr(str(script))+']).returncode)\n')
 p=k/'job.sh';p.write_text(p.read_text().replace('OMP_NUM_THREADS=48 MKL_NUM_THREADS=48 OPENBLAS_NUM_THREADS=48','OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8'))
 # The system python on this node is not the kit's 3.12 interpreter.
 p=k/'job.sh';p.write_text(p.read_text().replace('python3 ',sys.executable+' '))
 p=k/'b/pc.sh';p.write_text(p.read_text().replace('python3 ',sys.executable+' '))
 reseal(k);request=root/'r.json';J.write(request,{})
 log=(root/'job.log').open('w')
 proc=subprocess.Popen(['/bin/bash',str(k/'job.sh'),str(request)],stdout=log,stderr=subprocess.STDOUT,env={**os.environ,'SLURM_TMPDIR':str(root/'node'),'SLURM_JOB_ID':'91'})
 return dict(root=root,k=k,node=node,live=target/'o/91/live',private=private,value=value,proc=proc,log=log)

def await_marker(f,name):
 end=time.monotonic()+35
 while not (f['live']/name).exists():
  if f['proc'].poll() is not None:raise AssertionError((name,(f['root']/'job.log').read_text()))
  if time.monotonic()>end:raise AssertionError('test marker timeout '+str(f['root']))
  time.sleep(.05)

records=[]
for go in (False,True):
 for kind,expected in [('pass',None),('identity','R1_REVIEW_IDENTITY_DIFFERS'),('verdict','R1_REVIEW_NOT_PASS'),('mode','R1_REVIEW_FILE_UNUSABLE'),('symlink','R1_REVIEW_FILE_UNUSABLE'),('directory_mode','R1_REVIEW_FILE_UNUSABLE'),('timeout','R1_REVIEW_TIMEOUT'),('answer_only','R1_ANSWER_ONLY_ROWS'),('empty_routing','R1_ANSWER_ONLY_ROWS'),('empty_pose',None),('empty_pointing',None),('bench','R1_PROTECTED_ROOM_ROWS'),('dev','R1_PROTECTED_ROOM_ROWS'),('term','R1_REVIEW_INTERRUPTED'),('usr1','R1_REVIEW_INTERRUPTED')]:
  f=fixture(('go_' if go else 'no_')+kind,kind,go)
  if kind not in ('answer_only','empty_routing','bench','dev'):
   await_marker(f,'WAITING_REVIEW.json');time.sleep(.15)
   if kind in ('term','usr1'):f['proc'].send_signal(signal.SIGTERM if kind=='term' else signal.SIGUSR1)
   elif kind!='timeout':
    review=dict(verdict='FAIL' if kind=='verdict' else 'PASS',config_identity='0'*64 if kind=='identity' else f['value'],evidence=dict(reviewer='synthetic-test-only'))
    p=f['private']/'review.json'
    if kind=='symlink':
     actual=f['root']/'receipt.json';J.write(actual,review);actual.chmod(0o600);p.symlink_to(actual)
    else:J.write(p,review);p.chmod(0o644 if kind=='mode' else 0o600)
    if kind=='directory_mode':f['private'].chmod(0o755)
  rc=f['proc'].wait(timeout=40);f['log'].close()
  started=(f['node']/'T_STARTED').exists()
  if expected:
   refusal=J.load(f['live']/'REVIEW_REFUSED.json');assert refusal['refusal']==expected,(kind,refusal)
   assert rc!=0 and not started
   if kind in ('answer_only','empty_routing','bench','dev'):assert not (f['live']/'WAITING_REVIEW.json').exists()
  else:
   assert rc==0 and started,(kind,rc,(f['root']/'job.log').read_text())
   accepted=J.load(f['live']/'REVIEW_ACCEPTED.json');assert accepted['identity']==f['value']
   cfg=J.load(f['node']/'v.json');assert identity(cfg)==f['value']
   assert J.sha(cfg['r1_training']['review']['path'])==accepted['review_sha256']
   assert J.load(cfg['preparation']['path'])['r1_training']==cfg['r1_training']
  if kind in ('term','usr1'):
   assert (f['live']/'copy.json').exists(),list(f['live'].iterdir())
  records.append(dict(GO=go,case=kind,returncode=rc,refusal=expected,t_started=started,final_copy=(f['live']/'copy.json').exists()))
  print(go,kind,rc,expected,flush=True)

# Before control: h.py rejects before publication because no staged review exists.
f=fixture('before',legacy=True);rc=f['proc'].wait(timeout=30);f['log'].close()
assert rc!=0 and not (f['live']/'WAITING_REVIEW.json').exists() and not (f['node']/'T_STARTED').exists()
assert 'R1_REVIEW_RECEIPT_MISSING' in (f['node']/'h.log').read_text()
J.write(D/'REVIEW_TESTS.json',dict(status='PASS',records=records,before='R1_REVIEW_RECEIPT_MISSING before publication',stand_ins=['Prepared synthetic stores and host receipt','t.py boundary marker; no training'],production_poll_seconds=30,test_poll_seconds=.05))
