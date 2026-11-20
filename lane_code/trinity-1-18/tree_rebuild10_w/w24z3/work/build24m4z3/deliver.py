from pathlib import Path
import json,hashlib,shutil,base64,sys,ast
J=Path.cwd();D=J/'work/build24m4z3';O=J/'out';E=O/'e2'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):p.write_text(json.dumps(v,sort_keys=True,indent=2)+'\n')
def load(p):
 v=json.loads(p.read_bytes())
 return json.loads(base64.b64decode(v['payload'])) if isinstance(v,dict) and v.get('encoding') else v
old=load(D/'BASELINE_FILES.json');delta=load(D/'DELTA.json');assert delta['status']=='PASS'
names=['BUILD.json','SHA256SUMS.txt','b/o.py','b/pc.py','b/pc.sh','k/y.json']
def entry(p,name,baseline=None):
 assert p.stat().st_size<=5_000_000,(name,p.stat().st_size)
 return dict(name=name,relative_path=str(p.relative_to(J)),local_path=str(p),sha256=sha(p),bytes=p.stat().st_size,mode=format(p.stat().st_mode&511,'04o'),action='replace' if baseline else 'add',baseline_sha256=baseline)
normal=[entry(O/'kit_n'/n,'n/'+n,old['work/build24/kits/n'][n]['sha256']) for n in names]
normal.append(entry(O/'jn2.sh','jn2.sh'))
go=[entry(O/'kit_n_go'/n,'n_go/'+n,old['out/kit_n_go'][n]['sha256']) for n in names]
for suffix,rows,armed in (('',normal,False),('_GO',go,True)):
 record=dict(build='24m4z3',GO=armed,baseline='Overlay with all corresponding 24m4y2 reviewed files applied; n_go requires the 24m4y2 optional GO overlay first',files=rows,total_bytes=sum(v['bytes'] for v in rows),tree_sha256=delta['tree_sha256'],uploaded=False,launched=False,
   kit_seal=sha(O/('kit_n_go' if armed else 'kit_n')/'SHA256SUMS.txt'))
 write(O/('UPLOADS_24M4Z3'+suffix+'.json'),record)
 (O/('UPLOADS_24M4Z3'+suffix+'.list')).write_text(''.join(v['name']+'\n' for v in rows))
