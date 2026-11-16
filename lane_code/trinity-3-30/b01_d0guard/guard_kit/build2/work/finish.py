from pathlib import Path
import datetime
import hashlib
import json
import sys
import tarfile
if '--g5' in sys.argv:
    import runpy
    runpy.run_path(str(Path(__file__).with_name('g5_finish.py')),run_name='__main__')
    raise SystemExit(0)
if '--g4' in sys.argv:
    import runpy
    runpy.run_path(str(Path(__file__).with_name('g4_finish.py')),run_name='__main__')
    raise SystemExit(0)
if '--g3' in sys.argv:
    import runpy
    runpy.run_path(str(Path(__file__).with_name('g3_finish.py')),run_name='__main__')
    raise SystemExit(0)

B=Path(__file__).resolve().parents[1];O=B/'out';K=O/'guard_kit'
sys.path.insert(0,str(K))
from guard_core import read,write,sha
from transport import regular_tar

family=read(O/'FAMILY.json');tests=read(O/'TESTS.json');mutants=read(O/'MUTANTS.json')
assert tests['status']=='PASS' and mutants['complete'] and mutants['total']==mutants['killed']
assert family['release_ready'] is False and family['blockers']
for name,expected in family['code_pins'].items():
    assert sha(K/name)==expected,name
for name,pin in family['inputs'].items():
    assert sha(O/'inputs'/name)==pin['sha256'],name
for manifest_name,archive_name in [('CODE_MANIFEST.json','code_g2.tar'),('INPUT_MANIFEST.json','inputs_g2.tar')]:
    manifest=read(O/manifest_name);archive=O/archive_name
    assert sha(archive)==manifest['sha256'] and archive.stat().st_size==manifest['bytes']
    regular_tar(archive)
    with tarfile.open(archive) as stream:
        inventory={m.name:dict(bytes=m.size,sha256=hashlib.sha256(stream.extractfile(m).read()).hexdigest()) for m in stream}
    assert inventory==manifest['members']
    if archive_name=='code_g2.tar':assert {n:v['sha256'] for n,v in inventory.items()}==family['code_pins']
assert read(O/'SOURCE_IDENTITY.json')['all_equal']
assert read(O/'SYNTAX.json')['status']=='PASS'
assert read(O/'RESTORATION_TEST.json')['status']=='PASS'
assert read(O/'rehearsal/whole/INPUT_PATHS.json')['status']=='PASS'
pins=read(O/'PIN_CLASSIFICATION.json');assert [r['number'] for r in pins]==list(range(1,47))
for row in pins:
    filename,number=row['enforcement'].rsplit(':',1)
    assert 0<int(number)<=len((B/filename).read_text().splitlines())
report=B.parent/'report/guard_read.py'
report_sha='5424e41c68fc1918386c62865a68d7b3c1af2802f2800b1f0455837568a3cd11'
assert sha(report)==report_sha
now=datetime.datetime.now(datetime.timezone.utc)
timing=read(B/'work/TIMING.json')
start=datetime.datetime.fromisoformat(timing['start_utc'].replace('Z','+00:00'))
deadline=datetime.datetime.fromisoformat(timing['deadline_utc'].replace('Z','+00:00'))
assert now<deadline
timing.update(end_utc=now.isoformat(),elapsed_seconds=(now-start).total_seconds(),within_deadline=True)
write(B/'work/TIMING.json',timing)
code=read(O/'CODE_MANIFEST.json');inputs=read(O/'INPUT_MANIFEST.json');meta=read(O/'candidate_m50/CLOSURE.json')
audit=dict(status='PASS_FOR_PACKAGE_INTEGRITY_ONLY',release_ready=False,
    code_sha256=code['sha256'],inputs_sha256=inputs['sha256'],family_sha256=sha(O/'FAMILY.json'),
    metadata_sha256=meta['archive']['sha256'],report_sha256=report_sha,
    code_pins_verified=True,input_pins_verified=True,archive_members_verified=True,
    pin_table_rows=len(pins),tests=tests['tests'],report_mutants=mutants['killed'],
    whole_worker_executed=False,production_authorized=False)
