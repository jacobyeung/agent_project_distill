"""Seal the reviewed local fix and preserve the unresolved admission blocker explicitly."""
import ast,hashlib,json
from pathlib import Path
H=Path(__file__).resolve().parents[1]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
load=lambda n:json.loads((H/n).read_text())
old=load('evidence/fix6_before/hashes.json');ids=load('ids.json');up=load('UPLOAD.json')
audit=load('evidence/fix6_admission/results.json');tests=load('evidence/fix6/tests.json')
assert all(v['status']=='PASS' for v in tests)
assert audit['carrier_c1_run.validate']['status']=='PASS'
assert audit['routing_selection_implementation']['status']=='BLOCKED'
assert audit['only_guard_and_review_pin_changed']['status']=='PASS'
for n in ('evidence/fix6_patch/results.json','evidence/fix6_package/results.json'):assert load(n)['status']=='PASS'
assert load('evidence/cpu/fallback_fix6/result.json')['slot']['verified'] is True
assert load('evidence/cpu/fallback_fix6/result.json')['slot']['step']==200
assert sha(H/'tests/RERUN_CHAIN.sh')==old['tests/RERUN_CHAIN.sh']
assert sha(H/'EXPORT_OBJECTS.txt')==old['EXPORT_OBJECTS.txt']
for n in ('payload/7.json','payload/'+ids['trainer']['file'],'payload/g.sh','payload/names.txt'):
 assert sha(H/n)==old[n]
assert sha(H/'payload/d.py')==sha(H/'tools/derive_kit_h1.py')
assert sha(H/'runtime/jb.sh')==sha(H/'payload/jb.sh')
assert load('payload/4.json')['production_go_granted'] is False
assert load('payload/review.json')['verdict']=='PENDING'
assert len((H/'FIX6.md').read_text().splitlines())<=25
for d in ('tools','tests','payload'):
 for p in (H/d).rglob('*.py'):ast.parse(p.read_text(),filename=str(p))
for v in up['files']:assert sha(H/'payload'/v['name'])==v['sha256']
assert sha(H/'build'/up['archive'])==up['sha256']
summary=dict(status='BLOCKED',deployment_ready=False,fix_status='PASS',regression_scripts=len(tests),
 admission_config_test='PASS; reproduces known routing selection refusal',
 blocker=audit['routing_selection_implementation'],admit=audit['admit'],
 identity=ids['identity'],contract=ids['contract'],config_key=ids['config_key'],
 run_key=ids['tokens']['run'],kit_key=ids['tokens']['kit'],persistent_root=ids['tokens']['root'],
 deterministic_package='PASS',cpu_step200_verified_slot='PASS',four_rank_chain='NOT RUN; runner unchanged',
 production_go_granted=False,trainer_unchanged=True,export_names_unchanged=True,old_kit_untouched=True)
(H/'evidence/final_checks.json').write_text(json.dumps(summary,indent=2)+'\n')
files={H/n for n in ('REPORT.md','DIFF.md','FIX6.md','ids.json','TOKENS_H1.json','UPLOAD.json','EXPORT_OBJECTS.txt','orch_h1.sh','fin_h1.sh','REMOVAL_CANDIDATES.md','build/c_patch.sh','build/g_patch.sh','build/over_local.json','build/over_fx.json','build/over_seed.json','build/fx/SHA256SUMS.txt','evidence/fx.json','evidence/fx_seed.json','evidence/final_checks.json','evidence/fix6_admission.log','evidence/fix6_patch_manifest.json','evidence/fix6_before/hashes.json','evidence/fix6_before/config.json')}
files.add(H/'build'/up['archive'])
for d in ('tools','tests','payload','runtime'):
 files.update(p for p in (H/d).rglob('*') if p.is_file() and '__pycache__' not in p.parts)
for d in ('evidence/fix6','evidence/fix6_patch','evidence/fix6_package'):
 files.update(p for p in (H/d).iterdir() if p.is_file())
files.update(p for p in (H/'evidence/fix6_admission').rglob('*') if p.is_file())
# Seal the exact prior immutable bytes against which the small operator patch verifies.
files.update(H/'evidence/fix6_before/payload'/p.name for p in (H/'payload').iterdir() if p.is_file())
for n in ('ids.json','UPLOAD.json','SHA256SUMS.txt','tools/derive_kit_h1.py','tools/make_deriver.py','tools/build_packet.py'):
 files.add(H/'evidence/fix6_before'/n)
for n in ('result.json','chain.log','slots/A.json','slots/A.sha256','run/s2.json','run/inputs/first_step_993.json'):
 files.add(H/'evidence/cpu/fallback_fix6'/n)
changes={str(p.relative_to(H)):dict(before=old.get(str(p.relative_to(H))),after=sha(p)) for p in sorted(files) if p.is_file() and not str(p.relative_to(H)).startswith('evidence/fix6_before/') and old.get(str(p.relative_to(H)))!=sha(p)}
record=dict(status='BLOCKED',fix_status='PASS',identity=ids['identity'],contract=ids['contract'],config_key=ids['config_key'],
 deployment_blocker='Routing selection belongs to another implementation',changed=changes,
 old_manifest_sha256=sha(H/'evidence/fix6_before/SHA256SUMS.txt'),outer_seal='SHA256SUMS.txt seals this record; no self-hash.')
p=H/'evidence/hash_changes_fix6.json';p.write_text(json.dumps(record,indent=2,sort_keys=True)+'\n');files.add(p)
assert all(p.is_file() for p in files)
size=sum(p.stat().st_size for p in files);assert size<200_000_000,size
text=''.join(sha(p)+'  '+str(p.relative_to(H))+'\n' for p in sorted(files))
manifest=H/'SHA256SUMS.txt';manifest.write_text(text)
# Verify the new outer manifest against independently reread bytes.
for line in manifest.read_text().splitlines():
 digest,name=line.split('  ',1);assert sha(H/name)==digest,name
print(json.dumps(dict(status='BLOCKED',fix_status='PASS',regression_scripts=len(tests),manifest_sha256=sha(manifest),sealed_files=len(files),sealed_bytes=size,patch_sha256=sha(H/'build/c_patch.sh')),indent=2))
