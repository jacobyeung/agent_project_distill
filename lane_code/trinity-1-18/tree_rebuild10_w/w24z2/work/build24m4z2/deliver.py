from pathlib import Path
import json,hashlib,shutil,base64,sys,ast
J=Path.cwd();D=J/'work/build24m4z2';O=J/'out';E=O/'e2'
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
 record=dict(build='24m4z2',GO=armed,baseline='Overlay with all corresponding 24m4y2 reviewed files applied; n_go requires the 24m4y2 optional GO overlay first',files=rows,total_bytes=sum(v['bytes'] for v in rows),tree_sha256=delta['tree_sha256'],uploaded=False,launched=False,
   kit_seal=sha(O/('kit_n_go' if armed else 'kit_n')/'SHA256SUMS.txt'))
 write(O/('UPLOADS_24M4Z2'+suffix+'.json'),record)
 (O/('UPLOADS_24M4Z2'+suffix+'.list')).write_text(''.join(v['name']+'\n' for v in rows))
e2_names=['e2.sh','e2.py','observe.py','run.sh','k.tgz','pins.json']
e2=[entry(E/n,'e2/'+n) for n in e2_names]
write(O/'UPLOADS_24M4Z2_E2.json',dict(build='24m4z2',files=e2,uploaded=False,launched=False,total_bytes=sum(v['bytes'] for v in e2)))
(O/'UPLOADS_24M4Z2_E2.list').write_text(''.join(v['name']+'\n' for v in e2))
objects=load(O/'kit_n/k/y.json')['objects']
(E/'SESSION_NAMES.template.list').write_text(''.join(v+'.j<job>'+f'.part{i:02d}-of-04\n' for v in objects.values() for i in range(4)))
usage='''The CPU job is ready to upload. No remote job has been submitted. Its aggregate result must remain FAIL while the adopted kit lacks an exit-archive GCS route (E102); all other checks have passed against a local sink.

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

Record the returned numeric job ID. The file requests partition `preempt`, one CPU-only task, four CPUs, 16G and one hour. Its fixed name is `a15_cot_apf482d730ca91`. Slurm stdout and stderr go to `/tmp/q_e2_%j.log` and `/tmp/q_e2_%j.err`; the body redirects both streams to node-local files. The job writes only `X/o/<job>/E2.json` and `logs.tgz` on the real filesystem, using `.part` names during replacement.

While held, n_ops8 must mint 104 fresh sessions in its chosen bucket, then install `X/n_s/sess_<job>.json` with directory mode 0700 and file mode 0600, both owned by the submitting user. The JSON maps each exact object name to its fresh resumable session URL. Never print the file or its values. The required names are all 26 values from the new `k/y.json`, each followed by `.j<job>.part00-of-04` through `.j<job>.part03-of-04`. `SESSION_NAMES.template.list` spells out all 104 names; replace `<job>` with the actual job ID. No exit-archive label exists. Only the m100, ck00 and ckstop groups are consumed by this fixture, but prepare requires the full set.

After n_ops8 confirms installation, the lane can run `scontrol release <job>`. A failed allocation must use a new job ID and fresh sessions; do not reuse completed resumable sessions.

The job first probes `unshare -Urm` and a 1 MiB tmpfs; E01 means either is unavailable. It verifies the staged bundle pins, every sealed member, BUILD's manifest hash and the kit's own checker. It then creates two 3 MiB local payloads and an exit archive. A private 16 MiB tmpfs covers X; the sessions are copied there before dd fills it and df records zero available bytes. The same real pc.sh/pc.py/gc.py/o.py sources execute from the verified local kit. A separate observer forwards the unmodified HTTP response bytes and saves only size, crc32c, md5Hash, name and generation. The observer wraps the gc.py invocation so the sealed writer still performs the request, hashing and receipt checks. It supplies no replacement network implementation on Orchard.

The fixture invokes the launch's final-copy command while its files are static and X is full. The original small publisher remains alive. After tmpfs grows to 64 MiB, the job waits up to 660 seconds for that same publisher to resume; the actual 600-second interval is unchanged. This proves the copier with synthetic payloads and real sessions, not admission or training. The unchanged 50 GiB local spool reserve still applies; insufficient local free space produces a failed check.

`E2.json` lists PASS/FAIL per check and one row per part: exact name, bytes, locally computed SHA256 and the final response fields returned by GCS. It also retains the copier's local receipt fields. `logs.tgz` contains screened bounded logs and receipts, never sessions or tokens. E102 records the missing exit-archive route; the separate recovery check verifies that o.tar reaches X after space returns. An allocation that cannot publish its final report retains it under its node-local q_e2_<job> directory.

On trinity-3-30, n_ops8 can validate the exact GCS generations using the separately supplied local `readback.py`. Copy the small E2.json report to node-local scratch using the lane's authorized channel. In the credentialed shell on that node, run:

```bash
nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B readback.py E2.json --bucket BUCKET
```

Use the bucket n_ops8 selected when minting the sessions. The reader obtains an access token through gcloud without displaying it and passes it to curl through stdin. It reads serially at at most 8 MiB/s, pins the returned generation, and compares name, size, SHA256, md5Hash and crc32c. It prints only names, sizes, hashes and PASS/FAIL. Readback uses the full object names in E2.json; it does not use or expose session URLs. For a restored archive, concatenate part00 through part03 in that order. `readback.py`, this usage file and the name template are operator-side helpers, not part of the six-file Orchard upload list.
'''
usage+='\nThe operator-side readback helper SHA256 is `'+sha(E/'readback.py')+'`.\n'
(E/'E2_USAGE.md').write_text(usage)
shutil.copy2(J/'inputs/KIT_CHANGE_24M4Z.patch',D/'KIT_CHANGE_24M4Z.patch')
checks=load(J/'work/enospc2/RESULTS.json');suite=load(D/'SUITES.json')
oldn=old['work/build24/kits/n']['SHA256SUMS.txt']['sha256'];oldgo=old['out/kit_n_go']['SHA256SUMS.txt']['sha256']
report='''The adopted patch is applied and sealed, but the requested full-ENOSPC gate is **FAIL**: the exit archive has no GCS route. Exports, ordinary checkpoints and the stop checkpoint reach the local sink while X has zero free bytes. The exit archive remains local until X recovers. The E2 CPU job deliberately reports this gap as E102 instead of claiming a pass.

| Check | Outcome | Evidence |
|---|---|---|
'''
desc={'prepare_missing':'Missing sessions refuse before the training marker; file missing.','prepare_incomplete':'Incomplete sessions refuse before the training marker; E101.','full':'dd exhausts the 16 MiB tmpfs; df and disk_usage show zero available.','wrapper_local_logs':'The bounded child and real l.py return 0; the local checkpoint survives.','nonfatal_launch_finalizer':'The actual pc.sh EXIT path returns 0 and keeps local o.tar and RESULT.json; o.py logs E28 locally.','full_exports_and_stop':'Twelve parts cover m100, ck00 and ckstop; sink bytes and SHA256 match all receipts.','exit_archive_full_sink':'FAIL: no archive object or upload branch exists in the adopted patch.','pretraining_full_refusal':'rv.run refuses with ENOSPC and writes no REVIEW_ACCEPTED receipt.','full_automatic_retries':'The same small publisher stays alive and records repeated E28 locally.','automatic_recovery':'Without restarting the publisher, copy.json, wrapper logs and exact o.tar bytes appear after remount.'}
for r in checks:report+='| '+r['name']+' | '+r['status']+': '+desc[r['name']]+' | `'+r['log']+'` |\n'
report+='''| Wrapper redirection | PASS: the exact jn2 prefix redirects stdout/stderr locally, retains the checkpoint, retries E28 and republishes exact logs. | `work/enospc2/wrapper_prefix2.log` |
| TERM and USR1 | PASS: the actual pc.sh/sr.py path signals a descendant worker; both return 0 and retain its stop marker. | `work/build24m4z2/existing_signals.log`; `work/enospc2/logs4/` |
| Existing ENOSPC suite | PASS: 20 sink parts; a fresh export performs zero project write opens; all assertions retained. | `work/build24m4z2/existing_proposed_final.log` |
| Existing legacy copier suite | FAIL: all five cases refuse at fixture construction because the old suite supplies no sessions. Assertions were not weakened. | `work/build24m4z2/legacy_live_tests.log` |
| Compatible legacy cases | PASS: the original cap/listing and TERM assertions pass after supplying the now-mandatory session fixture. | `work/build24m4z2/legacy_ready.log` |
| Current copier regression suite | PASS: eight cases cover caps, missing/incomplete sessions, private modes and symlinks, allocation names, 16-slot exhaustion, retry/idempotence, dedicated stop upload and rejected MD5. | `work/build24m4z2/current_tests_final.log` |
| CPU job local dry run | PASS as a diagnostic: 12 parts and response fields match; its aggregate job result is correctly FAIL for archive_while_full. | `work/build24m4z2/e2_final.log`; `work/build24m4z2/e2_final/RESULT.json` |
| Readback helper | PASS against the local fixture: 12 generations, sizes, MD5, CRC32C fields and SHA256; no credentials printed. | `work/build24m4z2/READBACK_TEST.json` |
| Seals and Python/shell syntax | PASS: every kit's own checker and the native build checker agree; the full Python kit and E2 sources compile. | `work/build24m4z2/FINAL_SEALS.json`; `work/build24m4z2/suites.log` |

The four requested files were byte-identical between N and N_GO before patching. Both kits received the same change. The package supplied N at `work/build24/kits/n`; the build materializes `out/kit_n` and keeps the canonical copy identical. N and N_GO differ only in k/a.json and the two seals. GO is false in N, Q and QD and true only in N_GO, in both BUILD.json and k/a.json.

| Kit | Old seal | New seal |
|---|---|---|
'''
report+='| N | `'+oldn+'` | `'+sha(O/'kit_n/SHA256SUMS.txt')+'` |\n'
report+='| N_GO | `'+oldgo+'` | `'+sha(O/'kit_n_go/SHA256SUMS.txt')+'` |\n'
for label,r in [('Q','work/build24/kits/q'),('QD','out/kit_qd')]:
 h=sha(J/r/'SHA256SUMS.txt');report+='| '+label+' | `'+h+'` | `'+h+'` |\n'
