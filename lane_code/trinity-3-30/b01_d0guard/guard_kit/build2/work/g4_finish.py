"""Audit the G4 seal and write the operator result without traversing protected runs."""
from pathlib import Path
import ast
import datetime
import hashlib
import json
import os
import re
import subprocess
import sys
import tarfile
B=Path(__file__).resolve().parents[1];O=B/'out';K=O/'guard_kit'
sys.path.insert(0,str(K))
from guard_core import read,write,sha
from transport import regular_tar
from worker import REPORT_SHA256

baseline=read(B/'work/G4_BASELINE.json');family=read(O/'FAMILY.json')
tests=read(O/'TESTS.json');mutants=read(O/'MUTANTS.json');seal=read(O/'G4_SEAL.json')
assert tests['build_round']=='G4'
assert {s['name'] for s in tests['suites']}=={s['name'] for s in baseline['tests']['suites']}|{'G4'}
assert tests['tests']==sum(s['tests'] for s in tests['suites'])
assert tests['family_sha256']==sha(O/'FAMILY.json')
assert tests['admission_sha256']==sha(K/'admission.py')
assert mutants['complete'] and mutants['total']==mutants['killed'] and tests['mutants_returncode']==0
changed_pins=[name for name,pin in family['code_pins'].items() if baseline['family']['code_pins'][name]!=pin]
assert changed_pins==['transport.py','worker.py']
expected_family=dict(baseline['family'],code_pins=family['code_pins'],blockers=baseline['family']['blockers'][1:])
assert family==expected_family and family['release_ready'] is False
fields=['blockers']+['code_pins.'+name for name in changed_pins]
write(O/'FAMILY_CHANGES_G4.json',dict(baseline_sha256=baseline['family_sha256'],
    current_sha256=sha(O/'FAMILY.json'),changed_fields=fields,release_ready_changed=False,
    changes={field:dict(before=baseline['family']['blockers'],after=family['blockers']) if field=='blockers' else
       dict(before=baseline['family']['code_pins'][field[len('code_pins.'):]],after=family['code_pins'][field[len('code_pins.'):]]) for field in fields},
    reason='ORCH 1601Z naming acceptance; G4 fixes 1 and 3 change only coordinator/report binding and receipt verification.'))
for name,pin in family['code_pins'].items():assert sha(K/name)==pin,name
for name,pin in family['inputs'].items():assert sha(O/'inputs'/name)==pin['sha256'],name
for manifest_name,archive_name in [('CODE_MANIFEST.json','code_g2.tar'),('INPUT_MANIFEST.json','inputs_g2.tar')]:
    manifest=read(O/manifest_name);archive=O/archive_name
    assert sha(archive)==manifest['sha256'] and archive.stat().st_size==manifest['bytes']
    regular_tar(archive)
    with tarfile.open(archive) as stream:
        members=stream.getmembers()
        inventory={m.name:dict(bytes=m.size,sha256=hashlib.sha256(stream.extractfile(m).read()).hexdigest()) for m in members}
    assert len(members)==len(inventory) and inventory==manifest['members']
    if archive_name=='code_g2.tar':
        assert {n:v['sha256'] for n,v in inventory.items()}==family['code_pins']
        assert set(inventory)==set(baseline['code_manifest']['members'])
        assert not any('rehearsal' in Path(n).parts or n.endswith('.g2_orig.py') for n in inventory)
assert seal['code_sha256']==sha(O/'code_g2.tar') and seal['family_sha256']==sha(O/'FAMILY.json')
assert seal['changed_production_members']==changed_pins
assert read(O/'INPUT_MANIFEST.json')==baseline['input_manifest']
identity=read(O/'SOURCE_IDENTITY.json')
assert identity['all_equal']
for row in identity['files']:assert sha(B/row['file'])==row['sha256']==row['current_sha256']
assert read(O/'RESTORATION_TEST.json')['status']=='PASS'
meta=read(O/'candidate_m50/CLOSURE.json')
assert sha(O/'candidate_m50/metadata.tar')==meta['archive']['sha256']==baseline['audit']['metadata_sha256']
report_actual=sha(B.parent/'report/guard_read.py')
report_matches=report_actual==REPORT_SHA256
assert tests['report_sha256']==report_actual
assert tests['mutants_report_sha256']==mutants['report_sha256']==report_actual
brief_pin='5424e41c68fc1918386c62865a68d7b3c1af2802f2800b1f0455837568a3cd11'
report_pin=dict(status='PASS' if report_matches else 'BLOCKED',
    report=str(B.parent/'report/guard_read.py'),reviewed_sha256=baseline['audit']['report_sha256'],
    brief_sha256=brief_pin,required_sha256=REPORT_SHA256,observed_sha256=report_actual,
    intentional_post_review_change=True,report_modified_by_g4=False,
    changes=['Candidate artifact required','Step-544 candidate requires explicit self-pair',
             'Fixed seed and draw count','Strict boolean accounting flags'],
    authority=read(B/'work/G4_REPORT_AUTHORITY.json') if (B/'work/G4_REPORT_AUTHORITY.json').exists() else
              dict(source='BRIEF_G5.md',decision='The operator authorizes the final report source pin.'))
