"""Seal changed outputs and current evidence without rescanning historical trees."""
import ast,hashlib,json,subprocess
from pathlib import Path
H=Path(__file__).resolve().parents[1]
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 return h.hexdigest()
def load(n):return json.loads((H/n).read_text())
def write(n,v):(H/n).write_text(json.dumps(v,indent=2,sort_keys=True)+'\n')
for n in ('selection_tests','deriver_tests','package_tests'):
 assert load('evidence/fix7_selection/'+n+'.json')['status']=='PASS'
assert load('evidence/fix7_selection/selection_tests.json')['tool_sha256']==sha(H/'tools/selection_check.py')
audit=load('evidence/fix7_admission/latest.json')['results']
assert 219 in audit['production_after_215']['executed_lines']
assert audit['synthetic_build']['status']=='PASS' and audit['synthetic_build']['count']==2
assert load('evidence/fix7_selection/production_attempt/q.json')['status']=='BLOCKED'
assert not (H/'evidence/fix7_selection/production_attempt/r.json').exists()
assert sha(H/'payload/d.py')==sha(H/'tools/derive_kit_h1.py')
assert sha(H/'payload/d_f232d4160d75b582.json')=='f232d4160d75b5826d9e24aec324d690920a752a5bfaa33e5009d7550349dfc6'
assert load('payload/over.json')['status']=='BLOCKED'
assert load('payload/4.json')['production_go_granted'] is False
assert len((H/'FIX7.md').read_text().splitlines())<=25
for n in ['build/q.sh','build/c_patch.sh','payload/g.sh','payload/o.sh','payload/z.sh','payload/s.sh']:
 subprocess.run(['bash','-n',str(H/n)],check=True)
# Rebuild the new generators once and verify determinism against the published bytes.
before={n:sha(H/n) for n in ['tools/derive_kit_h1.py','payload/d.py','build/q.sh']}
for tool in ['make_deriver.py','package_selection.py']:
 subprocess.run(['/scratch/jjyeung/envs/p1cpu/bin/python','-B',str(H/'tools'/tool)],check=True,capture_output=True)
assert all(sha(H/n)==v for n,v in before.items())
for d in ('tools','tests','payload'):
 for p in (H/d).glob('*.py'):ast.parse(p.read_text(),filename=str(p))
up=load('UPLOAD.json')
for row in up['files']:
 assert 'TEST_ONLY' not in row['name'] and row['name'] not in ('r.json','q.json','selection_equality.json')
 assert sha(H/'payload'/row['name'])==row['sha256']
assert sha(H/'build'/up['archive'])==up['sha256']
summary=dict(status='BLOCKED',fix_status='PASS',production_equality='NOT VERIFIED: 13 missing local gzip files',
 production_replacement_emitted=False,production_go_granted=False,regeneration_package='build/q.sh',
 tests=dict(native_regeneration='PASS with synthetic inputs',deriver_checks=19,full_fixture_derivation='PASS',
 native_routing_build='PASS with synthetic rows',post_215='Reached 219; real legacy receipt missing',
 package='PASS',guarded_patch_cases=7,existing_gate_binding='PASS'),
 limits=audit['not_tested']['checks'],identity=load('ids.json')['identity'])
write('evidence/final_checks.json',summary)
files=['FIX7.md','REPORT.md','DIFF.md','build/q.sh','build/c_patch.sh','payload/d.py','payload/sums.txt',
 'UPLOAD.json','orch_h1.sh','fin_h1.sh','build/'+up['archive'],'tools/selection_check.py','tools/selection_guard.py',
 'tools/make_deriver.py','tools/derive_kit_h1.py','tools/package_selection.py','tools/inventory_selection.py',
 'tools/analyze_selection.py','tools/write_fix7.py','tools/seal_fix7.py','tools/build_config_patch.py',
 'tests/fix7_fixtures.py','tests/test_fix7_selection.py','tests/test_fix7_deriver.py','tests/test_fix7_admission.py','tests/test_fix7_package.py',
 'evidence/final_checks.json','evidence/gate_binding.json','evidence/fix7_patch_manifest.json',
 'evidence/fix7_admission/latest.json','evidence/fix7_selection/production_attempt/q.json']
files += [str(p.relative_to(H)) for p in (H/'evidence/fix7_selection').iterdir() if p.is_file() and p.name!='delivery.json']
# Seal the successful audit and test result records; preserve all earlier attempts untouched.
for index in ['selection_tests','deriver_tests','package_tests']:
 root=Path(load('evidence/fix7_selection/'+index+'.json')['path'])
 for p in root.iterdir():
  if p.is_file():files.append(str(p.relative_to(H)))
 if index=='selection_tests':
  for d in ['equal','changed']:
   for n in ['r.json','q.json','native/receipt.json']:files.append(str((root/d/n).relative_to(H)))
 if index=='deriver_tests':
  for n in ['derived/SHA256SUMS.txt','derived/k/selection_equality.json','derived/k/pool_selection_7test.json']:
   files.append(str((root/n).relative_to(H)))
 if index=='package_tests':files.append(str((root/'patch/results.json').relative_to(H)))
root=Path(load('evidence/fix7_admission/latest.json')['path'])
files += [str(p.relative_to(H)) for p in root.rglob('*') if p.is_file()]
# Small retained references needed to reproduce the stdlib deriver generator.
files += [str(p.relative_to(H)) for p in (H/'evidence/fix7_before').rglob('*') if p.is_file()]
files += ['evidence/derivation/d0/k/pool_selection.json']
changed={n:sha(H/n) for n in sorted(set(files))}
write('evidence/fix7_selection/delivery.json',dict(status='BLOCKED',fix_status='PASS',files=changed,
 outer_manifest='SHA256SUMS.txt seals this record; no self-hash.'))
# Preserve inherited immutable seals; update only files changed or added in this task.
prior=dict((n,h) for h,n in (line.split('  ',1) for line in (H/'evidence/fix7_before/SHA256SUMS.txt').read_text().splitlines()))
prior.update(changed)
prior['evidence/fix7_selection/delivery.json']=sha(H/'evidence/fix7_selection/delivery.json')
(H/'SHA256SUMS.txt').write_text(''.join(h+'  '+n+'\n' for n,h in sorted(prior.items())))
assert all(sha(H/n)==h for n,h in changed.items())
print(json.dumps(dict(status='BLOCKED',fix_status='PASS',sealed_changed_files=len(changed),
 manifest_sha256=sha(H/'SHA256SUMS.txt'),q_sha256=sha(H/'build/q.sh')),indent=2))