write(O/'FINAL_AUDIT.json',audit)
(O/'GUARD_KIT_READY.md').write_text(f'''# Guard-read kit: NOT READY

The package contains candidate closure admission, production packet and worker code, and an operator rehearsal command. It is not ready to submit. Runtime naming remains incomplete, and the whole-worker path has not run (`RELEASE_BLOCKERS.json`). The delivered family rejects production packet emission; unit tests use explicitly fabricated authority (`FAMILY.json`, `PACKET_TEST.json`).

The real candidate metadata passes config-identity, preparation, source-seal, initialization-chain and unchanged restoration checks (`CLOSURE_ADMISSION.json`, `RESTORATION_TEST.json`). The export must match the selected closure artifact byte-for-byte before candidate execution (`guard_kit/staging.py`, `guard_kit/closure.py`). The actual candidate tensors were not supplied or loaded.

The coordinator stages both exports, launches fresh checkpoint processes, publishes proof and canary receipts before continuing, and returns a merged native-only bundle with in-job admission (`guard_kit/worker.py`, `guard_kit/checkpoint.py`, `guard_kit/admission.py`). Component tests verify authority refusals, milestone packet emission, subprocess isolation, receipt ordering and failure returns. They do not establish a production run.

The executed suites pass {tests['tests']} checks (`TESTS.json`), and all {mutants['killed']} report mutants are detected (`MUTANTS.json`). The inherited backend and reviewed stager remain byte-identical (`SOURCE_IDENTITY.json`). The report remains unchanged (`FINAL_AUDIT.json`).

Run the operator rehearsal with `out/rehearsal/run_whole_worker.sh`, from this build directory, outside the sandbox. The sandbox attempt stopped at the namespace netlink refusal (`rehearsal/whole/sandbox/RESULT.json`). The command shares the production phase coordinator but retains fixture staging and allocation boundaries; it does not yet constitute a transport-only full-packet rehearsal (`rehearsal/RUNBOOK.md`).

Runtime naming is still blocked. The neutral outer metadata archive round-trips to identical file bytes, but the runtime does not consume the proposed config/item projections (`NAME_ROUNDTRIP.json`, `NAMING.json`). Renaming the prohibited trainer members changes the required source-tree digest even when every content hash stays equal (`NAMING_CONFLICT.json`). A canonical-name adapter remains unimplemented and unreviewed.

| Artifact | SHA256 | Evidence |
|---|---|---|
| `code_g2.tar` | `{code['sha256']}` | `CODE_MANIFEST.json` |
| `inputs_g2.tar` | `{inputs['sha256']}` | `INPUT_MANIFEST.json` |
| `FAMILY.json` | `{audit['family_sha256']}` | `FINAL_AUDIT.json` |
| `candidate_m50/metadata.tar` | `{meta['archive']['sha256']}` | `candidate_m50/CLOSURE.json` |
| Unchanged report | `{report_sha}` | `FINAL_AUDIT.json` |

`DIFF.md` records changed source blocks; `DIFF.patch` gives exact lines. `PIN_CLASSIFICATION.md` covers rows 1–46 with accepted values and implementation references (`PIN_CLASSIFICATION.json`). `RUN.md` gives closure fetch, preparation, packet, submission, return fetch and ledger commands. `SIZING.md` records provisional time and storage estimates. All remote commands remain unexecuted.

Not checked: real tensor restoration, GPU parity and token identity, complete worker execution, Orchard allocation, live GCS generations or credentials, result-pool state, installed operator/governor commands, and complete runtime naming. Independent review and the milestone-specific closure, export and ORCH GO records remain required (`RELEASE_BLOCKERS.json`).
''')
event=B/'events'/(now.strftime('%Y%m%dT%H%MZ')+'_RESULT_final.md');event.parent.mkdir(exist_ok=True)
lines=[
    'RESULT: NOT_READY — tested components are packaged; the requested release is incomplete.',
    '',
    'Candidate metadata admission and unchanged restoration checks pass (out/CLOSURE_ADMISSION.json; out/RESTORATION_TEST.json).',
    'Packet emission, dual-export staging, fresh-process coordination, canary publication, native admission and return code are implemented (out/DIFF.md).',
    f"The executed suites pass {tests['tests']} checks (out/TESTS.json); {mutants['killed']}/{mutants['total']} report mutants are detected (out/MUTANTS.json).",
    'Runtime naming remains open: outer aliases round-trip, but signed metadata and trainer paths retain prohibited names (out/NAMING.json; out/NAMING_CONFLICT.json).',
    'The operator rehearsal command is out/rehearsal/run_whole_worker.sh; its sandbox run stopped at the netlink refusal (out/rehearsal/whole/sandbox/RESULT.json).',
    'The rehearsal shares production coordination but still has fixture staging/allocation boundaries; transport-only full-packet coverage is incomplete (out/rehearsal/RUNBOOK.md).',
    'Production review and per-milestone authority remain absent; the delivered family refuses launch (out/RELEASE_BLOCKERS.json; out/FAMILY.json).',
    f"Code SHA256: {code['sha256']} (out/code_g2.tar; out/CODE_MANIFEST.json).",
    f"Family SHA256: {audit['family_sha256']} (out/FAMILY.json; out/FINAL_AUDIT.json).",
    'The report, inherited backend and reviewed stager remain unchanged (out/FINAL_AUDIT.json; out/SOURCE_IDENTITY.json).',
    'Not checked: real tensors, GPU restoration/parity/token identity, complete worker execution, live Orchard/GCS/pool/credentials, installed ossh/governor, complete naming (out/RELEASE_BLOCKERS.json).',
    'Commands, pin classifications, source differences and sizing are in out/RUN.md, out/PIN_CLASSIFICATION.md, out/DIFF.md and out/SIZING.md.',
    'Local size and build duration are recorded in out/BUILD_SIZE.json and work/TIMING.json; both respect the requested limits.',
    'Read out/GUARD_KIT_READY.md for the package and evidence index.',
]
assert len(lines)<=40;event.write_text('\n'.join(lines)+'\n')
(B/'STATUS.md').write_text('''G2 build finished with status NOT_READY. The requested release is incomplete.
Candidate metadata admission and unchanged restoration checks pass (out/RESTORATION_TEST.json).
Packet and coordinator component tests pass (out/TESTS.json).
Runtime naming remains incomplete; the delivered family refuses production launch (out/RELEASE_BLOCKERS.json).
The operator rehearsal command exists, but its namespace-dependent path has not run and its staging boundaries exceed transport-only substitution (out/rehearsal/RUNBOOK.md).
The package, hashes, evidence and unchecked work are indexed in out/GUARD_KIT_READY.md.
Final result: '''+str(event.relative_to(B))+'\n')
files=[p for p in B.rglob('*') if p.is_file() and not p.is_symlink()]
size=sum(p.stat().st_size for p in files)
assert size<=6_000_000_000
write(O/'BUILD_SIZE.json',dict(bytes=size,files=len(files),limit_bytes=6_000_000_000,within_cap=True,root=str(B)))
print(json.dumps(dict(result=str(event.relative_to(B)),status='NOT_READY',integrity='PASS',bytes=size)))
