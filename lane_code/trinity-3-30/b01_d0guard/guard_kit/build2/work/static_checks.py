from pathlib import Path
import ast,importlib.util,json,subprocess,sys
B=Path(__file__).resolve().parents[1];K=B/'out/guard_kit'
sys.path.insert(0,str(K));from guard_core import read,write,sha
checked=[]
for root in [K,B/'out/rehearsal',B/'out/tests']:
 for p in sorted(root.rglob('*.py')):
  if 'mutants' in p.parts:continue
  compile(p.read_text(),str(p),'exec');checked.append(str(p))
subprocess.run(['/bin/bash','-n',str(B/'out/rehearsal/run_whole_worker.sh')],check=True)
p=read(B/'out/PACKET_TEST.json');batch=Path(p['packet'])/'BATCH.sh'
subprocess.run(['/bin/bash','-n',str(batch)],check=True)
source=batch.read_text().split("<<'G2_PY'\n",1)[1].rsplit('\nG2_PY',1)[0]
compile(source,str(batch),'exec')
spec=importlib.util.spec_from_file_location('whole',B/'out/rehearsal/run_whole_worker.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
root=B/'out/rehearsal/whole/sandbox';args=m.namespace(root,root/'fixture');missing=[]
for n,a in enumerate(args):
 if a in ('--ro-bind','--bind') and not Path(args[n+1]).exists():missing.append(args[n+1])
write(B/'out/SYNTAX.json',dict(status='PASS',python_files=len(checked),files=checked,batch=str(batch),batch_sha256=sha(batch)))
write(B/'out/rehearsal/whole/INPUT_PATHS.json',dict(status='PASS' if not missing else 'FAIL',missing=missing,namespace_not_executed=True))
if missing:raise ValueError(missing)