write(O/'REPORT_PIN_G4.json',report_pin)
if report_matches:
    assert tests['status']=='PASS'
    assert all(s['status']=='PASS' and s['returncode']==0 and s['failures']==s['errors']==0 for s in tests['suites'])
else:
    assert all(s['status']=='PASS' for s in tests['suites'] if s['name'] not in ('report','G4'))

checked=[]
paths=[K/name for name in family['code_pins'] if name.endswith('.py')]
for root in (B/'work',O/'tests',O/'rehearsal',O/'operator'):paths.extend(root.glob('*.py'))
for path in sorted(paths):
    compile(path.read_text(),str(path),'exec');checked.append(str(path.relative_to(B)))
packet_test=read(O/'PACKET_TEST.json');batch=Path(packet_test['packet'])/'BATCH.sh'
shells=re.findall(r'```sh\n(.*?)```',(O/'RUN.md').read_text(),re.S)
shell_path=B/'work/RUN_G4_SYNTAX.sh';shell_path.write_text('\n'.join(shells))
for path in (batch,O/'rehearsal/run_whole_worker.sh',shell_path):subprocess.run(['/bin/bash','-n',str(path)],check=True)
source=batch.read_text().split("<<'G2_PY'\n",1)[1].rsplit('\nG2_PY',1)[0]
compile(source,str(batch),'exec')
write(O/'SYNTAX.json',dict(status='PASS',build_round='G4',python_files=len(checked),files=checked,
    batch=str(batch),batch_sha256=sha(batch),run_sheet_shell=str(shell_path)))
assert packet_test['status']=='PASS' and packet_test['production_authority'] is False
with tarfile.open(Path(packet_test['packet'])/'p.tar') as stream:packet_family=json.load(stream.extractfile('FAMILY.json'))
assert packet_family['code_pins']==family['code_pins']
pins=read(O/'PIN_CLASSIFICATION.json');assert [row['number'] for row in pins]==list(range(1,47))
for row in pins:
    filename,number=row['enforcement'].rsplit(':',1)
    assert 0<int(number)<=len((B/filename).read_text().splitlines())
blockers=read(O/'RELEASE_BLOCKERS.json');by_id={row['id']:row for row in blockers['blockers']}
assert by_id['naming']['status']=='ACCEPTED' and by_id['whole_worker']['status']=='CLOSED'
for row in blockers['review_fixes']:
    if row['id']==1:
        row['status']='FIXED' if report_matches else 'BLOCKED_REPORT_PIN'
        row['description']='Every report call binds the CONFIG artifact and authorized report source.' if report_matches else 'Report invocation changes are implemented; the report source differs from the required pin.'
blockers['report_source_pin']=report_pin
write(O/'RELEASE_BLOCKERS.json',blockers)
count=0;size=0
for root,dirs,files in os.walk(B,followlinks=False):
    if Path(root)==O/'rehearsal':dirs[:]=[name for name in dirs if name!='whole']
    for name in files:
        path=Path(root)/name
        if not path.is_symlink():count+=1;size+=path.stat().st_size
assert size<6_000_000_000
write(O/'BUILD_SIZE_G4.json',dict(bytes=size,files=count,limit_bytes=6_000_000_000,measured_scope_within_cap=True,
    scope='Build files excluding out/rehearsal/whole/; protected operator files were not inventoried.'))
