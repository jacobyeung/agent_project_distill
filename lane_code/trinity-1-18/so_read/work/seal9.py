"""Verify and seal the round-9 delivery without Git or input edits."""
import hashlib,json,re,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path

L=Path('/scratch/jjyeung/orch_n30/so_read');O=L/'out';B=L/'out_round9';C=O/'checks'
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
assert sha(L/'work/round9-before-a20.py')==before['patches']['03_production_integration.diff']['files']['u0/a20.py']['after_sha256']

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
assert len(pins)==40
assert pins=={rel:pin['after_sha256'] for group in m['patches'].values() for rel,pin in group['files'].items() if rel.startswith('u0/')}
assert json.loads((O/'kit_parity50/BASE_PIN.json').read_text())==m['base_pin']
assert (O/'kit_parity50/host.py').read_bytes()==(L/'work/src/u0/a21.py').read_bytes()
base=Path(m['base']).parent
assert m['a4_payload_pin']==dict(sha256=sha(base/'package/0.tgz'),bytes=(base/'package/0.tgz').stat().st_size)
for rel,pin in m['a4_member_pins'].items():
    assert pin==dict(sha256=sha(base/rel),bytes=(base/rel).stat().st_size)
assert m['operator_base_pin']['batch_sha256']==sha(base/'package/BATCH.sh')
assert m['operator_base_pin']['decoded_bootstrap_sha256']==sha(O/'operator/0.py')

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
sys.path.insert(0,str(L/'work/src/u0'))
from a9 import pack
sample=(json.dumps({'u0':pack(json.loads((O/'kit_parity50/sample50.json').read_text()))},sort_keys=True)+'\n').encode()
assert hashlib.sha256(sample).hexdigest()==m['kit_files']['sample50.json']['public_sha256']

r=json.loads((C/'RESULTS.json').read_text())
count=lambda rows:sum(int(re.search(r'Ran (\d+) tests?',(C/x['output']).read_text()).group(1)) for x in rows)
workspace=count(r['results']);applied=count(m['applied_cpu_suites'])
assert (workspace,applied)==(140,59),(workspace,applied)
assert r['cuda_visible_devices']=='' and r['torch_threads']==8
assert r['max_child_rss_bytes']<30*1024**3
cost=json.loads((C/'CACHE_COST3.json').read_text())
assert cost['max_rss_bytes']<30*1024**3 and cost['threads']==8 and cost['nice']>=10
report=(O/'REPORT.md').read_text();note=(O/'NOTE_FOR_CONT_OPS.md').read_text();readme=(O/'kit_parity50/README.md').read_text()
for text in (report,note):
    assert text.startswith('VERDICT: DONE ')
    assert '## Review round 9: finding -> fix -> test' in text
    assert 'u0/a19.py' in text and '--manifest' in text and '--extension-pins' in text
    assert '33 GB' in text and 'step 400' in text
for row in r['results']+m['applied_cpu_suites']:
    output=(C/row['output']).read_text()
    assert row['returncode']==0 and re.search(r'\nOK\n',output),row
    assert output.strip() in report,row['output']
controls=('round1_before','round2_before','round3_before','operator3_before','lock3_before','round4_before',
          'node4_before','round5_before','round6_before','round7_before','round8_before','round9_before','f16_behavior_before')
for name in controls:
    output=(C/(name+'.txt')).read_text();assert 'FAILED (' in output and output.strip() in report,name
assert 'FAILED (failures=11)' in (C/'round9_before.txt').read_text()
assert 'FAILED (failures=29)' in (C/'round8_before.txt').read_text()
for name in ('run_checks9','build_patches9','gate_integration9','docs9','archive_command9','profile_rerun','torch_versions3','cache_cost3'):
    assert (C/(name+'.txt')).read_text().strip() in report,name
for name in ('lock_round3','operator_round3','public','read_cache','read_journal','round1','round2','round3'):
    filename='applied_'+name+'.txt'
    assert (C/'round7'/filename).read_bytes()==(B/'checks'/filename).read_bytes()
    assert not (C/filename).exists()
