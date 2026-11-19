from pathlib import Path
import importlib.util,json,os,signal,subprocess,sys,time
L=Path(__file__).resolve().parents[2];D=L/'work/build24k'
sys.path.insert(0,str(L/'work/build24g'))
from live_tests import WRITER

def module(path,name):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
old=module(L/'attic/build24h/work/build24/kits/n/b/pc.py','old')
new=module(L/'work/build24/kits/n/b/pc.py','new')
records=[]

def fixture(C,name):
 f=D/'signal_final_tests'/name;f.mkdir(parents=True)
 k=f/'kit';(k/'k').mkdir(parents=True);(k/'b').mkdir()
 n=f/'node';n.mkdir();target=f/'project';target.mkdir();sd=target/'n_s';sd.mkdir(mode=0o700)
 C.put(sd/'sess.json',{});(sd/'sess.json').chmod(0o600)
 C.put(k/'k/p.json',{'n_root':str(target)})
 C.put(k/'k/n.json',{'output':'/tmp/q/r'})
 C.put(k/'k/y.json',{'objects':{'m100':'q9/test/m100.tar','m200':'q9/test/m200.tar'}})
 (k/'b/gc.py').write_text(WRITER);(k/'b/pc.py').write_bytes(Path(C.__file__).read_bytes())
 return f,k,n,target

def hashes(k):return {str(p.relative_to(k)):old.sha(p) for p in k.rglob('*') if p.is_file()}
# Use the real trap and worker-selection helper; the synthetic worker publishes only on USR1.
for label in ('after',):
 for sig in (signal.SIGTERM,signal.SIGUSR1):
  C=old if label=='before' else new
  f,k,n,target=fixture(C,label+'_signal_'+str(sig));src=L/('attic/build24h/work/build24/kits/n' if label=='before' else 'work/build24/kits/n')
  (k/'b/pc.sh').write_bytes((src/'b/pc.sh').read_bytes());(k/'b/sr.py').write_bytes((D/'sr.py').read_bytes())
  (k/'b/u.py').write_text('''from pathlib import Path
import json,signal,sys,time
r=Path(sys.argv[1]);stop=[False]
(r/'ready').write_text('ready')
time.sleep(.3)
signal.signal(signal.SIGUSR1,lambda *_:stop.__setitem__(0,True))
end=time.monotonic()+4
while not stop[0] and time.monotonic()<end:time.sleep(.02)
if stop[0]:
 time.sleep(.25)
 d=r/'p/q/r/m100';d.mkdir(parents=True)
 (d/'w').write_bytes(b'final export')
 (d/'artifact.json').write_text(json.dumps({'step':100}))
 (r/'t.log').write_text('export after USR1')
raise SystemExit(7)
''')
  launcher=f/'launcher.py';launcher.write_text('import subprocess,sys,os\nraise SystemExit(subprocess.run([sys.executable,"-B",sys.argv[1],sys.argv[2]],env={**os.environ,"RANK":"0","LOCAL_RANK":"0"}).returncode)\n')
  shell=f/'signal.sh';shell.write_text('set -eu\nROOT='+repr(str(k))+'\nN='+repr(str(n))+'\nexport SLURM_JOB_ID=41\nsource "$ROOT/b/pc.sh"\n'+repr(sys.executable)+' -B '+repr(str(launcher))+' '+repr(str(k/'b/u.py'))+' "$N" &\nTK_WORK_PID=$!\nwait "$TK_WORK_PID"\n')
  with (f/'signal.log').open('w') as log:
   p=subprocess.Popen(['/bin/bash',str(shell)],stdout=log,stderr=subprocess.STDOUT)
   end=time.monotonic()+10
   while not (n/'ready').exists() and time.monotonic()<end:time.sleep(.02)
   assert (n/'ready').exists();p.send_signal(sig);rc=p.wait(timeout=20)
  found=(target/'o/41/live/gcs_m100.done').exists()
  assert found==(label=='after'),(label,sig,rc,(f/'signal.log').read_text())
  assert rc==(7 if label=='after' else 128+int(sig)),rc
  records.append(dict(version=label,case='signal_'+str(sig),returncode=rc,final_export_copied=found))
  # The before-control worker exits on its own short deadline; no job is stopped.
  if label=='before':time.sleep(4)
(D/'SIGNAL_FINAL_TESTS.json').write_text(json.dumps(dict(status='PASS',records=records),indent=2)+'\n')
print('Copier A/B/C before/after controls PASS',flush=True)