now=datetime.datetime.now(datetime.timezone.utc);timing=read(B/'work/TIMING_G4.json')
start=datetime.datetime.fromisoformat(timing['start_utc'])
assert now<datetime.datetime.fromisoformat(timing['deadline_utc'])
timing.update(end_utc=now.isoformat(),elapsed_seconds=(now-start).total_seconds(),within_deadline=True)
write(B/'work/TIMING_G4.json',timing)
code=read(O/'CODE_MANIFEST.json');inputs=read(O/'INPUT_MANIFEST.json')
audit=dict(status='PASS_FOR_PACKAGE_INTEGRITY_ONLY' if report_matches else 'BLOCKED_REPORT_SOURCE_PIN',build_round='G4',
    release_ready=False,production_authorized=False,code_sha256=code['sha256'],inputs_sha256=inputs['sha256'],
    family_sha256=sha(O/'FAMILY.json'),family_changed_fields=fields,metadata_sha256=meta['archive']['sha256'],
    report_sha256=REPORT_SHA256,report_observed_sha256=report_actual,report_pin_matches=report_matches,
    report_post_review_change='Intentional operator change; see REPORT_PIN_G4.json',
    code_pins_verified=True,input_pins_verified=True,archive_members_verified=True,
    operator_transfer_sha256=sha(O/'operator/governed_transfer.py'),run_sheet_sha256=sha(O/'RUN.md'),
    diff_c8r_patch_sha256=sha(O/'DIFF_C8R.patch'),
    rehearsal_harness_sha256={name:sha(O/'rehearsal'/name) for name in ('prepare_whole.py','run_whole_worker.py','run_records.py')},
    original_production_inventory_preserved=True,rehearsal_and_backup_files_excluded=True,
    pin_table_rows=len(pins),tests=tests['tests'],tests_status=tests['status'],report_mutants=mutants['killed'],
    real_tensors_validated=False,gpu_parity_validated=False,token_identity_validated=False,
    whole_worker_executed_by_g4=False,whole_worker_scope='Operator-supplied G3 CPU fixture only; G4 uses separate receipt fixtures.',
    protected_run_writes=False,protected_run_read_incident='One rg exclusion failed and returned matching lines from existing RESULT.json files; no run files were modified.',
    live_governor_executed=False,network_ssh_gpu_git_agents_deletion_used=False)
