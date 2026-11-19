"""Verify the round-10 delivery, the preserved snapshot and all recorded evidence."""
import ast,hashlib,json,re,subprocess
from datetime import datetime,timezone
from pathlib import Path

L=Path('/scratch/jjyeung/orch_n30/so_read');O=L/'out';B=L/'out_round10';C=O/'checks'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
old=json.loads((B/'checks/FINAL_INTEGRITY.json').read_text())
for key,rel in (('manifest_sha256','patches/MANIFEST.json'),('report_sha256','REPORT.md'),('note_sha256','NOTE_FOR_CONT_OPS.md')):
    assert sha(B/rel)==old[key],rel
for group in ('documents','checks'):
    for rel,pin in old[group].items():assert sha(B/rel)==pin,rel
for name,pin in old['patches'].items():assert sha(B/'patches'/name)==pin,name
before=json.loads((B/'patches/MANIFEST.json').read_text())
for folder,key in (('kit_parity50','kit_files'),('operator','operator_files'),('operations','operations_files')):
    for rel,pin in before[key].items():assert sha(B/folder/rel)==pin['sha256'],rel
for name,group in (('a11','02_atomic_scene_shards.diff'),('a19','03_production_integration.diff')):
    assert sha(L/('work/round10-before-'+name+'.py'))==before['patches'][group]['files']['u0/'+name+'.py']['after_sha256']

m=json.loads((O/'patches/MANIFEST.json').read_text());verify=Path(m['verification_root'])
assert len(m['patches'])==5
for name,group in m['patches'].items():
    assert sha(O/'patches'/name)==group['sha256'],name
    assert (O/'patches'/name).stat().st_size==group['bytes']
    for rel,pin in group['files'].items():
        current=L/'work/src'/rel if rel.startswith('u0/') else O/'operator'/rel
        applied=verify/'src'/rel if rel.startswith('u0/') else verify/'operator'/rel
        assert sha(current)==pin['after_sha256']==sha(applied),rel
for rel,pin in m['base_pin']['inventory'].items():
    assert sha(verify/'src'/rel)==pin==sha(Path(m['base'])/rel),rel
originals={str(p.relative_to(L/'work/src')):p for p in (L/'work/src').rglob('*')
    if p.is_file() and p.relative_to(L/'work/src').parts[0]!='u0' and '__pycache__' not in p.parts and p.suffix!='.pyc'}
assert len(originals)==85
for rel,p in originals.items():assert sha(p)==m['base_pin']['inventory'][rel]
for folder,key in (('kit_parity50','kit_files'),('operator','operator_files'),('operations','operations_files')):
    assert {str(p.relative_to(O/folder)) for p in (O/folder).rglob('*') if p.is_file()}==set(m[key])
    for rel,pin in m[key].items():
        assert sha(O/folder/rel)==pin['sha256'] and (O/folder/rel).stat().st_size==pin['bytes'],rel
pins=json.loads((O/'kit_parity50/EXTENSION_PINS.json').read_text())
assert len(pins)==42
assert pins=={rel:pin['after_sha256'] for group in m['patches'].values() for rel,pin in group['files'].items() if rel.startswith('u0/')}
assert json.loads((O/'kit_parity50/BASE_PIN.json').read_text())==m['base_pin']
assert (O/'kit_parity50/host.py').read_bytes()==(L/'work/src/u0/a21.py').read_bytes()
assert (O/'kit_parity50/u5.py').read_bytes()==(L/'work/src/u0/a22.py').read_bytes()
assert 'u5.py' in m['kit_files']
base=Path(m['base']).parent
assert m['a4_payload_pin']==dict(sha256=sha(base/'package/0.tgz'),bytes=(base/'package/0.tgz').stat().st_size)
for rel,pin in m['a4_member_pins'].items():assert pin==dict(sha256=sha(base/rel),bytes=(base/rel).stat().st_size)
assert m['operator_base_pin']['batch_sha256']==sha(base/'package/BATCH.sh')
assert m['operator_base_pin']['decoded_bootstrap_sha256']==sha(O/'operator/0.py')
wrapper=json.loads((C/'A4_WRAPPER_PINS10.json').read_text())
assert m['a4_wrapper_member_pins']==wrapper
assert wrapper['prior_independent_wrapper_sha256_pins'] is False
tree=ast.parse((L/'work/src/u0/tests/test_round10.py').read_text())
literal={t.id:ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign)
         for t in n.targets if isinstance(t,ast.Name) and t.id in ('BOOT','WRAPPER','WRAPPER_PINS')}
