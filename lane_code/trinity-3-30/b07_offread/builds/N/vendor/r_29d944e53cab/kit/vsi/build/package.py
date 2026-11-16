"""Build a deterministic tar and an external, non-circular hash/diff inventory."""
from pathlib import Path
import difflib
import hashlib
import io
import json
import tarfile
K=Path(__file__).resolve().parents[1]
P=K.parent/'pull'
origins=json.loads((K/'build/ORIGINS.json').read_text())
files=[]
for directory in ('reader','launcher','cohort','parity','proof','tests'):
    candidates=(K/directory).rglob('*') if directory=='reader' else (K/directory).iterdir()
    for p in candidates:
        if p.name.startswith('_bootstrap_'):continue
        if p.is_file() and p.suffix in ('.py','.json','.jsonl','.sh','.md'):
            files.append(p)
files.extend([K/'build/package.py',K/'build/ORIGINS.json',K/'build/PASS2_FILES.json',K/'build/phase_b_reference.py',K/'build/coverage_report.py',K/'PROOF_JOB.md',K/'proof/LOCAL_LINES.json.gz',K/'proof/coverage.ini'])
files=sorted(files,key=lambda p:str(p.relative_to(K)))
records={}
with tarfile.open(K/'package.tar','w',format=tarfile.USTAR_FORMAT) as tf:
    for p in files:
        raw=p.read_bytes();name=str(p.relative_to(K));m=tarfile.TarInfo(name)
        m.size=len(raw);m.mtime=0;m.uid=m.gid=0;m.uname=m.gname='';m.mode=0o755 if p.suffix=='.sh' else 0o644
        tf.addfile(m,io.BytesIO(raw))
        record=dict(sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw),status='NEW')
        if name in origins:
            old=(P/origins[name]).read_bytes();h=hashlib.sha256(old).hexdigest()
            record.update(status='IDENTICAL' if raw==old else 'CHANGED',accepted_sha256=h,accepted_copy=origins[name])
        records[name]=record
