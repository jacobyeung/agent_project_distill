"""Seal the final round-5 delivery, preserving exact evidence and reviewed inputs."""
import ast,hashlib,json,re,subprocess
from datetime import datetime,timezone
from pathlib import Path
L=Path('/scratch/jjyeung/orch_n30/so_read');O=L/'out';B=L/'out_round5'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
old=json.loads((B/'checks/FINAL_INTEGRITY.json').read_text())
for key,rel in [('manifest_sha256','patches/MANIFEST.json'),('report_sha256','REPORT.md'),('note_sha256','NOTE_FOR_CONT_OPS.md')]:assert sha(B/rel)==old[key],rel
for rel,pin in old['documents'].items():assert sha(B/rel)==pin,rel
for rel,pin in old['checks'].items():assert sha(B/rel)==pin,rel
for name,pin in old['patches'].items():assert sha(B/'patches'/name)==pin,name
before=json.loads((B/'patches/MANIFEST.json').read_text())
for group in before['patches'].values():
 for rel,pin in group['files'].items():
  if rel.startswith('u0/'):assert sha(L/'work/round5-before-u0'/Path(rel).relative_to('u0'))==pin['after_sha256'],rel
for folder,key in [('kit_parity50','kit_files'),('operator','operator_files')]:
 for rel,pin in before[key].items():assert sha(B/folder/rel)==pin['sha256'],rel
m=json.loads((O/'patches/MANIFEST.json').read_text());verify=Path(m['verification_root'])
assert len(m['patches'])==5
assert {p.name for p in (O/'patches').glob('*.diff')}==set(m['patches'])
for name,group in m['patches'].items():
 assert sha(O/'patches'/name)==group['sha256'],name
 for rel,pin in group['files'].items():
  current=L/'work/src'/rel if rel.startswith('u0/') else O/'operator'/rel
  applied=verify/'src'/rel if rel.startswith('u0/') else verify/'operator'/rel
  assert sha(current)==pin['after_sha256']==sha(applied),rel
for rel,pin in m['base_pin']['inventory'].items():
 assert sha(verify/'src'/rel)==pin==sha(Path(m['base'])/rel),rel
for folder,key in [('kit_parity50','kit_files'),('operator','operator_files'),('operations','operations_files')]:
 expected=m[key]
 assert {str(p.relative_to(O/folder)) for p in (O/folder).rglob('*') if p.is_file()}==set(expected)
 for rel,pin in expected.items():assert sha(O/folder/rel)==pin['sha256'],rel
pins=json.loads((O/'kit_parity50/EXTENSION_PINS.json').read_text())
assert len(pins)==35
assert pins=={rel:pin['after_sha256'] for group in m['patches'].values() for rel,pin in group['files'].items() if rel.startswith('u0/')}
assert json.loads((O/'kit_parity50/BASE_PIN.json').read_text())==m['base_pin']
assert m['a4_payload_pin']==dict(sha256=sha(Path(m['base']).parent/'package/0.tgz'),bytes=(Path(m['base']).parent/'package/0.tgz').stat().st_size)
report=(O/'REPORT.md').read_text();note=(O/'NOTE_FOR_CONT_OPS.md').read_text();readme=(O/'kit_parity50/README.md').read_text()
for text in (report,note):
 assert text.startswith('VERDICT: DONE ')
 assert '## Review round 5: finding -> fix -> test' in text
 assert '--manifest' in text and '--extension-pins' in text and 'u0/a19.py' in text
 assert 'GPU' in text and 'synthetic' in text
for text in (note,readme):
 assert 'Package D' in text and 'no ON route' in text and '636-item' in text and '7,351.824' in text
 assert 'refused unpack leaves' in text.lower() and 'success output' in text.lower()
# Every documented shell block parses; nothing in those owner commands is executed.
blocks=re.findall(r'```bash\n(.*?)\n```',readme,re.S)
for block in blocks:
 checked=subprocess.run(['bash','-n'],input=block,text=True,capture_output=True)
 assert checked.returncode==0,checked.stderr
r=json.loads((O/'checks/RESULTS.json').read_text())
count=lambda rows:sum(int(re.search(r'Ran (\d+) tests?',(O/'checks'/x['output']).read_text()).group(1)) for x in rows)
assert count(r['results'])==102 and count(m['applied_cpu_suites'])==21
for row in [*r['results'],*m['applied_cpu_suites']]:
 text=(O/'checks'/row['output']).read_text()
 assert row['returncode']==0 and re.search(r'\nOK\n',text)
 assert text.strip() in report,row['output']
for name in ('round1_before.txt','round2_before.txt','round3_before.txt','operator3_before.txt','lock3_before.txt',
             'round4_before.txt','node4_before.txt','round5_before.txt','f16_behavior_before.txt','profile_rerun.txt',
             'torch_versions3.txt','cache_cost3.txt','run_checks5.txt','finish_checks5.txt','build_patches5.txt',
             'fixture_storage5.txt','retained_storage5.txt','gate_integration5.txt'):
 assert (O/'checks'/name).read_text().strip() in report,name
assert 'FAILED (failures=11)' in (O/'checks/round5_before.txt').read_text()
assert 'AssertionError' in (O/'checks/run_checks5.txt').read_text()
assert '3,004,528,639' in report and 'failed its final workspace-size assertion' in report
# Check every helper that the generated Orchard commands run with Python 3.6.
root=Path(re.search(r'CPU step-600 fixture: (.+)',(O/'checks/applied_round4.txt').read_text()).group(1))/'built'
for rel in ('package/3.py','package/a/4.py','package/a/5.py','package/a/6.py','package/a/7.py','src/8.py'):
 ast.parse((root/rel).read_text(),filename=rel,feature_version=(3,6))