for name,key in (('v/py','WRAPPER'),('v/boot.py','BOOT')):
    p=wrapper['members'][name];raw=Path(p['source']).read_bytes()
    assert raw==literal[key]
    assert dict(bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())==literal['WRAPPER_PINS'][name]
    assert sha(Path(p['source']))==p['sha256']

source=Path(m['base'])/'orchard_h10/vendor/ORCHARD_ASSETS.json'
assets=json.loads(source.read_text());runtime=json.loads((O/'kit_parity50/RUNTIME_PINS.json').read_text())
assert runtime=={key:assets[key] for key in runtime}
missing=json.loads((C/'RUNTIME_PREREQUISITES9.json').read_text())
assert missing['source_sha256']==sha(source)
assert len(missing['rows'])==14 and all(row['supplied'] is False for row in missing['rows'])
assert sum(row['bytes'] for row in missing['rows'] if row['group']!='bwrap')==10497433600
provenance=json.loads((O/'operations/DEFAULT_EXPORT_PROVENANCE.json').read_text());ref=Path(provenance['source'])
for name,pin in provenance['source_pins'].items():assert sha(ref/name)==pin['sha256']
inputs=json.loads((ref/'1.json').read_text());env=inputs['files']['env']
assert sha(C/'PRODUCTION_ENVIRONMENT9.json')==env['sha256']
assert (C/'PRODUCTION_ENVIRONMENT9.json').stat().st_size==env['bytes']
export=json.loads((ref/'export.json').read_text())
assert export['step']==400 and export['artifact']['sha256']=='5083243cfedd2a389dfca579c5452e7d0c73b03a58e1cb7d204292ddd10e67cd'
assert (ref/'export.json').read_bytes()==(O/'operations/BOUND_EXPORT.json').read_bytes()

r=json.loads((C/'RESULTS.json').read_text())
count=lambda rows:sum(int(re.search(r'Ran (\d+) tests?',(C/x['output']).read_text()).group(1)) for x in rows)
workspace=count(r['results']);applied=count(m['applied_cpu_suites'])
assert (workspace,applied)==(147,66),(workspace,applied)
assert r['cuda_visible_devices']=='' and r['torch_threads']==8
assert r['max_child_rss_bytes'] is None and 'aggregate is unavailable' in r['full_suite_resource_note']
assert m['applied_max_child_rss_bytes']<30*1024**3
cost=json.loads((C/'CACHE_COST3.json').read_text())
assert cost['max_rss_bytes']<30*1024**3 and cost['threads']==8 and cost['nice']>=10
report=(O/'REPORT.md').read_text();note=(O/'NOTE_FOR_CONT_OPS.md').read_text();readme=(O/'kit_parity50/README.md').read_text()
for text in (report,note):
    assert text.startswith('VERDICT: DONE ')
    assert '## Review round 10: finding -> fix -> test' in text
    assert 'u0/a19.py' in text and '--manifest' in text and '--extension-pins' in text
    assert '33 GB' in text and 'step 400' in text
for row in r['results']+m['applied_cpu_suites']:
    output=(C/row['output']).read_text()
    assert row['returncode']==0 and re.search(r'\nOK\n',output),row
    assert output.strip() in report,row['output']
    assert (C/row['output']).stat().st_mtime>datetime(2026,11,19,19,47,20,tzinfo=timezone.utc).timestamp()
controls=('round1_before','round2_before','round3_before','operator3_before','lock3_before','round4_before',
          'node4_before','round5_before','round6_before','round7_before','round8_before','round9_before','round10_before','f16_behavior_before')
for name in controls:
    raw=(C/(name+'.txt')).read_text();assert 'FAILED (' in raw and raw.strip() in report,name
    assert (C/(name+'.txt')).stat().st_mtime>datetime(2026,11,19,19,47,20,tzinfo=timezone.utc).timestamp()
