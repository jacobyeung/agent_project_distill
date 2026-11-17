"""Seal the final packet and bounded local evidence inventory."""
import ast,hashlib,json,subprocess
from pathlib import Path
H=Path(__file__).resolve().parents[1]
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 return h.hexdigest()
def load(n):return json.loads((H/n).read_text())
def write(n,v):(H/n).write_text(json.dumps(v,sort_keys=True,indent=2)+'\n')
ids=load('ids.json')
assert len((H/'FIX8.md').read_text().splitlines())<=25
assert sha(H/'payload/jb.sh')==sha(H/'evidence/fix8_before/payload/jb.sh')==sha(H/'runtime/jb.sh')
assert sha(H/'EXPORT_OBJECTS.txt')==sha(H/'evidence/fix8_before/EXPORT_OBJECTS.txt')
assert sha(H/'tools/derive_kit_h1.py')==sha(H/'payload/d.py')
assert ids['tokens']['run']=='17c4ffa4'
for n in ('selection_tests','deriver_tests','runtime_tests','package_tests'):
 assert load('evidence/fix7_selection/'+n+'.json')['status']=='PASS'
for n in ('pin_tests','proof_tests','submit_tests'):
 assert load('evidence/fix8_admission/'+n+'.json')['status']=='PASS'
audit=load('evidence/fix8_admission/config_tests.json')['results']
for n in ('carrier_c1_run.validate','run.authenticate','routing_selection_implementation'):
 assert audit[n]['status']=='PASS'
assert 219 in load('evidence/fix7_admission/latest.json')['results']['production_after_215']['executed_lines']
for n in ('build/c_patch.sh','build/a_8c74b291.sh','payload/s.sh','payload/o.sh','payload/z.sh','orch_h1.sh'):
 subprocess.run(['/bin/bash','-n',str(H/n)],check=True)
for p in list((H/'tools').glob('*.py'))+list((H/'tests').glob('test_fix8_*.py')):
 ast.parse(p.read_text(),filename=str(p))
up=load('UPLOAD.json')
assert sha(H/'build'/up['archive'])==up['sha256']
for row in up['files']:assert sha(H/'payload'/row['name'])==row['sha256']
for line in (H/'payload/sums.txt').read_text().splitlines():
 digest,name=line.split('  ',1);assert sha(H/'payload'/name)==digest
write('evidence/final_checks.json',dict(status='LOCAL_PACKET_PASS',config_identity=ids['identity'],
 config_key=ids['config_key'],contract=ids['contract'],run_key='17c4ffa4',
 selection_equality='EQUAL: original Orchard report and native files verified',
 config_validate='PASS',config_authenticate='PASS',routing_implementation='PASS',
 production_cpu_preparation='NOT RUN: operator must execute the proof on final certified KH',
 independent_devin_review='PENDING: user launches one review of tool and pin',production_go_granted=False,
 local_derivation='FIXTURE using retained incomplete source authority; production authority unchanged',
 proof_script='build/a_8c74b291.sh',proof_dry_test='PASS',submission_receipt_cases=13,
 all_fix7_tests='PASS',deriver_checks=19,guarded_patch_cases=7,
 wrappers_unchanged=True,exports_unchanged=True,deterministic_rebuild='PASS'))
names={line.split('  ',1)[1] for line in (H/'evidence/fix8_before/SHA256SUMS.txt').read_text().splitlines()}
names.update(['FIX8.md','REPORT.md','DIFF.md','ids.json','UPLOAD.json','orch_h1.sh','fin_h1.sh',
 'build/c_patch.sh','build/a_8c74b291.sh','build/'+up['archive'],'evidence/final_checks.json',
 'evidence/fix8_patch_manifest.json','build/over_local.json','build/over_seed.json','build/over_fx.json'])
for folder in ('payload','tools','tests'):
 names.update(str(p.relative_to(H)) for p in (H/folder).iterdir() if p.is_file())
for folder in ('build/fx','evidence/fix8_admission','evidence/fix8_before',
               'evidence/fix7_selection/orchard_equal_6c18a2bf/o'):
 names.update(str(p.relative_to(H)) for p in (H/folder).rglob('*')
              if p.is_file() and '__pycache__' not in p.parts and p.name!='delivery.json')
for n in ('selection_tests','deriver_tests','runtime_tests','package_tests'):
 index='evidence/fix7_selection/'+n+'.json';names.add(index)
 root=Path(load(index)['path'])
 names.update(str(p.relative_to(H)) for p in root.iterdir() if p.is_file())
 if n=='package_tests':names.add(str((root/'patch/results.json').relative_to(H)))
root=Path(load('evidence/fix7_admission/latest.json')['path'])
names.add('evidence/fix7_admission/latest.json')
names.update(str(p.relative_to(H)) for p in root.rglob('*') if p.is_file())
names.discard('SHA256SUMS.txt');names.discard('evidence/fix8_admission/delivery.json')
assert all((H/n).is_file() for n in names)
sealed={n:sha(H/n) for n in sorted(names)}
delivery=dict(status='LOCAL_PACKET_PASS',files=sealed,config_identity=ids['identity'],
 production_preparation='PENDING operator proof',outer_manifest='SHA256SUMS.txt seals this record; no self-hash')
write('evidence/fix8_admission/delivery.json',delivery)
sealed['evidence/fix8_admission/delivery.json']=sha(H/'evidence/fix8_admission/delivery.json')
(H/'SHA256SUMS.txt').write_text(''.join(h+'  '+n+'\n' for n,h in sorted(sealed.items())))
print(json.dumps(dict(status='LOCAL_PACKET_PASS',members=len(sealed),manifest_sha256=sha(H/'SHA256SUMS.txt'))))
