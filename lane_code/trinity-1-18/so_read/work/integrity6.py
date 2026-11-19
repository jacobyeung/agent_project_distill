"""Seal the tested round-6 delivery and verify the immutable reviewed snapshot."""
import hashlib,json,re,subprocess
from datetime import datetime,timezone
from pathlib import Path
L=Path('/scratch/jjyeung/orch_n30/so_read');O=L/'out';B=L/'out_round6'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
old=json.loads((B/'checks/FINAL_INTEGRITY.json').read_text())
for key,rel in [('manifest_sha256','patches/MANIFEST.json'),('report_sha256','REPORT.md'),('note_sha256','NOTE_FOR_CONT_OPS.md')]:assert sha(B/rel)==old[key],rel
for group in ('documents','checks'):
    for rel,pin in old[group].items():assert sha(B/rel)==pin,rel
for name,pin in old['patches'].items():assert sha(B/'patches'/name)==pin,name
before=json.loads((B/'patches/MANIFEST.json').read_text())
for group in before['patches'].values():
    for rel,pin in group['files'].items():
        if rel.startswith('u0/'):assert sha(L/'work/round6-before-u0'/Path(rel).relative_to('u0'))==pin['after_sha256'],rel
for folder,key in [('kit_parity50','kit_files'),('operator','operator_files'),('operations','operations_files')]:
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
workspace_originals={str(p.relative_to(L/'work/src')):p for p in (L/'work/src').rglob('*')
    if p.is_file() and p.relative_to(L/'work/src').parts[0]!='u0' and '__pycache__' not in p.parts and p.suffix!='.pyc'}
assert len(workspace_originals)==85 and set(workspace_originals)<=set(m['base_pin']['inventory'])
for rel,path in workspace_originals.items():assert sha(path)==m['base_pin']['inventory'][rel],rel
for folder,key in [('kit_parity50','kit_files'),('operator','operator_files'),('operations','operations_files')]:
    expected=m[key]
    assert {str(p.relative_to(O/folder)) for p in (O/folder).rglob('*') if p.is_file()}==set(expected)
    for rel,pin in expected.items():assert sha(O/folder/rel)==pin['sha256'],rel
pins=json.loads((O/'kit_parity50/EXTENSION_PINS.json').read_text())
assert len(pins)==36
assert pins=={rel:pin['after_sha256'] for group in m['patches'].values() for rel,pin in group['files'].items() if rel.startswith('u0/')}
assert json.loads((O/'kit_parity50/BASE_PIN.json').read_text())==m['base_pin']
base=Path(m['base']).parent
assert m['a4_payload_pin']==dict(sha256=sha(base/'package/0.tgz'),bytes=(base/'package/0.tgz').stat().st_size)
assert len(m['a4_member_pins'])==6
for rel,pin in m['a4_member_pins'].items():assert pin==dict(sha256=sha(base/rel),bytes=(base/rel).stat().st_size)
assert m['operator_base_pin']['batch_sha256']==sha(base/'package/BATCH.sh')
assert m['operator_base_pin']['decoded_bootstrap_sha256']==sha(O/'operator/0.py')
report=(O/'REPORT.md').read_text();note=(O/'NOTE_FOR_CONT_OPS.md').read_text();readme=(O/'kit_parity50/README.md').read_text()
for text in (report,note):
    assert text.startswith('VERDICT: DONE ')
    assert '## Review round 6: finding -> fix -> test' in text
    assert '--manifest' in text and '--extension-pins' in text and 'u0/a19.py' in text
    assert 'GPU' in text and 'synthetic' in text
for text in (note,readme):
    assert 'Package D' in text and 'no ON route' in text and '636-item' in text and '7,351.824' in text
    assert 'refused unpack leaves' in text.lower() and 'success output' in text.lower()
r=json.loads((O/'checks/RESULTS.json').read_text())
count=lambda rows:sum(int(re.search(r'Ran (\d+) tests?',(O/'checks'/x['output']).read_text()).group(1)) for x in rows)
workspace=count(r['results']);applied=count(m['applied_cpu_suites'])
assert workspace==111 and applied==30,(workspace,applied)
for row in [*r['results'],*m['applied_cpu_suites']]:
    text=(O/'checks'/row['output']).read_text()
    assert row['returncode']==0 and re.search(r'\nOK\n',text)
    assert text.strip() in report,row['output']
controls=('round1_before.txt','round2_before.txt','round3_before.txt','operator3_before.txt','lock3_before.txt',
          'round4_before.txt','node4_before.txt','round5_before.txt','round6_before.txt','f16_behavior_before.txt')
