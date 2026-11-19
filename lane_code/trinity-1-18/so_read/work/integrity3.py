"""Check the delivery and untouched backup without rerunning model/tests."""
import hashlib,json,subprocess
from datetime import datetime,timezone
from pathlib import Path
L=Path('/scratch/jjyeung/orch_n30/so_read');O=L/'out';B=L/'out_round3'
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
old=json.loads((B/'checks/FINAL_INTEGRITY.json').read_text())
for key,path in [('manifest_sha256','patches/MANIFEST.json'),('report_sha256','REPORT.md'),('note_sha256','NOTE_FOR_CONT_OPS.md')]:
 assert sha(B/path)==old[key],('Backup changed',path)
for name,value in old['patches'].items():assert sha(B/'patches'/name)==value,name
old_manifest=json.loads((B/'patches/MANIFEST.json').read_text())
for patch in old_manifest['patches'].values():
 for name,pin in patch['files'].items():
  assert sha(L/'work/round3-before-u0'/Path(name).relative_to('u0'))==pin['after_sha256'],('Reviewed baseline changed',name)
for name,pin in old_manifest['kit_files'].items():assert sha(B/'kit_parity50'/name)==pin['sha256'],name
manifest=json.loads((O/'patches/MANIFEST.json').read_text())
assert set(p.name for p in (O/'patches').glob('*.diff'))==set(manifest['patches'])
for name,info in manifest['patches'].items():
 assert sha(O/'patches'/name)==info['sha256'],name
 for rel,pin in info['files'].items():
  path=O/'operator'/rel if name.startswith('04_') else L/'work/src'/rel
  assert sha(path)==pin['after_sha256'],rel
for folder,key in [('kit_parity50','kit_files'),('operator','operator_files')]:
 expected=manifest[key]
 assert {p.name for p in (O/folder).iterdir() if p.is_file()}==set(expected)
 for name,pin in expected.items():assert sha(O/folder/name)==pin['sha256'],name
pins=json.loads((O/'kit_parity50/EXTENSION_PINS.json').read_text())
assert pins=={rel:info['after_sha256'] for patch in manifest['patches'].values() for rel,info in patch['files'].items() if rel.startswith('u0/')}
assert json.loads((O/'kit_parity50/BASE_PIN.json').read_text())==manifest['base_pin']
report=(O/'REPORT.md').read_text();note=(O/'NOTE_FOR_CONT_OPS.md').read_text()
for text in (report,note):
 assert text.startswith('VERDICT: DONE ')
 assert '## Review round 3: finding -> fix -> test' in text
 assert 'single-card' in text and 'zero' in text
assert 'PASS: REPORT and NOTE' in (O/'checks/report3.txt').read_text()
results=json.loads((O/'checks/RESULTS.json').read_text())
for entry in [*results['results'],*manifest['applied_cpu_suites']]:
 assert entry['returncode']==0
 assert (O/'checks'/entry['output']).read_text().strip() in report
for path in ('round1_before.txt','round2_before.txt','round3_before.txt','operator3_before.txt','lock3_before.txt','f16_behavior_before.txt'):
 assert (O/'checks'/path).read_text().strip() in report
stamp=subprocess.check_output(['date','-u'],text=True).strip()
size=sum(p.stat().st_size for p in L.rglob('*') if p.is_file() and not p.is_symlink())
assert size<3*1024**3
assert datetime.now(timezone.utc)<datetime(2026,11,19,14,4,6,tzinfo=timezone.utc)
receipt=dict(passed=True,utc=stamp,base_sha256=manifest['base_pin']['sha256'],workspace_bytes=size,
             manifest_sha256=sha(O/'patches/MANIFEST.json'),report_sha256=sha(O/'REPORT.md'),
             note_sha256=sha(O/'NOTE_FOR_CONT_OPS.md'),patches={n:sha(O/'patches'/n) for n in manifest['patches']},
             backup_verified=True,reviewed_round3_baseline_verified=True,
             operator_bootstrap_sha256=sha(O/'operator/0.py'),
             checks={str(p.relative_to(O)):sha(p) for p in sorted((O/'checks').iterdir())
                     if p.is_file() and p.name not in ('FINAL_INTEGRITY.json','integrity3.txt')},
             documents={name:sha(O/name) for name in ('REPORT.md','NOTE_FOR_CONT_OPS.md','FRAMEWORK_EVIDENCE.md')})
(O/'checks/FINAL_INTEGRITY.json').write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n')
(L/'work/STATUS.md').write_text(f'''{stamp}
VERDICT: DONE — requested round-3 fixes and CPU handover are complete.

- Findings 1, 2, 3, 4 and 7 have fail-before/pass-after evidence.
- 91 workspace tests and 88 fresh-application tests pass. Exact output is in out/REPORT.md and out/checks/.
- Three additive reader patches plus one default-OFF A4 operator patch apply without fuzz. Both 927-file base inventories authenticate.
- out_round3 is verified against its original integrity receipt; the reviewed round-3 source snapshot matches its original pins.
- CPU per-call overhead measured 356.5 to 25.9 ms on the 268M-parameter stub and 731.2 to 52.6 ms on the 537M-parameter stub. No GPU speedup is claimed.
- Report, note, README, framework evidence, patches and MANIFEST are complete. FINAL_INTEGRITY.json authenticates the delivery.
- Final workspace size is {size:,} bytes, under 3 GB. No GPU, Git, SSH, scheduler, paid API, deletion or input-tree edit ran.
- GPU parity/performance/memory and remote requeue remain unrun. No multi-card operator is delivered; step 600 remains a single-card cache-only candidate after gates pass.
''')
print('PASS: four patch hashes, all source/kit/operator pins, exact report outputs, and both report verdicts.')
print('PASS: out_round3 backup and reviewed round-3 source snapshot match original integrity pins.')
print(f'PASS: final workspace {size} bytes < 3 GiB; completed before 14:04:06 UTC.')
print('UTC: '+stamp)
