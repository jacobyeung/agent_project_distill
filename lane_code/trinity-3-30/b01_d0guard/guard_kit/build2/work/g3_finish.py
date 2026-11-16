"""Verify and document the G3 package without accessing operator run directories."""
from pathlib import Path
import datetime,hashlib,json,os,subprocess,sys,tarfile
B=Path(__file__).resolve().parents[1];O=B/'out';K=O/'guard_kit'
sys.path.insert(0,str(K))
from guard_core import read,write,sha
from transport import regular_tar

baseline=read(B/'work/G3_BASELINE.json');family=read(O/'FAMILY.json')
tests=read(O/'TESTS.json');mutants=read(O/'MUTANTS.json');seal=read(O/'G3_SEAL.json')
assert tests['build_round']=='G3' and tests['status']=='PASS'
assert {s['name'] for s in tests['suites']}=={s['name'] for s in baseline['tests']['suites']}
assert all(s['status']=='PASS' and s['returncode']==0 and s['failures']==s['errors']==0 for s in tests['suites'])
assert tests['tests']==sum(s['tests'] for s in tests['suites'])
assert tests['family_sha256']==sha(O/'FAMILY.json')
assert tests['admission_sha256']==sha(K/'admission.py')
assert mutants['complete'] and mutants['total']==mutants['killed']==25
assert tests['mutants_returncode']==0
expected_family=dict(baseline['family'],code_pins=family['code_pins'],
    blockers=[x for x in baseline['family']['blockers'] if x!='Whole-worker CPU namespace run has not completed.'])
assert family==expected_family and family['release_ready'] is False and family['blockers']
for name,expected in family['code_pins'].items():assert sha(K/name)==expected,name
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
assert seal['changed_production_members']==['admission.py']
for name,expected in baseline['operator_files'].items():assert sha(B/name)==expected,name
assert read(O/'INPUT_MANIFEST.json')==baseline['input_manifest']
assert read(O/'SOURCE_IDENTITY.json')['all_equal']
assert read(O/'RESTORATION_TEST.json')['status']=='PASS'
meta=read(O/'candidate_m50/CLOSURE.json')
assert sha(O/'candidate_m50/metadata.tar')==meta['archive']['sha256']==baseline['audit']['metadata_sha256']
report_sha=sha(B.parent/'report/guard_read.py')
assert report_sha==baseline['audit']['report_sha256']

checked=[]
paths=[K/name for name in family['code_pins'] if name.endswith('.py')]
for root in (B/'work',O/'tests',O/'rehearsal'):paths.extend(root.glob('*.py'))
for path in sorted(paths):
    compile(path.read_text(),str(path),'exec');checked.append(str(path.relative_to(B)))
packet_test=read(O/'PACKET_TEST.json');batch=Path(packet_test['packet'])/'BATCH.sh'
for path in (batch,O/'rehearsal/run_whole_worker.sh'):
    subprocess.run(['/bin/bash','-n',str(path)],check=True)
source=batch.read_text().split("<<'G2_PY'\n",1)[1].rsplit('\nG2_PY',1)[0]
compile(source,str(batch),'exec')
write(O/'SYNTAX.json',dict(status='PASS',build_round='G3',python_files=len(checked),files=checked,
      batch=str(batch),batch_sha256=sha(batch),protected_rehearsal_directory_accessed=False))
assert packet_test['status']=='PASS' and packet_test['production_authority'] is False
packet_family=read(Path(packet_test['packet'])/'FAMILY.json') if (Path(packet_test['packet'])/'FAMILY.json').is_file() else None
# The emitted packet stores its family inside p.tar; inspect that exact payload.
with tarfile.open(Path(packet_test['packet'])/'p.tar') as stream:
    packet_family=json.load(stream.extractfile('FAMILY.json'))
assert packet_family['code_pins']==family['code_pins']
pins=read(O/'PIN_CLASSIFICATION.json')
assert [row['number'] for row in pins]==list(range(1,47))
for row in pins:
    filename,number=row['enforcement'].rsplit(':',1)
    assert 0<int(number)<=len((B/filename).read_text().splitlines())
blockers=read(O/'RELEASE_BLOCKERS.json');by_id={row['id']:row for row in blockers['blockers']}
operator=read(O/'rehearsal/OPERATOR_EVIDENCE_G3.json')
assert by_id['whole_worker']['status']=='CLOSED' and by_id['whole_worker']['scope']=='CPU fixture only'
assert by_id['whole_worker']['evidence']==operator['result']
assert by_id['naming']['status']=='OPEN' and blockers['production_packet_authorized'] is False

# Measure only this build's accessible files; prune the protected subtree before descent.
count=0;size=0
for root,dirs,files in os.walk(B,followlinks=False):
    if Path(root)==O/'rehearsal':dirs[:]=[name for name in dirs if name!='whole']
    for name in files:
        path=Path(root)/name
        if not path.is_symlink():count+=1;size+=path.stat().st_size