source=Path('/scratch/jjyeung/orch_n30/so_in/scratch/jjyeung/orch_n30/cont_ops17/work')
for name in ('dryres2.py','dry2.py'):assert (O/'operations'/name).read_bytes()==(source/name).read_bytes()
stamp=subprocess.check_output(['date','-u'],text=True).strip()
assert datetime.now(timezone.utc)<datetime(2026,11,19,15,26,45,tzinfo=timezone.utc)
size=int(subprocess.check_output(['du','-sb',str(L)],text=True).split()[0]);assert size<3_000_000_000,size
receipt=dict(passed=True,utc=stamp,manifest_sha256=sha(O/'patches/MANIFEST.json'),report_sha256=sha(O/'REPORT.md'),note_sha256=sha(O/'NOTE_FOR_CONT_OPS.md'),
 backup_verified=True,reviewed_round5_baseline_verified=True,workspace_tests=102,fresh_application_tests=21,
 workspace_bytes_before_seal=size,interim_workspace_sample_bytes=3004528639,resource_exception_documented=True,
 base_sha256=m['base_pin']['sha256'],a4_payload_pin=m['a4_payload_pin'],
 patches={name:sha(O/'patches'/name) for name in m['patches']},
 documents={name:sha(O/name) for name in ('REPORT.md','NOTE_FOR_CONT_OPS.md','FRAMEWORK_EVIDENCE.md','kit_parity50/README.md')},
 operations={str(p.relative_to(O)):sha(p) for p in (O/'operations').iterdir() if p.is_file()},
 checks={str(p.relative_to(O)):sha(p) for p in sorted((O/'checks').iterdir()) if p.is_file() and p.name not in ('FINAL_INTEGRITY.json','integrity5.txt')})
(O/'checks/FINAL_INTEGRITY.json').write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n')
size_after=int(subprocess.check_output(['du','-sb',str(L)],text=True).split()[0]);assert size_after<3_000_000_000,size_after
(L/'work/STATUS.md').write_text(stamp+f'''
VERDICT: DONE — requested round-5 fixes, regression checks, patches and handoff are complete.

- Preserved out_round5 and the 33-file reviewed u0 snapshot; their original pins verify.
- a19 applies exact cont_ops wrap_batch; the built exclusion/EXIT/USR1 wrapper passes the real bundle guard. Reviewed A4 payload, three patched operator files, exact extension inventory and alias bases are authenticated before copying.
- a20 provides explicit binding derivation, delivery archive/SHA, placement, one-shot pull/fill, original dry checks, CPU allocation, guarded submit and fetch scripts. README gives proof/return archive staging and authenticated unpack. The submit checker tests CPU memory binding and the 75 MB pool boundary.
- The GPU gate derives the adopted per-read profile from exact A4 prepare bytes and CPU proof, applies the operator overrides, and pins cache slots/budget and plan. Both all-cache and processor-only profiles are covered. An additional check feeds the real applied CPU fixture's SETTINGS.json and CPU.json through the gate successfully.
- NOTE/README distinguish Package D from A4 and label forecasts as estimates. Scorers must use successful unpack output; refused trees and partial status are explicit.
- 102 workspace tests and 21 fresh-application tests pass. All nine fail-before controls reproduce; round 5 has seven tests and eleven expected baseline assertion failures. OFF source/output bytes remain identical; GPU ON answer/trace equality remains unrun and mandatory.
- Five diffs apply with zero fuzz. All 35 extension files and three operator files match tested/applied bytes. Both full A4 base inventories authenticate. Kit, dry helpers, manifest, documents and exact check outputs are sealed by FINAL_INTEGRITY.json.
- Profile, installed-framework probes and guard benchmark reran. The benchmark measured peak RSS 1,320,165,376 bytes. Full-suite driver RSS was not captured because its post-test workspace assertion failed.
- Resource exception: an interim workspace sample was 3,004,528,639 bytes. Sharing identical fixture files preserved all paths and bytes; measured size after the integrity seal is {size_after:,} bytes, below 3,000,000,000. The failed driver output and correction remain documented. No file-deletion command ran.
- No GPU, Git, SSH, scheduler action, paid API, upload, production restore or input-tree edit ran. All compute used nice -n 10, CUDA hidden and at most eight configured threads. Network reads covered official PyTorch docs only.
- Completed before the 15:26:45 UTC deadline. Actual export/binding, GPU parity/performance/memory, real transport/storage/requeue and a multi-card operator remain unrun or undelivered.
''')
print('PASS: five patch hashes, 35 extension pins, three operator files, all kit/operation files and both 927-file A4 bases.')
print('PASS: out_round5 backup and reviewed source snapshot retain their original pins.')
print('PASS: 102 workspace tests, 21 fresh-application tests, all nine baseline controls and real prepared-profile integration evidence.')
print('PASS: exact report outputs, documented Bash syntax and Python-3.6 helper syntax; requested review sections present.')
print('PASS: workspace after seal',size_after,'bytes < 3,000,000,000; interim cap exception is documented.')
print('UTC:',stamp,'— before 15:26:45 UTC deadline.')
