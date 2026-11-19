from common import *
import subprocess,shutil,time,signal,importlib.util
F=D/'publication';F.mkdir();records=[]
for name in ('q','n','n_go','qd'):
 root=F/name;root.mkdir();k=root/'kit'
 def transport(a,b):
  if Path(a).name in ('p.json','ep.py','BUILD.json','SHA256SUMS.txt'):return shutil.copyfile(a,b)
  os.link(a,b);return b
 shutil.copytree(kit(name),k,copy_function=transport)
 target=root/'target';node=root/'node';node.mkdir()
 spec=J.load(k/'k/p.json');spec['n_root']=str(target);cap(k,'k/p.json',spec)
 # The test shortens only the period; the shipped copier remains 600 seconds.
 p=k/'b/ep.py';s=p.read_text();assert 'time.sleep(600)' in s;p.write_text(s.replace('time.sleep(600)','time.sleep(.1)'));reseal(k)
 for log in ('q.log','rooms.log','h.log','rv.log','t.log'):(node/log).write_text('safe diagnostic '+log+'\n')
 (node/'94.steps').write_text('stage completed\n')
 J.write(node/'p/r0.json',dict(status='REFUSE',refusal='R1_FIXTURE_FAILURE'))
 J.write(node/'p/q/RESULT.json',dict(status='REFUSE',refusal='R1_FIXTURE_FAILURE'))
 J.write(node/'o/RESULT.json',dict(proof_rc=7,GO=False,discovery=name=='qd'))
 selected=J.write(node/'routing_selection.json',dict(regenerated_sha256='1'*64))
 base=node/('dr/p/q/selection' if name=='qd' else 'p/q/selection')
 artifacts={n:J.write(base/n,dict(schema=n,synthetic=True)) for n in ('receipt.json','materialization.json')}
 args=[sys.executable,'-B','-I','-s',str(k/'b/ep.py'),str(k),str(node),'94','7']
 result=subprocess.run(args,check=True,capture_output=True,text=True)
 out=target/'o/94';v=J.load(out/'r1.json')
 assert v['returncode']==7
 assert all((out/x).is_file() for x in ('q.log','rooms.log','h.log','rv.log','t.log','q.steps','q0.json','r0.json','RESULT.json'))
 for n,pin in artifacts.items():
  assert J.sha(out/n)==pin['sha256'] and pin['sha256'] in result.stdout
 assert sum(p.stat().st_size for p in out.iterdir() if p.is_file())<5_000_000
 # Concurrent periodic/final copies share a lock, including routing artifacts.
 children=[subprocess.Popen(args,stdout=subprocess.PIPE,stderr=subprocess.PIPE) for _ in range(2)]
 for child in children:
  stdout,stderr=child.communicate();assert child.returncode==0,stderr
 # Exercise the actual EXIT and TERM trap with the production loop body.
 for kind in ('exit','term'):
  job='95' if kind=='exit' else '96';shell=root/(kind+'.sh')
  shell.write_text('set -euo pipefail\nROOT='+repr(str(k))+'\nN='+repr(str(node))+'\nexport SLURM_JOB_ID='+job+'\nsource "$ROOT/b/ep.sh"\n'+
   ('sleep .3\nexit 9\n' if kind=='exit' else 'setsid sleep 30 &\nTK_WORK_PID=$!\nwait "$TK_WORK_PID"\n'))
  env={**os.environ,'PATH':str(Path(sys.executable).parent)+':'+os.environ['PATH']}
  with (root/(kind+'.log')).open('w') as f:
   proc=subprocess.Popen(['/bin/bash',str(shell)],stdout=f,stderr=subprocess.STDOUT,env=env)
   deadline=time.monotonic()+20
   while not (target/'o'/job/'r1.json').exists():
    assert time.monotonic()<deadline and proc.poll() is None,(name,kind)
    time.sleep(.05)
   (node/'q.log').write_text('final '+kind+'\n')
   if kind=='term':proc.send_signal(signal.SIGTERM)
   rc=proc.wait(timeout=20)
  assert rc==(143 if kind=='term' else 9),(name,kind,rc)
  value=J.load(target/'o'/job/'r1.json');assert value['returncode']==rc
  assert (target/'o'/job/'q.log').read_text()=='final '+kind+'\n'
  assert sum(p.stat().st_size for p in (target/'o'/job).iterdir() if p.is_file())<5_000_000
 records.append(dict(kit=name,loop=True,exit=True,term=True,artifacts=True,concurrent=True,sha256_logged=True))
J.write(D/'PUBLICATION_TESTS.json',dict(status='PASS',records=records,period_seconds=600,test_period_seconds=.1,under_5_MB=True))
print('four kits: screened logs, routing artifacts, loop, EXIT, TERM and concurrent copies PASS')