assert size<6_000_000_000
write(O/'BUILD_SIZE_G3.json',dict(bytes=size,files=count,limit_bytes=6_000_000_000,
      scope='Build files excluding out/rehearsal/whole/; total including protected operator files is unmeasured.',
      protected_directory_accessed=False,measured_scope_within_cap=True))
now=datetime.datetime.now(datetime.timezone.utc)
start=datetime.datetime.fromisoformat(baseline['start_utc'])
assert now<datetime.datetime.fromisoformat(baseline['deadline_utc'])
write(B/'work/TIMING_G3.json',dict(start_utc=baseline['start_utc'],end_utc=now.isoformat(),
      deadline_utc=baseline['deadline_utc'],elapsed_seconds=(now-start).total_seconds(),within_deadline=True))
code=read(O/'CODE_MANIFEST.json');inputs=read(O/'INPUT_MANIFEST.json')
audit=dict(status='PASS_FOR_PACKAGE_INTEGRITY_ONLY',build_round='G3',release_ready=False,
    code_sha256=code['sha256'],inputs_sha256=inputs['sha256'],family_sha256=sha(O/'FAMILY.json'),
    metadata_sha256=meta['archive']['sha256'],report_sha256=report_sha,
    code_pins_verified=True,input_pins_verified=True,archive_members_verified=True,
    original_production_inventory_preserved=True,rehearsal_and_backup_files_excluded=True,
    operator_harness_files_unchanged=True,pin_table_rows=len(pins),tests=tests['tests'],report_mutants=mutants['killed'],
    whole_worker_executed=True,whole_worker_executed_by_g3=False,whole_worker_scope='CPU fixture only',
    whole_worker_evidence=operator['result'],whole_worker_evidence_source='Operator report; protected directory not accessed',
    real_tensors_validated=False,gpu_parity_validated=False,token_identity_validated=False,production_authorized=False)