report+='''
`work/build24m4z2/DELTA.json` records a full byte/size/mode/membership comparison streamed from the supplied 24m4y2 archive (SHA256 `'''+delta['source_archive_sha256']+'''`). Exactly b/o.py, b/pc.py, b/pc.sh, k/y.json, SHA256SUMS.txt and BUILD.json change in each N kit. Q, QD, every rcj helper and both retained tree directories are identical. The active tree's own inventory digest remains `'''+delta['tree_sha256']+'''`. Admission, census, configuration preparation and the training loop are unchanged.

The local harness executes copies of the new sealed bytes in unshare -Urmn. It substitutes only n_root in memory, a local in-process HTTPS sink and an accelerated copier polling clock (0.003 scale). The wrapper test executes its exact prefix/helper and substitutes the unavailable GPU/resolver/job boundary with a bounded printing fixture. The real worker signal tests retain the launch finalizer. The rv.run refusal supplies synthetic identity/evidence prerequisites. Local tests do not exercise Slurm daemon buffering, real GCS, data preparation, GPU training, node-local ENOSPC, inode exhaustion or teardown after a failed upload. The supplied harness and logs remain under work/enospc2/inherited; fresh logs are listed above.

The E2 job leaves its production polling intervals unchanged, probes unshare/tmpfs, verifies the complete staged kit, uses real sessions installed while held, records response fields without capabilities, and writes only the bounded final report/log tar under X/o/<job>. `out/e2/E2_USAGE.md` gives exact upload hashes, the held submit command, all session names and the trinity-3-30 readback procedure. No remote job, session minting, network request or GPU operation ran in this build.

The ordinary upload delta contains six N kit files and jn2.sh. The separate GO delta contains the six changed N_GO files against the corresponding 24m4y2 GO overlay; it does not arm N. E2 has its own six-file upload list and complete sealed bundle. Every upload file is under 5,000,000 bytes. The final delivery archive is not an individual Orchard upload.

Retained failures are listed with their full output in work/build24m4z2/FAILURES.json. The legacy suite's absent-session expectations and the absent archive route remain explicit. Setup-only failures include a shell-heredoc quoting error before files ran, a regression assertion that expected a return instead of the real MD5 exception, an early wrapper recovery assertion that saw the zero-byte file created while full, and mismatched modes on regenerated canonical N seals. The corrected checks have separate logs; no cluster-killed command was rerun.

Card sentences:

- The sealed ENOSPC gate is FAIL because the adopted kit cannot send its exit archive to GCS while X remains full.
- Exports, ordinary checkpoints and the dedicated stop checkpoint upload with local claims and receipts while X has zero free bytes.
- Live publication and wrapper log publication keep retrying and resume automatically after X recovers; the tested trainer/finalizer return code stays zero.
- Missing sessions refuse with file missing; incomplete sessions refuse with E101 at pc.sh's --prepare command, before training starts.
- N and N_GO are resealed; Q, QD, rcj and tree 9d2bbb8a are unchanged. Fresh per-allocation sessions and a new runtime review remain necessary.
- The CPU diagnostic is ready for the lane's held submission. Real-session GCS behavior remains untested here, and E102 remains a required failure until an archive route is authorized.

The required old/new seal table and retained-failure details are deliberate comparisons requested by this build, not a narrative of paper revisions.
'''
(O/'ENOSPC_24M4Z2.md').write_text(report)
lines=[
 'The adopted patch is applied to N and N_GO; the full-ENOSPC gate remains FAIL because the exit archive has no GCS route (E102).',
 'N seals '+oldn[:8]+' to '+sha(O/'kit_n/SHA256SUMS.txt')[:8]+'; N_GO seals '+oldgo[:8]+' to '+sha(O/'kit_n_go/SHA256SUMS.txt')[:8]+'; every own/native checker passes.',
 'The full archive comparison proves exactly four files plus two seals changed per N kit; Q, QD, rcj and tree 9d2bbb8a are identical; GO=true only in N_GO.',
 'On full private tmpfs, exports and both checkpoint routes reach the local sink; live publication, local wrapper logs and exit-archive publication resume automatically after recovery.',
 'Missing/incomplete sessions refuse before training; the pre-training ENOSPC gate refuses safely; TERM and USR1 preserve the local stop marker and return zero.',
 'The existing ENOSPC/signal suites, two compatible legacy cases and eight current regression cases pass; all five unadapted legacy cases fail because their sessions are absent.',
 'The E2 CPU job verifies uploaded kit bytes and records real-response metadata; its local dry run validates 12 sink parts and correctly reports archive_while_full=FAIL.',
 'The ordinary, GO and E2 upload lists are separate; all upload assets are below 5 MB; E2_USAGE.md gives hashes, held submission, 104 session names and readback instructions.',
 'ENOSPC_24M4Z2.md links outcomes and retained failures; no network, scheduler, GPU, Git, SSH or other agent was used.',
 'The package contains out and work, excludes the canonical trees and itself, verifies archived members, and receives its checksum last.'
]
assert len(lines)<12;(O/'BUILD24M4Z2_REPORT.md').write_text('\n'.join(lines)+'\n')
print(json.dumps(dict(normal_uploads=len(normal),GO_uploads=len(go),E2_uploads=len(e2),maximum_upload_bytes=max(r['bytes'] for r in normal+go+e2),report_lines=len(lines))))