assert 'FAILED (failures=7)' in (C/'round10_before.txt').read_text()
assert 'sys.executable' not in (O/'kit_parity50/run.py').read_text()
assert 'host.private_aliases' in readme
assert "archive.open('rb')" not in readme.split("<<'PYASSET'",1)[1].split('\nPYASSET',1)[0]
assert readme.index('--enable-extensions gate')<readme.index('--bwlimit=8000')<readme.index('salloc --account')
stamp=subprocess.check_output(['date','-u'],text=True).strip()
assert datetime.now(timezone.utc)<datetime(2026,11,19,20,47,20,tzinfo=timezone.utc)
size=int(subprocess.check_output(['du','-sb',str(L)],text=True).split()[0]);assert size<3_000_000_000,size
receipt=dict(passed=True,utc=stamp,manifest_sha256=sha(O/'patches/MANIFEST.json'),report_sha256=sha(O/'REPORT.md'),note_sha256=sha(O/'NOTE_FOR_CONT_OPS.md'),
    backup_verified=True,workspace_tests=workspace,fresh_application_tests=applied,baseline_controls=len(controls),
    round10_expected_assertion_failures=7,workspace_bytes_before_seal=size,observed_interim_workspace_bytes=3041057187,
    workspace_original_files_verified=len(originals),applied_original_files_verified=len(m['base_pin']['inventory']),
    base_sha256=m['base_pin']['sha256'],a4_payload_pin=m['a4_payload_pin'],default_export=export,
    runtime_prerequisites=missing['rows'],production_gpu_gate_run=False,wrapper_evidence=wrapper,
    patches={name:sha(O/'patches'/name) for name in m['patches']},
    documents={name:sha(O/name) for name in ('REPORT.md','NOTE_FOR_CONT_OPS.md','FRAMEWORK_EVIDENCE.md','kit_parity50/README.md')},
    checks={str(p.relative_to(O)):sha(p) for p in sorted(C.rglob('*')) if p.is_file() and p.name not in ('FINAL_INTEGRITY.json','integrity10.txt')})
(C/'FINAL_INTEGRITY.json').write_text(json.dumps(receipt,sort_keys=True,indent=2)+'\n')
size=int(subprocess.check_output(['du','-sb',str(L)],text=True).split()[0]);assert size<3_000_000_000,size
(L/'work/STATUS.md').write_text(stamp+f'''
VERDICT: DONE — round-10 fixes and delivery are complete.
{workspace} workspace tests and {applied} fresh-application tests pass. All 14 fail-before controls reran; all seven new tests fail before and pass after.
Pinned script preflight, exact boot bytes, one alias table, sealed-path existence, direct namespaced workers and one-pass archive hashing are verified on CPU fixtures.
Five patches apply with zero fuzz; original reader files and OFF output bytes remain unchanged. CPU ON equality passes; H100 byte equality remains required and unrun.
Supplied wrapper hashes/sizes match coordinator evidence; prior MANIFEST had no independent wrapper-member hashes. Exact supplied hashes are recorded and checked.
All 13 runtime parts plus bwrap remain pinned Orchard prerequisites. REPORT/NOTE include Review round 10 and exact test outputs. MANIFEST and FINAL_INTEGRITY seal the delivery. out_round10 bytes are unchanged.
Workspace after seal: {size:,} unique-inode bytes. An interim sample reached 3,041,057,187 bytes; byte-verified duplicate sharing restored the cap without removing paths.
No Git, SSH, SCP, Slurm, GPU, paid API, input edit or file-deletion command ran. Completed before 20:47:20 UTC.
''')
print('PASS: unchanged out_round10 snapshot; five patches, 42 extension files and all delivered hashes verified.')
print('PASS:',workspace,'workspace tests;',applied,'fresh-application tests; 14 fail-before controls; seven expected round-10 failures.')
print('PASS: original/OFF bytes unchanged; CPU ON equality passes; real boot bytes and staged-path resolution verified; H100 gate unrun.')
print('Wrapper evidence: both supplied SHA256/size checks match; prior independent member SHA256 pins absent.')
print('Workspace unique-inode bytes:',size,'Completed:',stamp,'Deadline: Thu Nov 19 20:47:20 UTC 2026')
