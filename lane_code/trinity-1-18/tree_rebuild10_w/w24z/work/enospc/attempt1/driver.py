import os,sys,json,subprocess,time,traceback,runpy,hashlib,types,ast,shutil,signal
from pathlib import Path
W=Path(__file__).resolve().parent;K=W/'kit';X=W/'mnt';N=W/'node';L=W/'logs';PY=sys.executable
os.environ.update(TEST_X=str(X),TEST_W=str(W),FAKE_SINK=str(W/'sink'),PATH=str(W/'bin')+':'+os.environ['PATH'],SLURM_JOB_ID='24004',TMPDIR=str(W/'tmp'),OMP_NUM_THREADS='8',OPENBLAS_NUM_THREADS='8',MKL_NUM_THREADS='8')
sys.path.insert(0,str(K/'b'));import z,pc,rv,ep
zl=z.load;pr=pc.read
def mapped(f):
 def g(p):
  v=f(p)
  if Path(p).name=='p.json':v['n_root']=str(X)
  return v
 return g
z.load=mapped(zl);pc.read=mapped(pr);rv.load=z.load;ep.load=z.load
N.mkdir();T=N/'p/q/r';T.mkdir(parents=True)
for n in ('t.log','q.log','h.log','rooms.log'):(N/n).write_text('q 1\n')
(N/'24004.steps').write_text('1\n')
for n,m in (('m100','artifact.json'),('checkpoint_7','complete.json')):
 d=T/n;d.mkdir();(d/m).write_text(json.dumps(dict(step=7,tag=n))+'\n');(d/'a.bin').write_bytes(b'q'*8192)
for d in ('o/24004/live','o/gcs_claims','n_s','n_r','j','o/24005/live'):(X/d).mkdir(parents=True,exist_ok=True)
os.chmod(X/'n_s',0o700);os.chmod(X/'n_r',0o700)
names=z.load(K/'k/y.json')['objects']; sessions={key+f'.part{i:02d}-of-04':'https://local.invalid/'+label+'/'+str(i) for label,key in names.items() for i in range(4)}
(X/'n_s/sess.json').write_text(json.dumps(sessions));os.chmod(X/'n_s/sess.json',0o600)
results=[]
def record(name,fn):
 t=time.monotonic()
 with (L/(name+'.log')).open('w') as f:
  try:
   result=fn();out=dict(name=name,ok=True,result=result)
  except Exception as e:
   traceback.print_exc(file=f);out=dict(name=name,ok=False,error=type(e).__name__,errno=getattr(e,'errno',None),message=str(e))
  out['seconds']=round(time.monotonic()-t,3);out['log']=str(L/(name+'.log'));f.write(json.dumps(out,sort_keys=True)+'\n')
 results.append(out);print(json.dumps(out),flush=True);return out

def cli(name,args,stdout=None):
 with (L/(name+'.stderr')).open('wb') as err:
  if stdout is None:
   with (L/(name+'.stdout')).open('wb') as out:r=subprocess.run(args,stdout=out,stderr=err,timeout=30)
  else:
   with Path(stdout).open('ab') as out:r=subprocess.run(args,stdout=out,stderr=err,timeout=30)
 return dict(returncode=r.returncode,stderr=str(L/(name+'.stderr')))
cmd=lambda file,*args:[PY,'-I','-s','-B',str(W/'runner.py'),str(K/'b'/file),*map(str,args)]
c=pc.Copier(K,N,'24004',writer=W/'fake_gc_run.py')
record('baseline_small',lambda:c.small())
# Independently running trainer: it writes only node-local state, not stdout.
trainer=W/'trainer.py';trainer.write_text("from pathlib import Path\nimport sys,time\np=Path(sys.argv[1])\nfor i in range(150):\n with (p/'steps.local').open('a') as f:f.write(str(i)+'\\n')\n if i==8:(p/'checkpoint.local').write_bytes(b'q'*4096)\n time.sleep(.1)\n")
trainerlog=(L/'trainer.log').open('wb');train=subprocess.Popen([PY,'-I','-s','-B',str(trainer),str(N)],stdout=trainerlog,stderr=trainerlog)
# Fill by dd, retaining its output and explicit df result. Recovery grows the mount, no deletion.
with (L/'fill.log').open('wb') as f:
 r=subprocess.run(['dd','if=/dev/zero','of='+str(X/'fill'),'bs=1M','count=64'],stdout=f,stderr=f)
 subprocess.run(['df','-B1',str(X)],stdout=f,stderr=f)
assert shutil.disk_usage(X).free==0
record('full_small',lambda:c.small())
record('full_loop_small',lambda:cli('full_loop_small',cmd('pc.py',K,N,'24004','--loop-small')))
record('full_loop',lambda:cli('full_loop',cmd('pc.py',K,N,'24004','--loop')))
record('full_export',lambda:c.send(T/'m100',T/'m100/artifact.json',['m100']))
record('full_stop',lambda:c.stop_checkpoint())
record('full_final',lambda:cli('full_final',cmd('pc.py',K,N,'24004','--final')))
# Preexisting claim permits upload but the project done marker still fails.
# Preallocate claim before fill in a separate phase below; direct gc now proves transport is local.
priv=N/'direct';priv.mkdir();ss=priv/'sess.json';ss.write_text(json.dumps(sessions))
record('full_gc_direct',lambda:cli('full_gc_direct',[PY,'-I','-s','-B',str(W/'fake_gc_run.py'),'split',str(ss),names['m100'],str(c.archive(T/'m100',T/'m100/artifact.json')),'4','4']))
for filename in ('v.json','h0.json','c0.json','c1.json','c2.json','c3.json','c4.json','s0.json','s1.json'):
 record('receipt_'+filename.replace('.','_'),lambda filename=filename:rv.put(c.live/filename,b'{"q":1}\n'))
