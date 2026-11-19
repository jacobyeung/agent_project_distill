"""Verify the delivered patches, fresh applications, evidence and immutable backup."""
import ast,hashlib,json,re,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path
L=Path('/scratch/jjyeung/orch_n30/so_read');O=L/'out';B=L/'out_round8';C=O/'checks'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
old=json.loads((B/'checks/FINAL_INTEGRITY.json').read_text())
for key,rel in [('manifest_sha256','patches/MANIFEST.json'),('report_sha256','REPORT.md'),('note_sha256','NOTE_FOR_CONT_OPS.md')]:assert sha(B/rel)==old[key],rel
for group in ('documents','checks'):
    for rel,pin in old[group].items():assert sha(B/rel)==pin,rel
for name,pin in old['patches'].items():assert sha(B/'patches'/name)==pin,name
before=json.loads((B/'patches/MANIFEST.json').read_text())
for group in before['patches'].values():
    for rel,pin in group['files'].items():
        if rel.startswith('u0/'):assert sha(L/'work/round8-before-u0'/Path(rel).relative_to('u0'))==pin['after_sha256'],rel
assert sha(L/'work/round8-before-5.py')==before['operator_files']['package/a/5.py']['sha256']
for folder,key in [('kit_parity50','kit_files'),('operator','operator_files'),('operations','operations_files')]:
    for rel,pin in before[key].items():assert sha(B/folder/rel)==pin['sha256'],rel
m=json.loads((O/'patches/MANIFEST.json').read_text());verify=Path(m['verification_root'])
assert len(m['patches'])==5 and {p.name for p in (O/'patches').glob('*.diff')}==set(m['patches'])
for name,group in m['patches'].items():
    assert sha(O/'patches'/name)==group['sha256'],name
    for rel,pin in group['files'].items():
        current=L/'work/src'/rel if rel.startswith('u0/') else O/'operator'/rel
        applied=verify/'src'/rel if rel.startswith('u0/') else verify/'operator'/rel
        assert sha(current)==pin['after_sha256']==sha(applied),rel
for rel,pin in m['base_pin']['inventory'].items():assert sha(verify/'src'/rel)==pin==sha(Path(m['base'])/rel),rel
originals={str(p.relative_to(L/'work/src')):p for p in (L/'work/src').rglob('*')
    if p.is_file() and p.relative_to(L/'work/src').parts[0]!='u0' and '__pycache__' not in p.parts and p.suffix!='.pyc'}
assert len(originals)==85 and set(originals)<=set(m['base_pin']['inventory'])
for rel,p in originals.items():assert sha(p)==m['base_pin']['inventory'][rel],rel
for folder,key in [('kit_parity50','kit_files'),('operator','operator_files'),('operations','operations_files')]:
    assert {str(p.relative_to(O/folder)) for p in (O/folder).rglob('*') if p.is_file()}==set(m[key])
    for rel,pin in m[key].items():assert sha(O/folder/rel)==pin['sha256'] and (O/folder/rel).stat().st_size==pin['bytes'],rel
pins=json.loads((O/'kit_parity50/EXTENSION_PINS.json').read_text())
assert len(pins)==38 and pins=={rel:pin['after_sha256'] for g in m['patches'].values() for rel,pin in g['files'].items() if rel.startswith('u0/')}
assert json.loads((O/'kit_parity50/BASE_PIN.json').read_text())==m['base_pin']
sys.path.insert(0,str(L/'work/src/u0'))
from a9 import pack
sample=(json.dumps({'u0':pack(json.loads((O/'kit_parity50/sample50.json').read_text()))},sort_keys=True)+'\n').encode()
assert hashlib.sha256(sample).hexdigest()==m['kit_files']['sample50.json']['public_sha256']
base=Path(m['base']).parent
assert m['a4_payload_pin']==dict(sha256=sha(base/'package/0.tgz'),bytes=(base/'package/0.tgz').stat().st_size)
for rel,pin in m['a4_member_pins'].items():assert pin==dict(sha256=sha(base/rel),bytes=(base/rel).stat().st_size)
assert m['operator_base_pin']['batch_sha256']==sha(base/'package/BATCH.sh')
assert m['operator_base_pin']['decoded_bootstrap_sha256']==sha(O/'operator/0.py')
provenance=json.loads((O/'operations/DEFAULT_EXPORT_PROVENANCE.json').read_text());ref=Path(provenance['source'])
for name,pin in provenance['source_pins'].items():assert sha(ref/name)==pin['sha256']
assert (ref/'export.json').read_bytes()==(O/'operations/BOUND_EXPORT.json').read_bytes()
export=json.loads((ref/'export.json').read_text());binding=json.loads((O/'operations/binding.default.json').read_text())
assert export['artifact']['sha256']=='5083243cfedd2a389dfca579c5452e7d0c73b03a58e1cb7d204292ddd10e67cd' and export['step']==binding['step']==400
assert provenance['source_package']=='a15_cot_apdc76460c3a164' and provenance['job']==173060
inputs=json.loads((ref/'1.json').read_text());assert inputs['export_pin']['sha256']==sha(ref/'export.json')
assert binding['archive_bytes']==sum(p['bytes'] for p in inputs['archives'][0]['parts'])
tree=ast.parse((L/'work/src/u0/a19.py').read_text())
selected=next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='DEFAULT_BOUND_EXPORT' for t in n.targets))
assert selected==export
report=(O/'REPORT.md').read_text();note=(O/'NOTE_FOR_CONT_OPS.md').read_text();readme=(O/'kit_parity50/README.md').read_text()
for t in (report,note):
    assert t.startswith('VERDICT: DONE ')
    assert '## Review round 8: finding -> fix -> test' in t
    assert 'u0/a19.py' in t and '--manifest' in t and '--extension-pins' in t
    assert 'synthetic' in t and 'GPU' in t