e2_names=['e2.sh','e2.py','observe.py','run.sh','k.tgz','pins.json']
e2=[entry(E/n,'e2/'+n) for n in e2_names]
write(O/'UPLOADS_24M4Z3_E2.json',dict(build='24m4z3',files=e2,uploaded=False,launched=False,total_bytes=sum(v['bytes'] for v in e2)))
(O/'UPLOADS_24M4Z3_E2.list').write_text(''.join(v['name']+'\n' for v in e2))
objects=load(O/'kit_n/k/y.json')['objects']
(E/'SESSION_NAMES.template.list').write_text(''.join(v+'.j<job>'+f'.part{i:02d}-of-04\n' for v in objects.values() for i in range(4)))
usage='''The CPU job is ready to upload. No remote job has been submitted. Its local dry run passes every required check, including archive_while_full. Real GCS validation still requires the held CPU job and generation-pinned readback.

Upload these six files beneath `/project/community/jjyeung/okh7/x_22c714e1/`. Every listed SHA256 authenticates the complete file. `k.tgz` contains the full newly sealed N kit with GO=false; its copier and archive bytes match N_GO.

| Destination relative to X | Bytes | SHA256 |
|---|---:|---|
'''
usage+=''.join('| '+r['name']+' | '+str(r['bytes'])+' | `'+r['sha256']+'` |\n' for r in e2)
usage+='''
On Orchard, submit exactly:

```bash
X=/project/community/jjyeung/okh7/x_22c714e1
sbatch --hold "$X/e2/e2.sh"
```

Record the returned numeric job ID. The file requests partition `preempt`, one CPU-only task, four CPUs, 16G and one hour. Its fixed name is `a15_cot_ap8d3ce49b27f1`. Slurm stdout and stderr go to `/tmp/q_e2_%j.log` and `/tmp/q_e2_%j.err`; the body redirects both streams to node-local files. The job writes only `X/o/<job>/E2.json` and `logs.tgz` on the real filesystem, using `.part` names during replacement.

While held, n_ops8 must mint 108 fresh sessions in its chosen bucket, then install `X/n_s/sess_<job>.json` with directory mode 0700 and file mode 0600, both owned by the submitting user. The JSON maps each exact object name to its fresh resumable session URL. Never print the file or its values. The required names are all 27 values from the new `k/y.json`, each followed by `.j<job>.part00-of-04` through `.j<job>.part03-of-04`. `SESSION_NAMES.template.list` spells out all 108 names; replace `<job>` with the actual job ID. The exit archive uses label `o`, whose base name is `q9/22c714e1/469ddece_o.tar`. The fixture consumes m100, ck00, ckstop and o (16 parts); prepare requires all 108 names and refuses a set missing the four o parts.

After n_ops8 confirms installation, the lane can run `scontrol release <job>`. A failed allocation must use a new job ID and fresh sessions; do not reuse completed resumable sessions.

The job first probes `unshare -Urm` and a 1 MiB tmpfs; E01 means either is unavailable. It verifies the staged bundle pins, every sealed member, BUILD's manifest hash and the kit's own checker. It then creates two 3 MiB local payloads and an exit archive. A private 16 MiB tmpfs covers X; the sessions are copied there before dd fills it and df records zero available bytes. The same real pc.sh/pc.py/gc.py/o.py sources execute from the verified local kit. A separate observer forwards the unmodified HTTP response bytes and saves only size, crc32c, md5Hash, name and generation. The observer wraps the gc.py invocation so the sealed writer still performs the request, hashing and receipt checks. It supplies no replacement network implementation on Orchard.

The fixture invokes the launch's final-copy command while its files are static and X is full. The original small publisher remains alive. After tmpfs grows to 64 MiB, the job waits up to 660 seconds for that same publisher to resume; the actual 600-second interval is unchanged. This proves the copier with synthetic payloads and real sessions, not admission or training. The unchanged 50 GiB local spool reserve still applies; insufficient local free space produces a failed check.

`E2.json` lists PASS/FAIL per check and one row per part: exact name, bytes, locally computed SHA256 and the final response fields returned by GCS. It also retains the copier's local receipt fields. `logs.tgz` contains screened bounded logs and receipts, never sessions or tokens. archive_while_full is a required PASS: all four archive parts must have verified receipts while X has zero free bytes, and RESULT.json must be inside the exact o.tar bytes. The separate recovery check verifies that o.tar reaches X after space returns. An allocation that cannot publish its final report retains it under its node-local q_e2_<job> directory.

On trinity-3-30, n_ops8 can validate the exact GCS generations using the separately supplied local `readback.py`. Copy the small E2.json report to node-local scratch using the lane's authorized channel. In the credentialed shell on that node, run:

```bash
nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B readback.py E2.json --bucket BUCKET
```

Use the bucket n_ops8 selected when minting the sessions. The reader obtains an access token through gcloud without displaying it and passes it to curl through stdin. It reads serially at at most 8 MiB/s, pins the returned generation, and compares name, size, SHA256, md5Hash and crc32c. It prints only names, sizes, hashes and PASS/FAIL. Readback uses the full object names in E2.json; it does not use or expose session URLs. The reader requires all 16 parts and archive_while_full=PASS. It also concatenates the four archive parts in order and verifies the complete o.tar size and SHA256 from E2.json. RESULT.json is inside that archive; its node-local copy also publishes to X/o/<job>/RESULT.json. `readback.py`, this usage file and the name template are operator-side helpers, not part of the six-file Orchard upload list.
'''
usage+='\nThe operator-side readback helper SHA256 is `'+sha(E/'readback.py')+'`.\n'
(E/'E2_USAGE.md').write_text(usage)

