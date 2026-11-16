"""Produce a complete line-classified review against the authenticated source package."""
import ast
import difflib
import hashlib
import json
from pathlib import Path
import tarfile
ROOT=Path(__file__).resolve().parent
SOURCE=Path('/scratch/jjyeung/orch_n30/evalx27/work/kit_revsi/package.tar')
EXPECTED='ea1a1b2d5b965017f7cacce9c02c13cbbe5522d87be8cc55ab755176ecd55d3b'
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()==EXPECTED
with tarfile.open(SOURCE) as archive:
    baseline={m.name:archive.extractfile(m).read() for m in archive}
added=['launcher/export_stage.py','launcher/opaque_io.py','tests/offline_guard.py',
       'reader/work/vendor/r3/c0.json','reader/work/vendor/r3/c1.json']
files={name:(ROOT/'kit'/name).read_bytes() for name in [*baseline,*added]}
local=[p for p in ROOT.glob('*.py')]+list((ROOT/'tests').glob('*.py'))+[ROOT/n for n in ('REPORT.md','REVIEW.md','LEDGER.jsonl')]
classes={
 'launcher/orchard_launcher.py':'BEYOND', 'launcher/orchard_stage.py':'PATH/ENV',
 'launcher/export_stage.py':'PATH/ENV', 'launcher/MODELS.json':'PATH/ENV',
 'launcher/TRANSPORT.json':'PATH/ENV', 'reader/official_adapter.py':'PATH/ENV',
 'reader/chain.py':'PATH/ENV','parity/prove_prompts.py':'PATH/ENV',
 'launcher/orchard_job.py':'BEYOND','launcher/return_io.py':'BEYOND',
 'launcher/orchard_results.py':'PATH/ENV','launcher/trace_runtime.py':'PATH/ENV',
 'launcher/opaque_io.py':'PATH/ENV','reader/work/vendor/r3/adapter.py':'PATH/ENV',
 'reader/work/vendor/r3/PINS.json':'PATH/ENV','reader/work/vendor/r5/adapter.py':'PATH/ENV',
 'reader/work/vendor/r3/c0.json':'PATH/ENV','reader/work/vendor/r3/c1.json':'PATH/ENV'}
lines=['Comparison base: `'+EXPECTED+'` (`package.tar`, 125 regular members).',
       '', 'Scope: kit source members, new analysis/test/build tools, reports, and the local ledger. Generated evidence and DIFF.md itself are BEYOND artifacts, not recursive diff inputs. Every added or removed line below has one classification. PATH/ENV covers checkpoint paths, step binding, names, transport, and diagnostic encoding. BEYOND covers deadlines, retaining write-test evidence, analysis, documentation, and offline validation. Unchanged lines appear only as diff context.', '']
changed=[]
for name,raw in sorted(files.items()):
    old=baseline.get(name,b'')
    if old==raw:continue
    kind=classes.get(name,'BEYOND');changed.append(dict(file='kit/'+name,classification=kind,old_sha256=hashlib.sha256(old).hexdigest() if old else None,sha256=hashlib.sha256(raw).hexdigest()))
    lines+=['### kit/'+name+' — '+kind,'','```diff']
    for line in difflib.unified_diff(old.decode().splitlines(),raw.decode().splitlines(),fromfile='ea1a1b2d/'+name,tofile='kit/'+name,lineterm=''):
        lines.append(('['+kind+'] ' if line[:1] in '+-' and not line.startswith(('+++','---')) else '')+line)
    lines+=['```','']
for p in sorted(local):
    name=str(p.relative_to(ROOT));raw=p.read_bytes();changed.append(dict(file=name,classification='BEYOND',old_sha256=None,sha256=hashlib.sha256(raw).hexdigest()))
    lines+=['### '+name+' — BEYOND (new local file)','','```diff']
    lines+=['[BEYOND] +'+line for line in raw.decode().splitlines()];lines+=['```','']
(ROOT/'DIFF.md').write_text('\n'.join(lines)+'\n')
unchanged=[n for n in baseline if files[n]==baseline[n]]
required=[n for n in baseline if n.startswith(('reader/evaluator/','inputs/','cohort/'))]+['reader/official_score.py','reader/out/export_check.py','reader/out/common.py']
assert all(n in unchanged for n in required)
pins={'kit/'+n:hashlib.sha256(raw).hexdigest() for n,raw in files.items()}
pins.update({str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in local})
(ROOT/'evidence/FINAL_PINS.json').write_text(json.dumps(pins,indent=2,sort_keys=True)+'\n')
(ROOT/'evidence/CHANGE_MANIFEST.json').write_text(json.dumps(dict(base=EXPECTED,changed=changed,unchanged=unchanged,protocol_byte_identical=required),indent=2)+'\n')
# Verify the imported admission body remains identical to both reviewed sources.
def function(path,name):
    tree=ast.parse(Path(path).read_text())
    return ast.dump(next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name==name),include_attributes=False)
ref='/scratch/jjyeung/orch_n30/cont_ops/work/d0/readk/kit/launcher/export_stage.py'
assert function(ref,'stage_export')==function(ROOT/'kit/launcher/export_stage.py','stage_export')
assert function(ref,'parse_done')==function(ROOT/'kit/launcher/export_stage.py','parse_done')
compiled=0
for name in pins:
    if name.endswith('.py'):compile((ROOT/name).read_text(),name,'exec');compiled+=1
print(json.dumps(dict(base=EXPECTED,unchanged_members=len(unchanged),changed_members=len(baseline)-len(unchanged),added_kit_members=len(added),protocol_files_unchanged=len(required),compiled_python_files=compiled)))
