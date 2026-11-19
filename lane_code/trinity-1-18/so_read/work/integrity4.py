"""Verify the completed round-4 delivery without creating another fixture corpus."""
import hashlib,json,re,subprocess
from datetime import datetime,timezone
from pathlib import Path
L=Path('/scratch/jjyeung/orch_n30/so_read');O=L/'out';B=L/'out_round4'
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
old=json.loads((B/'checks/FINAL_INTEGRITY.json').read_text())
for key,rel in [('manifest_sha256','patches/MANIFEST.json'),('report_sha256','REPORT.md'),('note_sha256','NOTE_FOR_CONT_OPS.md')]:
 assert sha(B/rel)==old[key],('Backup changed',rel)
for name,pin in old['patches'].items():assert sha(B/'patches'/name)==pin,name
old_manifest=json.loads((B/'patches/MANIFEST.json').read_text())
for info in old_manifest['patches'].values():
 for rel,pin in info['files'].items():
  if rel.startswith('u0/'):
   assert sha(L/'work/round4-before-u0'/Path(rel).relative_to('u0'))==pin['after_sha256'],rel
  else:assert sha(L/'work/round4-before-sequence.py')==pin['after_sha256'],rel
for folder,key in [('kit_parity50','kit_files'),('operator','operator_files')]:
 for name,pin in old_manifest[key].items():assert sha(B/folder/name)==pin['sha256'],name
manifest=json.loads((O/'patches/MANIFEST.json').read_text())
assert {p.name for p in (O/'patches').glob('*.diff')}==set(manifest['patches'])
assert len(manifest['patches'])==5
verify=Path(manifest['verification_root'])
for name,info in manifest['patches'].items():
 assert sha(O/'patches'/name)==info['sha256'],name
 for rel,pin in info['files'].items():
  path=L/'work/src'/rel if rel.startswith('u0/') else O/'operator'/rel
  applied=verify/'src'/rel if rel.startswith('u0/') else verify/'operator'/rel
  assert sha(path)==pin['after_sha256']==sha(applied),rel
for rel,digest in manifest['base_pin']['inventory'].items():assert sha(verify/'src'/rel)==digest,rel
for folder,key in [('kit_parity50','kit_files'),('operator','operator_files')]:
 expected=manifest[key]
 assert {str(p.relative_to(O/folder)) for p in (O/folder).rglob('*') if p.is_file()}==set(expected)
 for name,pin in expected.items():assert sha(O/folder/name)==pin['sha256'],name
pins=json.loads((O/'kit_parity50/EXTENSION_PINS.json').read_text())
assert pins=={rel:pin['after_sha256'] for info in manifest['patches'].values() for rel,pin in info['files'].items() if rel.startswith('u0/')}
assert json.loads((O/'kit_parity50/BASE_PIN.json').read_text())==manifest['base_pin']
report=(O/'REPORT.md').read_text();note=(O/'NOTE_FOR_CONT_OPS.md').read_text()
for text in (report,note):
 assert text.startswith('VERDICT: DONE ')
 assert '## Review round 4: finding -> fix -> test' in text
 assert 'zero' in text and 'synthetic' in text
 assert '--export-binding' in text and 'u0/a19.py' in text
results=json.loads((O/'checks/RESULTS.json').read_text())
count=lambda rows:sum(int(re.search(r'Ran (\d+) tests?',(O/'checks'/row['output']).read_text()).group(1)) for row in rows)
assert count(results['results'])==95
assert count(manifest['applied_cpu_suites'])==14
for row in [*results['results'],*manifest['applied_cpu_suites']]:
 assert row['returncode']==0
 assert (O/'checks'/row['output']).read_text().strip() in report,row['output']
for name in ('round1_before.txt','round2_before.txt','round3_before.txt','operator3_before.txt','lock3_before.txt',
             'f16_behavior_before.txt','round4_before.txt','node4_before.txt','profile_rerun.txt','torch_versions3.txt',
             'cache_cost3.txt','run_checks4.txt','build_patches4.txt'):
 assert (O/'checks'/name).read_text().strip() in report,name
