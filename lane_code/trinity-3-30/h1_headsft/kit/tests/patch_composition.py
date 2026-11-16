"""Build plain patches and prove both compositions against the sealed file bytes."""
import difflib
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile

K=Path(__file__).resolve().parents[1]
BASE=Path('/scratch/jjyeung/orch_n30/tree_rebuild/work/base/tree_b01ce449')
files=['student_pilot/'+name for name in ('carrier_c1.py','carrier_c1_run.py','carrier_c1_routing.py','h1.py','h1_faithful.py','h1_r0.py')]
copy_pins={v['destination'].removeprefix('tree/'):v['sha256'] for v in json.loads((K/'COPY_MANIFEST.json').read_text())}
base={};full={}
for name in files:
    path=BASE/name
    base[name]=path.read_text() if name in copy_pins else ''
    if name in copy_pins:assert hashlib.sha256(path.read_bytes()).hexdigest()==copy_pins[name],name
    full[name]=(K/'tree'/name).read_text()
faithful=dict(base)
faithful['student_pilot/h1_faithful.py']=full['student_pilot/h1_faithful.py']
faithful['student_pilot/carrier_c1_routing.py']=full['student_pilot/carrier_c1_routing.py']
changes=[
("    self.processor = processor\n", "    self.processor = processor\n        self.h1 = receipt.get('h1', {})\n"),
("'tool_mode_flag', 'ground_target_filter', 's1_route_policy') if k in cfg", "'tool_mode_flag', 'ground_target_filter', 's1_route_policy', 'h1') if k in cfg"),
("    if cfg.get('geometry_online'):\n        receipt = {**receipt", "    if 'h1' in cfg:\n        receipt = {**receipt, 'h1': cfg['h1']}\n    if cfg.get('geometry_online'):\n        receipt = {**receipt"),
("    if not any(decision):\n", "    if getattr(rows, 'h1', {}).get('faithful_own_camera_rows'):\n        from .h1_faithful import own_values as faithful_own_values\n        return faithful_own_values(model, rows, batch, audit, index, decision, device)\n    if not any(decision):\n"),
("\n\ndef warn(cfg, message):", "\n    if cfg.get('h1', {}).get('faithful_own_camera_rows') is not None:\n        from .h1_faithful import validate as validate_faithful\n        validate_faithful(cfg)\n\n\ndef warn(cfg, message):"),
]
key='student_pilot/carrier_c1_run.py'
rest=dict(full)
rest['student_pilot/h1_faithful.py']=''
rest['student_pilot/carrier_c1_routing.py']=base['student_pilot/carrier_c1_routing.py']
for old,new in changes:
    assert faithful[key].count(old)==1,(old,faithful[key].count(old))
    faithful[key]=faithful[key].replace(old,new)
    assert rest[key].count(new)==1,(new,rest[key].count(new))
    rest[key]=rest[key].replace(new,old)

def diff(after):
    result=[]
    for name in files:
        if base[name]!=after[name]:
            result.extend(difflib.unified_diff(base[name].splitlines(True),after[name].splitlines(True),
                          fromfile='a/'+name if base[name] else '/dev/null',tofile='b/'+name,n=3))
    return ''.join(result)

for name,content in [('faithful_own_rows.patch',faithful),('h1_rest.patch',rest),('h1_trainer.patch',full)]:
    (K/'patches'/name).write_text(diff(content))
root=Path(tempfile.mkdtemp(prefix='patch_proof_',dir=K/'tmp'))
results=[]
for label,patches in [('faithful_then_rest',['faithful_own_rows.patch','h1_rest.patch']),
                      ('rest_then_faithful',['h1_rest.patch','faithful_own_rows.patch']),('full',['h1_trainer.patch'])]:
    target=root/label;target.mkdir()
    for name,text in base.items():
        if text:
            p=target/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text)
    for patch in patches:
        run=subprocess.run(['patch','--batch','--fuzz=0','--no-backup-if-mismatch','-p1','-i',str(K/'patches'/patch)],cwd=target,text=True,capture_output=True)
        print(label,patch,run.stdout,run.stderr)
        assert run.returncode==0
    for name,text in full.items():assert (target/name).read_text()==text,(label,name)
    results.append(dict(order=label,files_identical=len(files),pass_count=1))
# Retain a standalone S1 overlay for tests, with unmodified modules resolved from the sealed tree.
target=root/'faithful_only';target.mkdir()
for name,text in faithful.items():
    if text:
        p=target/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text)
(target/'student_pilot/__init__.py').write_text('__path__.append('+repr(str(BASE/'student_pilot'))+')\n')
report=dict(pass_count=3,root=str(root),results=results,baseline={k:copy_pins[k] for k in files if k in copy_pins},faithful_only=str(target))
(K/'logs/patch_composition.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report))