checks=load(J/'work/enospc3/RESULTS.json')
assert all(r['status']=='PASS' for r in checks)
seals=load(D/'SEALS.json');before={r['kit']:r['old'] for r in seals}
report="""The local ENOSPC gate is **PASS**. Exports, ordinary and stop checkpoints, and the exact exit archive reach the local GCS substitute while X has zero free bytes. RESULT.json is inside o.tar. The E2 CPU job requires archive_while_full=PASS and its local aggregate result is PASS.

| Check | Outcome | Evidence |
|---|---|---|
"""
for r in checks:report+='| '+r['name']+' | '+r['status']+' | `'+r['log']+'` |\n'
report+="""| Copier regression | PASS: 10 cases, including failed archive part, resumed upload, no duplicate completed object, and refusal without its four sessions. | `work/build24m4z3/current_tests_final.log` |
| Existing ENOSPC suite | PASS: 20 parts; a fresh export performs zero project write opens. | `work/build24m4z3/existing_proposed_final.log` |
| Existing signals | PASS: TERM and USR1 preserve the descendant stop marker and return zero. | `work/build24m4z3/existing_signals.log` |
| Compatible legacy cases | PASS: original cap/listing and TERM assertions with complete current finalizer fixtures. | `work/build24m4z3/legacy_verified.log` |
| Wrapper | PASS: exact jn2 prefix/helper keeps logs local and resumes publication after recovery. | `work/build24m4z3/wrapper.log` |
| E2 local dry run | PASS: all 13 required checks and all 16 part receipts. | `work/build24m4z3/e2_final.log`; `work/build24m4z3/e2_final/n/E2.json` |
| Readback | PASS: 16 pinned generations, response fields, part hashes and reconstructed archive SHA256. | `work/build24m4z3/READBACK_TEST.json`; `work/build24m4z3/readback_test.log` |
| Seals and syntax | PASS: five own/native kit checks; all N/N_GO and E2 Python sources and five shells. | `work/build24m4z3/FINAL_SEALS.json`; `work/build24m4z3/SYNTAX.json` |
| Full archive diff | PASS: four files plus two seals per N kit; Q, QD, rcj and both trees unchanged. | `work/build24m4z3/DELTA.json` |

The finalizer creates o.tar before final copying. It atomically publishes the local archive once and includes the final RESULT.json, so a retry cannot rebuild bytes behind completed receipts. The copier passes that exact archive to the same gc.py split writer, using one local claim and four local receipts for `q9/22c714e1/469ddece_o.tar.j<job>`. A failed part stays pending; reruns skip completed parts. The finalizer retries up to three passes, ten seconds apart, inside its existing 150-second copy timeout. Its small publisher also retries X/o/<job>/o.tar and RESULT.json. A permanently failed upload still cannot survive node teardown; local PASS proves the supplied sink behavior, not real GCS availability.

The required session set contains 27 labels and 108 names. Missing sessions, incomplete sessions and the 104-name set without o refuse before training. The configuration preparation, admission, census and training sources are unchanged.

| Kit | 24m4z2 seal | 24m4z3 seal |
|---|---|---|
"""
for label,root in [('N','out/kit_n'),('N_GO','out/kit_n_go')]:
 report+='| '+label+' | `'+before[root]+'` | `'+sha(J/root/'SHA256SUMS.txt')+'` |\n'
for label,root in [('Q','work/build24/kits/q'),('QD','out/kit_qd')]:
 h=sha(J/root/'SHA256SUMS.txt');report+='| '+label+' | `'+h+'` | `'+h+'` |\n'