write(O/'FINAL_AUDIT.json',audit)
summary='G4 review fixes are sealed; all checks pass.' if report_matches else 'G4 is sealed with the report source pin unresolved.'
(O/'GUARD_KIT_READY.md').write_text(f'''# Guard-read kit: G4 sealed; production authority required

{summary} The suites ran {tests['tests']} tests with status {tests['status']} (`TESTS.json`). All {mutants['killed']}/{mutants['total']} report mutants are detected (`MUTANTS.json`). Package hashes and exact checks are in `FINAL_AUDIT.json`.

Every report call supplies the CONFIG candidate artifact. The coordinator copies candidate stage/checker receipts before checkpoint execution, returns any existing step-544 equivalents, and records their exact bytes in `STAGE_RECEIPTS.json`. Return verification rejects missing or changed evidence (`G4_TESTS.json`, `G4_RETURN_EVIDENCE.json`).

`DIFF.md`, `DIFF_C8R.patch` and `DIFF_C8R.json` cover every production addition against sealed C8r. The production member inventory is unchanged; only `worker.py` and `transport.py` differ from the reviewed G3 tar. All inherited C8r files and reviewed stager dependencies retain their bytes (`G4_SEAL.json`, `SOURCE_IDENTITY.json`).

All run-sheet fetches and the packet upload use the stopped-root serial governor wrapper. It registers with tier 3, allow-resume and IO weight 1, waits for running in STATE.md, preserves its root identity, and closes the stream record. No live transfer was executed (`RUN.md`, `operator/governed_transfer.py`, `G4_TESTS.json`).

The seven trainer-tree names are ACCEPTED by ORCH 1601Z. The CPU-fixture blocker is CLOSED on operator-supplied evidence. A current FAMILY-bound independent review, completed candidate closure/export and exact ORCH GO remain required. The family retains `release_ready: false` (`RELEASE_BLOCKERS.json`).

FAMILY differs from `{baseline['family_sha256']}` only in `blockers`, `code_pins.transport.py` and `code_pins.worker.py`. The blocker change removes the accepted naming condition; the code pins bind the receipt and report-call fixes. `release_ready` and all other fields remain unchanged (`FAMILY_CHANGES_G4.json`).

| Artifact | SHA256 |
|---|---|
| `code_g2.tar` | `{code['sha256']}` |
| `inputs_g2.tar` | `{inputs['sha256']}` |
| `FAMILY.json` | `{audit['family_sha256']}` |
| `candidate_m50/metadata.tar` | `{meta['archive']['sha256']}` |
| Required report | `{REPORT_SHA256}` |
| Observed report | `{report_actual}` |

The report pin is an intentional post-review change. Its authorization and observed bytes are recorded in `REPORT_PIN_G4.json`; G4 does not edit the external report.

Reproduce with `/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B`, `nice -n 10` and numerical-library threads set to one: `work/family.py --g4`, `work/seal.py --g4`, `work/g4_diff.py`, `work/run_g4_tests.py`, then `work/finish.py --g4`.

Not checked: real tensors, GPU parity, token identity, the namespace worker, live Orchard/GCS/pool/credentials or governor transfers. The receipt rehearsal uses phase stand-ins outside the protected operator runs. One search exclusion failed and read matching RESULT lines under the protected directory; no files there were modified (`FINAL_AUDIT.json`). Build size and elapsed time are in `BUILD_SIZE_G4.json` and `../work/TIMING_G4.json`.
''')
event=B/'events'/(now.strftime('%Y%m%dT%H%MZ')+'_RESULT_g4.md')
lines=[
    'RESULT: '+('G4 SEALED; review fixes 1–4 PASS; production authority remains required.' if report_matches else 'G4 PARTIAL: fixes 2–4 pass; fix 1 awaits the correct report source pin.'),
    f"All suites ran {tests['tests']} tests: {tests['status']} (out/TESTS.json); mutants {mutants['killed']}/{mutants['total']} detected (out/MUTANTS.json).",
    'Report commands bind CONFIG.artifact_sha256; the external report was not edited (out/REPORT_PIN_G4.json).',
    'The C8r table and patch cover every production addition against code_c8r.tar f4535bc0 (out/DIFF.md; out/DIFF_C8R.json).',
    'Candidate stage/checker receipts are copied before checkpoints; omissions fail return verification (out/G4_TESTS.json; out/G4_RETURN_EVIDENCE.json).',
    'Every documented fetch and packet upload uses the stopped, registered serial-governor pipeline (out/RUN.md; out/operator/governed_transfer.py).',
    'The seven trainer-tree names are ACCEPTED by ORCH 1601Z; CPU-fixture closure remains recorded (out/RELEASE_BLOCKERS.json).',
    'FAMILY fields changed: blockers, code_pins.transport.py, code_pins.worker.py; release_ready remains false (out/FAMILY_CHANGES_G4.json).',
    f"Code SHA256: {code['sha256']} (out/CODE_MANIFEST.json).",
    f"Family SHA256: {audit['family_sha256']} (out/FINAL_AUDIT.json).",
    f"Required report SHA256: {REPORT_SHA256} (out/REPORT_PIN_G4.json).",
    f"Observed report SHA256: {report_actual} (out/REPORT_PIN_G4.json).",
    'Current-family review and milestone-specific closure/export/ORCH GO remain required (out/RELEASE_BLOCKERS.json).',
    'No protected run files were modified; one failed search exclusion read matching RESULT lines (out/FINAL_AUDIT.json).',
    'Not checked: real tensors, GPU parity/token identity, namespace worker or live Orchard/GCS/pool/governor (out/FINAL_AUDIT.json).',
    'The explicit post-review hash history is retained because the G4 task requires it (out/REPORT_PIN_G4.json).',
    'Build size and timing: out/BUILD_SIZE_G4.json; work/TIMING_G4.json. Evidence index: out/GUARD_KIT_READY.md.',
]
assert len(lines)<=30;event.write_text('\n'.join(lines)+'\n')
(B/'STATUS.md').write_text(summary+'\n'+
    f"Tests: {tests['status']} ({tests['tests']}); mutants: {mutants['killed']}/{mutants['total']} (out/TESTS.json; out/MUTANTS.json).\n"+
    'Naming: ACCEPTED by ORCH 1601Z. Production authority remains required (out/RELEASE_BLOCKERS.json).\n'+
    'FAMILY changes and hashes are audited in out/FAMILY_CHANGES_G4.json and out/FINAL_AUDIT.json.\n'+
    'Final result: '+str(event.relative_to(B))+'\n')
print(json.dumps(dict(result=str(event.relative_to(B)),status=audit['status'],tests=tests['status'],report_matches=report_matches)))