assert 'sys.executable' not in (O/'kit_parity50/run.py').read_text()
assert 'interpreter outside bwrap' not in readme
assert 'ab0123456789' not in (O/'kit_parity50/config.example.json').read_text()
assert readme.index('--enable-extensions gate')<readme.index('--bwlimit=8000')<readme.index('salloc --account')
assert 'Raw writes restored between boundaries' in readme and 'Models must remain frozen' in readme
stamp=subprocess.check_output(['date','-u'],text=True).strip()
assert datetime.now(timezone.utc)<datetime(2026,11,19,19,38,16,tzinfo=timezone.utc)
size=int(subprocess.check_output(['du','-sb',str(L)],text=True).split()[0]);assert size<3_000_000_000,size
receipt=dict(passed=True,utc=stamp,manifest_sha256=sha(O/'patches/MANIFEST.json'),report_sha256=sha(O/'REPORT.md'),note_sha256=sha(O/'NOTE_FOR_CONT_OPS.md'),
    backup_verified=True,workspace_tests=workspace,fresh_application_tests=applied,baseline_controls=len(controls),
    round9_expected_assertion_failures=11,workspace_bytes_before_seal=size,
    workspace_original_files_verified=len(originals),applied_original_files_verified=len(m['base_pin']['inventory']),
    base_sha256=m['base_pin']['sha256'],a4_payload_pin=m['a4_payload_pin'],default_export=export,
    runtime_prerequisites=missing['rows'],production_gpu_gate_run=False,
    patches={name:sha(O/'patches'/name) for name in m['patches']},
    documents={name:sha(O/name) for name in ('REPORT.md','NOTE_FOR_CONT_OPS.md','FRAMEWORK_EVIDENCE.md','kit_parity50/README.md')},
    checks={str(p.relative_to(O)):sha(p) for p in sorted(C.rglob('*')) if p.is_file() and p.name not in ('FINAL_INTEGRITY.json','integrity9.txt')})
(C/'FINAL_INTEGRITY.json').write_text(json.dumps(receipt,sort_keys=True,indent=2)+'\n')
size=int(subprocess.check_output(['du','-sb',str(L)],text=True).split()[0]);assert size<3_000_000_000,size
(L/'work/STATUS.md').write_text(stamp+f'''
VERDICT: DONE — round-9 fixes and delivery are complete.
{workspace} workspace tests and {applied} fresh-application tests pass. All 13 fail-before controls reran; all 11 round-9 tests fail before and pass after.
A4 runtime staging, namespace/wrapper commands, J.environment, production guard self-test, failed ue.json persistence, submit evidence, pre-allocation transfer and exact extraction commands are covered.
Five patches apply with zero fuzz; original reader files and OFF output bytes remain unchanged. CPU ON equality passes; H100 byte equality remains required and unrun.
All 13 runtime parts plus bwrap are pinned and listed as exact Orchard prerequisites, absent from supplied files. No dependency on the reference workspace remains.
REPORT/NOTE contain Review round 9 and exact outputs. MANIFEST and FINAL_INTEGRITY seal the delivery. out_round9 is unchanged; eight round-7 logs are labelled.
Workspace after seal: {size:,} unique-inode bytes. No Git, SSH, SCP, Slurm, GPU, paid API, input edit or deletion command ran.
Completed before 19:38:16 UTC.
''')
print('PASS: immutable out_round9 snapshot, five patches, 40 extension files and all delivery hashes verified.')
print('PASS:',workspace,'workspace tests;',applied,'fresh-application tests; 13 fail-before controls; 11 expected round-9 failures.')
print('PASS: original/OFF bytes unchanged; namespace wrapper, guard/self-test evidence and step-400 binding verified; H100 gate unrun.')
print('Workspace unique-inode bytes:',size,'Completed:',stamp,'Deadline: Thu Nov 19 19:38:16 UTC 2026')