for t in (note,readme):
    assert 'Package D' in t and 'no ON route' in t and '636-item' in t and '7,351.824' in t
    assert 'refused unpack leaves' in t.lower() and 'success output' in t.lower()
    assert '$LOCAL/step600' not in t and '$STEP600_BINDING' not in t and '$LOCAL/5.tar' not in t
r=json.loads((C/'RESULTS.json').read_text())
count=lambda rows:sum(int(re.search(r'Ran (\d+) tests?',(C/x['output']).read_text()).group(1)) for x in rows)
workspace=count(r['results']);applied=count(m['applied_cpu_suites'])
assert workspace==129 and applied==48,(workspace,applied)
for row in [*r['results'],*m['applied_cpu_suites']]:
    text=(C/row['output']).read_text();assert row['returncode']==0 and re.search(r'\nOK\n',text)
    assert text.strip() in report,row['output']
controls=('round1_before.txt','round2_before.txt','round3_before.txt','operator3_before.txt','lock3_before.txt',
    'round4_before.txt','node4_before.txt','round5_before.txt','round6_before.txt','round7_before.txt','round8_before.txt','f16_behavior_before.txt')
for name in (*controls,'profile_rerun.txt','torch_versions3.txt','cache_cost3.txt','run_checks8.txt','build_patches8.txt',
             'gate_integration8.txt','docs8.txt','archive_command8.txt','storage8.txt'):
    assert (C/name).read_text().strip() in report,name
assert 'FAILED (failures=10)' in (C/'round7_before.txt').read_text()
assert 'PASS: archive reconstructs READY-identical' in (C/'gate_integration8.txt').read_text()
assert '38 files' in report
assert 'FAILED (failures=29)' in (C/'round8_before.txt').read_text()
assert '--bound-export' not in readme
assert '33 GB' in note and '33 GB' in report
assert 'adoption_environment' in (O/'kit_parity50/run.py').read_text()
stamp=subprocess.check_output(['date','-u'],text=True).strip()
assert datetime.now(timezone.utc)<datetime(2026,11,19,18,30,31,tzinfo=timezone.utc)
size=int(subprocess.check_output(['du','-sb',str(L)],text=True).split()[0]);assert size<3_000_000_000,size
receipt=dict(passed=True,utc=stamp,manifest_sha256=sha(O/'patches/MANIFEST.json'),report_sha256=sha(O/'REPORT.md'),note_sha256=sha(O/'NOTE_FOR_CONT_OPS.md'),
    backup_verified=True,reviewed_round8_source_verified=True,workspace_tests=workspace,fresh_application_tests=applied,
    baseline_controls=len(controls),round8_expected_assertion_failures=29,workspace_bytes_before_seal=size,
    workspace_original_files_verified=len(originals),applied_original_files_verified=len(m['base_pin']['inventory']),
    base_sha256=m['base_pin']['sha256'],a4_payload_pin=m['a4_payload_pin'],default_export=export,
    patches={n:sha(O/'patches'/n) for n in m['patches']},
    documents={n:sha(O/n) for n in ('REPORT.md','NOTE_FOR_CONT_OPS.md','FRAMEWORK_EVIDENCE.md','kit_parity50/README.md')},
    checks={str(p.relative_to(O)):sha(p) for p in sorted(C.iterdir()) if p.is_file() and p.name not in ('FINAL_INTEGRITY.json','integrity8.txt')})
(C/'FINAL_INTEGRITY.json').write_text(json.dumps(receipt,sort_keys=True,indent=2)+'\n')
size=int(subprocess.check_output(['du','-sb',str(L)],text=True).split()[0]);assert size<3_000_000_000,size
(L/'work/STATUS.md').write_text(stamp+f"""
VERDICT: DONE — round-8 fixes and delivery are complete.
All five findings are fixed. The archive preserves admitted symlinks, rejects escaping/broken/cyclic links and retains stderr.
The GPU interpreter/cache/preflight contract is explicit; CPU READY, gate, workers, ue.json and submit bind environment versions and SHA256.
The builder admits only step 400 before reading base inputs; no alternate-export gate parameter remains. Archive-path aliases resolve on both sides.
{workspace} workspace tests and {applied} fresh-application tests pass. All 12 retained failure controls reran; the ten round-8 tests produce 29 expected assertion failures before fixes.
Five diffs apply with zero fuzz; original reader bytes and OFF output bytes are unchanged. ON CPU answers/traces remain exact.
Archive/real-loader admission, CPU operator path, synthetic gate/submit integration, source probes, benchmark/profile and documentation checks pass.
Workspace size after seal: {size:,} unique-inode bytes. out_round8 and the reviewed source snapshot retain their original hashes.
No GPU, Git, SSH, scheduler operation, paid API, input-tree edit or deletion command ran. Production GPU parity/performance/memory and host interpreter/restore remain unrun.
Completed before 18:30:31 UTC. FINAL_INTEGRITY.json seals the delivery.
""")
print('PASS: immutable backup/source snapshot, five patches, fresh applications and all delivery hashes verified.')
print('PASS:',workspace,'workspace tests;',applied,'applied tests; 12 baseline controls; round 8 has 29 expected pre-fix assertion failures.')
print('PASS: step-400-only build, symlink archive/real-loader admission, environment/kit-bound submit; GPU gate remains unrun.')
print('Workspace unique-inode bytes:',size,'Completed:',stamp,'Deadline: Thu Nov 19 18:30:31 UTC 2026')