h=hashlib.sha256((K/'package.tar').read_bytes()).hexdigest()
(K/'KIT_SHA256').write_text(h+'  package.tar\n')
(K/'build/PACKAGE_FILES.json').write_text(json.dumps(records,indent=2)+'\n')
text=['# Package inventory and diffs','',
'KIT_SHA256: `'+h+'`','',
'package.tar uses sorted names, mtime 0, uid/gid 0 and empty owner/group names. DIFF.md, REPORT.md, KIT_SHA256 and this build inventory are external sidecars to avoid a circular self-hash. Local environments, caches, test runs, generated media, archives and large accepted result journals are excluded.','',
'## Scope','',
'- Exactly one evaluator file changes: evalpath/kit_inputs.py adds optional sorted question_types and example_ids filters after the full 5,130-row check; proof selection reaches every caller through the same loader. All 35 other evaluator files equal the accepted bound kit inventory. Every caller enters through data.tasks_for; budgets inherit the worker source IDs and merge against the same loader.',
'- evalpath/SOURCE_PINS.json does not pin kit_inputs.py. It records upstream official/trainer provenance and remains identical. New per-bind code inventories authenticate the changed kit; the old CODE_PINS/source archive digest is not falsely reused.',
'- common.py, export_check.py, direct.py and vendor imports are byte-identical. The official adapter does not use the dev label override or PNG store. The unchanged dev wrapper/r3 path remains available for prompt parity.',
'- Launcher preparation replaces lost release/review files with an explicitly new build-integrity record, fixed step/artifact/model pins and the rebuilt transport. It does not invent an ACCEPT review, training receipt or recovered attestation.',
'- orchard_stage retains runtime, camera compatibility package, base, payload, bwrap and generation-pinned GCS export staging. It replaces the PNG pull with 288 sequential, SHA-verified video copies using only the two aliases, plus the pinned questions. Physical video cache filenames are SHA256 values. Dataset paths exist in the private bwrap view under the supplied alias; legacy absolute namespace paths remain necessary for the immutable export and runtime links.',
'- orchard_job retains the H100 checks and local-storage policy, calls reader/chain.py through the accepted vLLM interpreter; proof mode keeps real H100 checks, uses runtime_0 for decoded planning/frame staging, runs 14 official items with AsyncLLM fake, then launches real vLLM on 20 accepted dev-main items in a fresh interpreter. Proof returns stay below 20 MB and production below 90 MB. chain_save saves one copy of each arm and receipt and enforces the existing 512 MiB expanded verifier limit. orchard_results builds locally and verifies independent pool/GCS copies; stdout_transfer remains identical but fetch streams raw bytes directly.',
'- submit/fetch use the requested ossh.sh operator wrapper. The /data3 notice write is removed. No remote command or job submission ran during this build.',
'- The deterministic package contains CPU proof code and parity data; both embedded payloads include the same reader, vendor parity data, selection, engine fake and runtime helpers; they exclude official metadata and test artifacts and remain below the original 3 MiB base64 limit.','',
'- Stdlib tracing records hash-keyed line sets in every job Python process and its threads; final publication lines return as a separate bounded TRACE sidecar. lines_report.py combines only matching source hashes.',
'- Proof and production preparations carry byte-identical code; deterministic gzip removes timestamp differences. CONFIG mode and phase_b select execution; both modes request one GPU; tokens also bind paths and derived hashes.',
'', '## File hashes','', '| File | Status | SHA256 | Accepted SHA256 |','|---|---|---|---|']
for name,r in records.items():text.append(f"| {name} | {r['status']} | `{r['sha256']}` | `{r.get('accepted_sha256','—')}` |")
text+=['','## Changes in this pass','',
'Pool configuration defaults to /project/community/jjyeung/okh7/x27ret. A subprocess performs a 4 MiB fsync/SHA256 write test with a 60-second deadline before staging. Pool locks enforce <100 MB; proof returns stay <20 MB and production packets <90 MB. Only the authorized .wtest is removed.',
'Both return channels verify independently. GCS uploads use the export credentials, deadlines, object generations and SHA256 readback. Receipts/logs identify verified channels. Fetch streams pool/GCS stdout into the lane; >=20 MB stops for governor registration.',
'Proof requests an H100/16 CPUs/200G/2h, keeps real card checks, runs 14 official fake-engine items and then 20 dev-main real-engine items. An isolated interpreter prevents fake-engine leakage. Accepted request/cell settings and sort order are checked; smoke_items alone limits the dev prefix.',
'Twenty reconstructed frame receipts match accepted frames/0.json hashes and identify 576 PNGs. The unchanged accepted puller reads k6tk. Phase B requires 16 ID and two pixel checks and reports accepted prompt hashes, item-level generation/answer/score agreement and paired arm means.',
'Local proof uses fake engines for both phases and miniature media/model/storage fixtures. New tests cover return channels, deadlines, corruption, caps, fetch registration, Phase A gating, accepted receipt reconstruction and comparison counts. No Orchard action was performed.',
'Final trace sidecars use bounded pool/GCS publication; the archive snapshot remains available if sidecar publication fails. The job runner keeps mode separate from storage evidence.',
'', '### Changed/new files relative to the supplied kit','']
before_records=json.loads((K/'build/PASS2_FILES.json').read_text())
for name,row in records.items():
    before=before_records.get(name)
    if before is None or row['sha256']!=before['sha256']:
        status='CHANGED' if before is not None or name in ('build/package.py','build/coverage_report.py','build/ORIGINS.json') else 'NEW'
        text.append('- '+status+': `'+name+'`')
text.append('- CHANGED: `REPORT.md`, `DIFF.md`, `KIT_SHA256`, `package.tar` and external build inventories.')
text+=['','## Unified diffs','']
for name,r in records.items():
    if r['status']!='CHANGED':continue
    old=(P/r['accepted_copy']).read_text().splitlines(keepends=True);new=(K/name).read_text().splitlines(keepends=True)
    text.extend(['### '+name,'','Accepted source: `'+r['accepted_copy']+'`.','','```diff',''.join(difflib.unified_diff(old,new,fromfile='accepted/'+name,tofile='package/'+name)).rstrip(),'```',''])
(K/'DIFF.md').write_text('\n'.join(text)+'\n')
print(json.dumps(dict(files=len(files),bytes=(K/'package.tar').stat().st_size,KIT_SHA256=h)))