write(O/'FINAL_AUDIT.json',audit)
(O/'GUARD_KIT_READY.md').write_text(f'''# Guard-read kit: G3 sealed; production NOT READY

The package passes integrity verification and all {tests['tests']} tests (`FINAL_AUDIT.json`, `TESTS.json`). All {mutants['killed']}/{mutants['total']} report mutants are detected (`MUTANTS.json`). Packet tests bind the refreshed family and code pins (`PACKET_TEST.json`, `ALL_STEPS_TEST.json`). Production launch remains blocked by naming, independent review and milestone authority (`RELEASE_BLOCKERS.json`, `FAMILY.json`).

The native merge compares per-key canonical-JSON digests, so tuple/list representations with equal contents admit. A changed score refuses and writes `MERGE_DIFF.json`; missing keys refuse. Matching rows still undergo the request, denominator, parity, score and geometry checks. The merge uses the journal rows after comparison (`guard_kit/admission.py:14`, `G2_TESTS.json`).

The code tar retains the original production member inventory. Only `admission.py` changes; rehearsal-only mount splitting, torchvision and argument forwarding, plus operator backup files, stay outside the tar (`G3_SEAL.json`, `CODE_MANIFEST.json`). The input archive, inherited backend, reviewed stager and report retain their hashes (`INPUT_MANIFEST.json`, `SOURCE_IDENTITY.json`, `FINAL_AUDIT.json`).

The whole-worker blocker is CLOSED for the CPU fixture on operator-supplied evidence: `rehearsal/whole/31f44f39c63b4d68be53660ff5780980/RESULT.json`. The proof passes 20/20; the report correctly refuses the 20-item fixture with return code 3 (`rehearsal/OPERATOR_EVIDENCE_G3.json`). G3 neither accesses that protected directory nor reruns the namespace worker. The fixture cannot establish real tensors, GPU parity or token identity. Production cloud staging and allocation remain unvalidated (`rehearsal/RUNBOOK.md`).

The real candidate metadata passes config identity, preparation, source seals, initialization-chain and unchanged restoration checks (`CLOSURE_ADMISSION.json`, `RESTORATION_TEST.json`). Those metadata results do not establish actual candidate tensor restoration.

Runtime naming remains blocked as written in `RELEASE_BLOCKERS.json`. The seven names sit inside the sealed trainer tree b01ce449, the same tree job 170056 and D0's training job already staged on Orchard; ORCH decides (`NAMING_CONFLICT.json`; operator context in `RELEASE_BLOCKERS.json`). The neutral outer archive round-trips to identical file bytes, but runtime projections remain unintegrated (`NAME_ROUNDTRIP.json`, `NAMING.json`).

| Artifact | SHA256 | Evidence |
|---|---|---|
| `code_g2.tar` | `{code['sha256']}` | `CODE_MANIFEST.json` |
| `inputs_g2.tar` | `{inputs['sha256']}` | `INPUT_MANIFEST.json` |
| `FAMILY.json` | `{audit['family_sha256']}` | `FINAL_AUDIT.json` |
| `candidate_m50/metadata.tar` | `{meta['archive']['sha256']}` | `candidate_m50/CLOSURE.json` |
| Unchanged report | `{report_sha}` | `FINAL_AUDIT.json` |

Reproduce this seal from the build directory with `/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B`: run `work/family.py`, `work/run_g3_tests.py`, `work/seal.py --g3`, `work/g3_docs.py`, then `work/finish.py --g3`, under `nice -n 10` with numerical-library threads set to one. The operator rehearsal command and overlay are in `rehearsal/RUNBOOK.md`.

`DIFF.md` gives current admission line ranges; `G3_ADMISSION.patch` isolates the merge change. `PIN_CLASSIFICATION.md` covers the contract checks. `RUN.md` gives production preparation and authority commands. Remote commands remain unexecuted.

Not checked: real tensors, GPU parity, token identity, production Orchard/GCS/pool/credentials, the namespace proof-mismatch variant, and complete runtime naming. Local size excluding protected operator runs is in `BUILD_SIZE_G3.json`; G3 timing is in `../work/TIMING_G3.json`.
''')
event=B/'events'/(now.strftime('%Y%m%dT%H%MZ')+'_RESULT_g3.md')
lines=[
    'RESULT: G3 SEALED; package checks PASS; production remains NOT_READY.',
    'Canonical-JSON merge admits tuple/list equality and keeps journal rows; changed scores and missing keys refuse (out/G3_ADMISSION.patch).',
    'Real mismatches write MERGE_DIFF.json; absent-versus-null field diagnostics are covered (out/G2_TESTS.json).',
    f"All {tests['tests']} tests pass across the registered suites (out/TESTS.json); all {mutants['killed']}/{mutants['total']} report mutants are detected (out/MUTANTS.json).",
    'Packet tests pass with refreshed code pins; production authority remains absent (out/PACKET_TEST.json; out/ALL_STEPS_TEST.json).',
    'The production member inventory is unchanged; only admission.py differs; rehearsal files and operator backups are excluded (out/G3_SEAL.json).',
    f"Code SHA256: {code['sha256']} (out/code_g2.tar; out/CODE_MANIFEST.json).",
    f"Family SHA256: {audit['family_sha256']} (out/FAMILY.json; out/FINAL_AUDIT.json).",
    'The whole_worker blocker is CLOSED for the CPU fixture only, using the operator-supplied pass (out/RELEASE_BLOCKERS.json; out/rehearsal/OPERATOR_EVIDENCE_G3.json).',
    'Operator evidence: out/rehearsal/whole/31f44f39c63b4d68be53660ff5780980/RESULT.json; proof 20/20 and expected report refusal rc 3 for the 20-item fixture.',
    'G3 did not access out/rehearsal/whole/ or rerun the namespace worker. The fixture cannot establish real tensors, GPU parity or token identity (out/rehearsal/RUNBOOK.md).',
    "Naming remains open: the seven names are inside trainer tree b01ce449 already staged by job 170056 and D0 training; ORCH decides (out/RELEASE_BLOCKERS.json; out/NAMING_CONFLICT.json).",
    'Not checked: real production tensors/runtime, GPU parity/token identity, live Orchard/GCS/pool/credentials, namespace mismatch variant, complete naming (out/GUARD_KIT_READY.md).',
    'Source differences, operator command, overlay and current hashes are documented (out/DIFF.md; out/rehearsal/RUNBOOK.md; out/GUARD_KIT_READY.md).',
    'Integrity, measured local size excluding protected runs, and timing are recorded (out/FINAL_AUDIT.json; out/BUILD_SIZE_G3.json; work/TIMING_G3.json).',
]
assert len(lines)<=30;event.write_text('\n'.join(lines)+'\n')
(B/'STATUS.md').write_text('G3 is complete: the package is sealed and all checks pass; production remains NOT_READY.\n'
    f"All {tests['tests']} tests and {mutants['killed']}/{mutants['total']} mutants pass (out/TESTS.json; out/MUTANTS.json).\n"
    'The code archive preserves its member inventory and excludes rehearsal files and operator backups (out/G3_SEAL.json).\n'
    'The CPU-fixture blocker is CLOSED on operator-supplied evidence; out/rehearsal/whole/ was not accessed.\n'
    'Naming remains open for ORCH; real tensors, GPU parity, token identity and production authority remain unproven (out/RELEASE_BLOCKERS.json).\n'
    'Hashes and integrity checks are in out/GUARD_KIT_READY.md and out/FINAL_AUDIT.json.\n'
    'Final result: '+str(event.relative_to(B))+'\n')
print(json.dumps(dict(result=str(event.relative_to(B)),status='G3_SEALED_PRODUCTION_NOT_READY',tests=tests['tests'],mutants=mutants['killed'],code_sha256=code['sha256'])))