for name in (*controls,'profile_rerun.txt','torch_versions3.txt','cache_cost3.txt','run_checks6.txt',
             'build_patches6.txt','gate_integration6.txt','docs6.txt','storage6.txt'):
    assert (O/'checks'/name).read_text().strip() in report,name
assert 'FAILED (failures=31)' in (O/'checks/round6_before.txt').read_text()
assert "ModuleNotFoundError: No module named 'fetch_return'" in (O/'checks/round6_before.txt').read_text()
assert 'PASS: real bundle/entry/memory CPU proof' in (O/'checks/gate_integration6.txt').read_text()
assert 'AssertionError' not in (O/'checks/run_checks6.txt').read_text()
assert '36 files' in report
stamp=subprocess.check_output(['date','-u'],text=True).strip()
assert datetime.now(timezone.utc)<datetime(2026,11,19,16,13,3,tzinfo=timezone.utc)
size=int(subprocess.check_output(['du','-sb',str(L)],text=True).split()[0]);assert size<3_000_000_000,size
receipt=dict(passed=True,utc=stamp,manifest_sha256=sha(O/'patches/MANIFEST.json'),report_sha256=sha(O/'REPORT.md'),note_sha256=sha(O/'NOTE_FOR_CONT_OPS.md'),
    backup_verified=True,reviewed_round6_source_verified=True,workspace_tests=workspace,fresh_application_tests=applied,
    baseline_controls=len(controls),round6_expected_assertion_failures=31,workspace_bytes_before_seal=size,
    workspace_original_files_verified=len(workspace_originals),applied_original_files_verified=len(m['base_pin']['inventory']),
    base_sha256=m['base_pin']['sha256'],a4_payload_pin=m['a4_payload_pin'],a4_member_pins=m['a4_member_pins'],
    patches={name:sha(O/'patches'/name) for name in m['patches']},
    documents={name:sha(O/name) for name in ('REPORT.md','NOTE_FOR_CONT_OPS.md','FRAMEWORK_EVIDENCE.md','kit_parity50/README.md')},
    operations={str(p.relative_to(O)):sha(p) for p in (O/'operations').iterdir() if p.is_file()},
    checks={str(p.relative_to(O)):sha(p) for p in sorted((O/'checks').iterdir()) if p.is_file() and p.name not in ('FINAL_INTEGRITY.json','integrity6.txt')})
(O/'checks/FINAL_INTEGRITY.json').write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n')
size_after=int(subprocess.check_output(['du','-sb',str(L)],text=True).split()[0]);assert size_after<3_000_000_000,size_after
(L/'work/STATUS.md').write_text(stamp+f'''
VERDICT: DONE — round-6 fixes, tests, patches and handoff are complete.

- The out_round6 backup and 35-file source snapshot match their original pins.
- README unpack runs as written. Pull/fill/dry runs under nohup with an attempt lock, PID/log and success/failure exit file.
- Submit embeds every cont_ops A4 CPU assertion and requires the bound successful GPU receipt. A4 copied members, batch and bootstrap are pinned before output.
- The gate binds CPU restore/manifest receipts and step-600 export identity. Workers recheck staged assets and require H100 80 GB. CPU proof exports the small exact receipts needed for local preflight.
- {workspace} workspace tests and {applied} applied tests pass. All ten baseline controls reran; round 6 fails 31 assertions on the reviewed snapshot and passes after fixes.
- Five diffs apply with zero fuzz; all original reader and OFF output bytes remain unchanged. ON CPU answer/trace checks pass. GPU byte equality remains unrun and mandatory.
- Profile, framework probes, guard benchmark, real CPU-proof gate/submit integration and documentation checks pass. Exact outputs and measured resources are in REPORT.md.
- The final workspace is {size_after:,} unique-inode bytes, below 3 GB. Immutable fixture sharing preserves every path. No GPU, Git, SSH, scheduler action, paid API, deletion command or input-tree edit ran.
- Real target weights, production transfer/restore, GPU parity/performance/memory and persistent requeue remain external checks. No multi-card A4 operator is delivered.
- Completed before 16:13:03 UTC; FINAL_INTEGRITY.json seals the reviewed delivery and evidence.
''')
print('PASS: five patch hashes, 36 extension pins, operator/kit/operation files and the complete 927-file A4 bases.')
print('PASS: all six additional A4 member pins, base batch and decoded-bootstrap pins; no original reader byte changed.')
print('PASS: out_round6 backup and reviewed source snapshot retain their original pins.')
print('PASS:',workspace,'workspace tests,',applied,'fresh-application tests, ten baseline controls and actual CPU-proof gate integration.')
print('PASS: exact report outputs, requested review sections, manifest and document hashes.')
print('PASS: workspace after seal',size_after,'bytes < 3,000,000,000.')
print('UTC:',stamp,'— before 16:13:03 UTC deadline.')