report+="""
The full comparison streams every member of the supplied 24m4y2 archive (SHA256 `15cdc1273ff7a1c794c79c895505d08a5a1e325b21029d3606eac999f5efa181`) and compares file bytes, sizes, modes and membership in the protected roots. N and N_GO change only b/o.py, b/pc.py, b/pc.sh, k/y.json, SHA256SUMS.txt and BUILD.json. The canonical N copy matches out/kit_n. N_GO differs from N only in k/a.json and the seals. GO is true only in N_GO. The active tree digest remains `9d2bbb8ad209d91e21e56121785f62b0dddf3c8d9f14db8d23daf6dcd1d3591b`.

The fresh harness under work/enospc3 reruns work/enospc2 with the sealed new bytes. It uses private 16 MiB tmpfs, unshare -Urmn, an in-process HTTPS substitute, an in-memory n_root mapping and a 0.003 polling-clock scale. It preserves the real copier, writer and finalizer. The E2 dry run verifies its uploaded bundle before applying the same local adapters. Production E2 retains its polling intervals. No network, Orchard, scheduler, GPU, SSH, Git or other agent ran. These tests do not exercise real GCS, node teardown, training, inode exhaustion or local-spool exhaustion.

UPLOADS_24M4Z3.json/.list applies the six N changes and jn2.sh to the reviewed 24m4y2 overlay. The separate _GO list applies six corresponding GO files; _E2 lists six CPU-job assets. Every upload file is below 5,000,000 bytes. E2_USAGE.md gives their hashes, the held submit command, all 108 session names and generation-pinned archive readback. Only the lane submits the job.

FAILURES.json retains the full output of the fixture permission failure and incomplete legacy finalizer fixture, with their successful corrected checks. Expected failed-part and rejected-digest diagnostics remain in the regression log. No cluster-killed command was rerun.

Card sentences:

- The local ENOSPC gate passes: exports, the stop checkpoint and the exact exit archive reach the sink while X has zero free bytes.
- The archive contains RESULT.json and uses one allocation-specific label with the same local claim, receipt and retry path as exports.
- N and N_GO are sealed; only the four authorized files and seals differ from 24m4y2, and Q, QD, rcj and tree 9d2bbb8a remain unchanged.
- Prepare requires 108 fresh sessions; omission of the four archive sessions refuses before training.
- The E2 local aggregate is PASS and readback verifies all 16 parts plus the complete archive; real GCS remains for the lane's held job.

The requested old/new seal table and named 24m4y2 comparison are retained because they establish the authorized file boundary.
"""
(O/'ENOSPC_24M4Z3.md').write_text(report)
lines=[
 'The local ENOSPC gate and the E2 local aggregate are PASS, including the exit archive while X has zero free bytes.',
 'N seals '+before['out/kit_n'][:8]+' to '+sha(O/'kit_n/SHA256SUMS.txt')[:8]+'; N_GO seals '+before['out/kit_n_go'][:8]+' to '+sha(O/'kit_n_go/SHA256SUMS.txt')[:8]+'; all own/native checkers pass.',
 'The full diff against 24m4y2 15cdc127 changes only four authorized files and two seals per N kit; Q, QD, rcj and tree 9d2bbb8a are identical.',
 'The exact o.tar includes RESULT.json and uploads through gc.py with allocation-specific local claims and receipts; X remains a retried second destination.',
 'Ten current regressions pass, including failed-part recovery, no duplicate archive object and refusal when the four archive sessions are absent.',
 'Every ENOSPC check, TERM/USR1, wrapper recovery, the existing copier suite and two compatible legacy cases pass on current fixtures.',
 'E2 requires archive_while_full=PASS; its dry run and readback verify 16 parts and the complete archive hash.',
 'The upload lists separate N, GO and E2, all below 5 MB; E2_USAGE.md lists hashes, 108 session names and the held submission/readback procedure.',
 'FAILURES.json retains fixture errors and corrected evidence; no network, scheduler, GPU, Git, SSH or other agent ran.',
 'The package contains out and work, excludes the canonical trees and itself, verifies all archived members, and receives its checksum last.'
]
assert len(lines)<12;(O/'BUILD24M4Z3_REPORT.md').write_text('\n'.join(lines)+'\n')
print(json.dumps(dict(normal_uploads=len(normal),GO_uploads=len(go),E2_uploads=len(e2),maximum_upload_bytes=max(r['bytes'] for r in normal+go+e2),report_lines=len(lines))))