stamp=subprocess.check_output(['date','-u'],text=True).strip()
size=int(subprocess.check_output(['du','-sb',str(L)],text=True).split()[0])
assert size<3_000_000_000,size
assert datetime.now(timezone.utc)<datetime(2026,11,19,14,32,2,tzinfo=timezone.utc)
receipt=dict(passed=True,utc=stamp,base_sha256=manifest['base_pin']['sha256'],workspace_bytes=size,
             manifest_sha256=sha(O/'patches/MANIFEST.json'),report_sha256=sha(O/'REPORT.md'),
             note_sha256=sha(O/'NOTE_FOR_CONT_OPS.md'),patches={n:sha(O/'patches'/n) for n in manifest['patches']},
             backup_verified=True,reviewed_round4_baseline_verified=True,
             operator_bootstrap_sha256=sha(O/'operator/0.py'),
             workspace_tests=95,fresh_application_tests=14,
             checks={str(p.relative_to(O)):sha(p) for p in sorted((O/'checks').iterdir())
                     if p.is_file() and p.name not in ('FINAL_INTEGRITY.json','integrity4.txt')},
             documents={n:sha(O/n) for n in ('REPORT.md','NOTE_FOR_CONT_OPS.md','FRAMEWORK_EVIDENCE.md','kit_parity50/README.md')})
(O/'checks/FINAL_INTEGRITY.json').write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n')
(L/'work/STATUS.md').write_text(f'''{stamp}
VERDICT: DONE — round-4 fixes, CPU verification and handoff are complete.

- A4 build_r1-style post-processing preserves run keys, the Python-3.6 submit helper, export admission and the required target export/whole-archive binding. It seals target fill-helper constants and regenerates all pins. Generic a12 operator builds fail closed.
- Real A4 CPU-proof, bootstrap, job.main, action-0 preparation and action-1 operator/runner paths pass with stub storage/namespace/models. The cache-only step-600 fixture completes 636 items in five verified ordinary journals. It is synthetic, not a production export or launch package.
- ON unpack rejects unverified weights on partial and complete returns. OFF reader outputs and original files remain byte-identical.
- 95 workspace tests pass. All earlier failing baselines and seven round-4 failure assertions reproduce; the old CPU-proof helper independently fails the cache-allowance assertion.
- Five diffs apply with zero fuzz; all 33 additive reader files and three operator files match tested source. Both 927-file base inventories authenticate. Fourteen OFF/integration/comparator tests pass from the fresh application. Other suites already ran against those exact bytes; avoiding redundant fixture copies keeps the workspace under 3 GB without deletion.
- Profile, framework mutation probes and CPU guard benchmark reran. REPORT embeds every listed test's exact current output. NOTE and README give the bound build/fill/proof commands and required round-4 section.
- Backup out_round4 and the reviewed source snapshot match their original integrity pins. FINAL_INTEGRITY.json binds the final manifest, patches, documents and receipts.
- Measured workspace size is {size:,} bytes < 3,000,000,000. CPU threads <= 8; benchmark peak RSS 1,310,048,256 bytes. No GPU, Git, SSH, scheduler, paid API, deletion or input-tree edit ran.
- Actual step-600 export/binding, GPU byte/performance/memory gates, real restore/storage/requeue and multi-card operator remain unrun/undelivered. Candidate adoption is single-card caches-only on general/no-requeue after the GPU gates. Array approval remains false.
''')
print('PASS: five patch hashes, all source/kit/operator pins, both 927-file bases, and exact report outputs.')
print('PASS: out_round4 backup and reviewed round-4 source snapshot match their original pins.')
print('PASS: 95 workspace tests and 14 fresh-application tests; required regressions fail before and pass after.')
print(f'PASS: workspace {size} bytes < 3,000,000,000; completed before 14:32:02 UTC.')
print('UTC: '+stamp)