# Replay the precise sealed publication statements, without evaluating unrelated training preparation.
def site(file,start,end,env):
 tree=ast.parse((K/'b'/file).read_text());nodes=[n for n in ast.walk(tree) if isinstance(n,ast.Expr) and start<=n.lineno<=end]
 exec(compile(ast.Module(body=sorted(nodes,key=lambda n:n.lineno),type_ignores=[]),str(K/'b'/file),'exec'),env)
scene=N/'scene';scene.mkdir();(scene/'2.json').write_text('{}\n');(scene/'0.json').write_text('{}\n');(N/'hr.json').write_text('{}\n')
record('full_pl_sites',lambda:site('pl.py',255,256,dict(put=rv.put,live=c.live,scene=scene)))
record('full_h_site',lambda:site('h.py',39,39,dict(put=rv.put,live=c.live,r=N)))
# Real review control flow; synthetic identity/evidence avoids GPU/data dependencies.
carrier=types.ModuleType('student_pilot.carrier_c1_run');carrier.identity=lambda cfg:'q'*40
parent=types.ModuleType('student_pilot');parent.__path__=[];sys.modules['student_pilot']=parent;sys.modules['student_pilot.carrier_c1_run']=carrier
cfg=N/'v.json';cfg.write_text('{"r1_training":{}}\n');rv.evidence=lambda *a:None
record('full_rv_run',lambda:rv.run(K,N,cfg,'24004',interval=.05))
record('full_review_missing',lambda:rv.receipt_bytes(X/'n_r/review.json'))
# stdout: sufficient sustained output ensures l.py's failure reaches the writer pipe.
child=W/'printing.py';child.write_text("import sys,time\nfrom pathlib import Path\np=Path(sys.argv[1])\nfor i in range(10000):\n with p.open('a') as f:f.write(str(i)+'\\n')\n print('q'*1024,flush=True)\n")
record('full_direct_print',lambda:cli('full_direct_print',[PY,'-I','-s','-B',str(child),str(N/'direct.steps')],X/'j/direct.log'))
def pipeline():
 with (X/'j/pipe.log').open('ab') as out,(L/'pipeline.stderr').open('wb') as err:
  p1=subprocess.Popen([PY,'-I','-s','-B',str(child),str(N/'pipe.steps')],stdout=subprocess.PIPE,stderr=err)
  p2=subprocess.Popen(cmd('l.py',K),stdin=p1.stdout,stdout=out,stderr=err);p1.stdout.close()
  return dict(child_rc=p1.wait(timeout=15),logger_rc=p2.wait(timeout=15),steps=len((N/'pipe.steps').read_text().splitlines()))
record('full_pipeline',pipeline)
record('full_exit_archive',lambda:cli('full_exit_archive',cmd('o.py',N,0,0)))
record('full_ep',lambda:cli('full_ep',cmd('ep.py',K,N,'24004',0)))
# Use the actual EXIT/TERM/USR1 traps; no TK_WORK_PID is set in these focused finalizer tests.
for mode in ('EXIT','TERM','USR1'):
 shell='set -euo pipefail; ROOT="$TEST_W/kit"; N="$TEST_W/node"; source "$ROOT/b/pc.sh"; '
 shell += 'exit 0' if mode=='EXIT' else 'kill -'+mode+' $$'
 record('trap_'+mode.lower(),lambda shell=shell,mode=mode:cli('trap_'+mode.lower(),['bash','-c',shell]))
record('trainer_full_progress',lambda:dict(alive=train.poll() is None,steps=len((N/'steps.local').read_text().splitlines()),checkpoint=(N/'checkpoint.local').is_file(),sink_files=len(list((W/'sink').glob('*')))))
# No deletion: increasing tmpfs capacity makes free blocks available.
with (L/'recovery.log').open('wb') as f:
 subprocess.run(['mount','-o','remount,size=64m',str(X)],check=True,stdout=f,stderr=f)
 subprocess.run(['df','-B1',str(X)],stdout=f,stderr=f)
record('recovered_small_manual',lambda:c.small())
record('recovered_export_manual',lambda:c.send(T/'m100',T/'m100/artifact.json',['m100']))
record('recovered_stop_manual',lambda:c.stop_checkpoint())
record('recovered_archive_manual',lambda:cli('recovered_archive_manual',cmd('o.py',N,0,0)))
record('trainer_complete',lambda:dict(returncode=train.wait(timeout=30),steps=len((N/'steps.local').read_text().splitlines()),checkpoint=(N/'checkpoint.local').is_file()))
(W/'results.json').write_text(json.dumps(results,indent=2)+'\n')
# Preserve only small published files, never filler.
shutil.copytree(X/'o',W/'published_after_recovery')
