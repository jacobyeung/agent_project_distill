"""Check launch wiring and read-only reuse without starting training or sockets."""
from pathlib import Path
import ast, json, subprocess, sys
D=Path(__file__).resolve().parent;L=D.parents[1];R=D/'rehearsal5'
sys.path.insert(0,str(D))
from rehearsal_copier5 import read,sha,put,module_path
sys.path.insert(0,str(L/'work/build24'))
import joblib as J
prepared=read(R/'PREPARED.json');kit=Path(prepared['kit_dir'])
assert J.seal(kit)==prepared['kit']
start=read(R/'PREPARATION_STARTED.json');assert start['kit_seal']==prepared['kit']
assert start['build24k_present_at_preparation'] is True
synthetic=read(R/'copier_synthetic/RESULT.json')
assert synthetic['status']=='PASS' and synthetic['pass_once_calls']==1
module,_=module_path(kit)
assert synthetic['source']['module']==str(module)
assert synthetic['source']['module_sha256']==sha(module)
assert synthetic['source']['kit_seal']==prepared['kit']
files=['rehearsal_copier5.py','check_rehearsal_copier5.py','make_rehearsal5.py',
       'rehearsal_runner5.py','rehearsal_boundary5.py','rehearsal_cpu_python5',
       'rehearsal_repro5.py','check_rehearsal5.py','check_rehearsal_setup5.py']
for name in files: ast.parse((D/name).read_text(),filename=name)
subprocess.run(['bash','-n',str(D/'go_rehearsal5.sh')],check=True)
assert (D/'rehearsal_cpu_python5').stat().st_mode & 0o111
args=read(R/'VIEW.json')
writable=[(args[i+1],args[i+2]) for i,x in enumerate(args) if x=='--bind']
assert writable==[(str(R),str(R)),(str(R),'/tmp/q_22c714e1')]
readonly=[(args[i+1],args[i+2]) for i,x in enumerate(args) if x=='--ro-bind']
assert (str(D/'rehearsal4'),str(D/'rehearsal4')) in readonly
assert (str(R/'p2/s'),str(L/'work/tree_r1')) in readonly
assert (str(kit),str(kit)) in readonly
assert not (R/'RUN_STARTED.json').exists()
size=sum(p.stat().st_size for p in R.rglob('*') if p.is_file() and not p.is_symlink())
assert size < 1_000_000_000
put(R/'SETUP_VALIDATION.json',dict(status='PASS',kit=str(kit),kit_seal=prepared['kit'],source_tree=prepared['tree'],
    copier=str(module),module_sha256=sha(module),synthetic_done=synthetic['done'],
    syntax_files=files+['go_rehearsal5.sh'],writable_binds=writable,generated_bytes=size,
    training_executed=False,training_skip='BUILD24K_REPORT.md was present at initial build24fr4 check',
    native_preparation=True,host_receipt='CPU frame-host stand-in; unmodified kit h.py consumes it'))
print('PASS: kit pins, synthetic copier evidence, launch syntax, read-only reuse, and disk bound; no training started')
