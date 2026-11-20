from pathlib import Path
import json,hashlib,base64,re
J=Path.cwd();D=J/'work/build24m4z5';O=J/'out';E=O/'e3';W=J/'work/enospc5_final'
def load(p):
 v=json.loads(p.read_text());return json.loads(base64.b64decode(v['payload'])) if isinstance(v,dict) and 'payload' in v else v
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):p.write_text(json.dumps(v,sort_keys=True,indent=2)+'\n')
baseline=load(D/'BASELINE_FILES.json');delta=load(D/'DELTA.json');assert delta['status']=='PASS'
files=['BUILD.json','SHA256SUMS.txt','b/o.py','b/pc.py','b/pc.sh','k/y.json']
def entry(p,name,old=None):
 assert p.stat().st_size<5_000_000
 return dict(name=name,relative_path=str(p.relative_to(J)),local_path=str(p),bytes=p.stat().st_size,sha256=sha(p),mode=format(p.stat().st_mode&511,'04o'),baseline_sha256=old,action='replace' if old else 'add')
normal=[entry(O/'kit_n'/n,'n/'+n,baseline['work/build24/kits/n'][n]['sha256']) for n in files]+[entry(O/'jn3.sh','jn3.sh')]
go=[entry(O/'kit_n_go'/n,'n_go/'+n,baseline['out/kit_n_go'][n]['sha256']) for n in files]
e3=[entry(E/n,'e3/'+n) for n in ('e3.sh','e3.py','observe.py','run.sh','k.tgz','pins.json')]
for suffix,rows,armed in (('',normal,False),('_GO',go,True),('_E3',e3,False)):
 write(O/('UPLOADS_24M4Z5'+suffix+'.json'),dict(build='24m4z5',files=rows,GO=armed,uploaded=False,launched=False,launch_verdict='NO-GO: see NEEDS_OTHER_FILE_24M4Z5.md',total_bytes=sum(r['bytes'] for r in rows),baseline='24m4y2 reviewed overlay; GO uses its matching GO overlay'))
 (O/('UPLOADS_24M4Z5'+suffix+'.list')).write_text(''.join(r['name']+'\n' for r in rows))
objects=load(O/'kit_n/k/y.json')['objects'];assert len(objects)==27
(E/'SESSION_NAMES.template.list').write_text(''.join(v+'.j<job>'+f'.part{i:02d}-of-04\n' for v in objects.values() for i in range(4)))
job=re.search(r'--job-name=(\S+)',(E/'e3.sh').read_text())[1]
usage='''E3 is an offline-validated CPU diagnostic awaiting real-session execution. Its local dry run uses a 4 MiB substitute and passes all 15 checks. The submitted driver creates a 2,147,483,648-byte random payload only on the allocated node. No real GCS rate is claimed by this build.

Upload these six files beneath X = `/project/community/jjyeung/okh7/x_22c714e1`. Each is below 5 MB; k.tgz contains the complete sealed N kit with GO=false.

| Destination relative to X | Bytes | SHA256 |
|---|---:|---|
'''+''.join('| '+r['name']+' | '+str(r['bytes'])+' | `'+r['sha256']+'` |\n' for r in e3)+'''
The three launch steps are:

1. **Hold:** `sbatch --hold "$X/e3/e3.sh"` and record its numeric job ID. Submission should take less than one minute; queue delay is unknown.
2. **Mint:** n_ops8 creates 108 fresh resumable sessions for that job ID and installs `X/n_s/sess_<job>.json`, owned by the submitting user, with directory mode 0700 and file mode 0600. Allow approximately 5–15 minutes for this operator step; this is an estimate, not a measured mint rate. Never print capability values.
3. **Release:** after validating the complete session mapping, run `scontrol release <job>`. Release should take less than one minute. Expect roughly 12–20 execution minutes at adequate upload rates; the allocation allows one hour and queue delay is additional.

The fixed job name is `'''+job+'''`. The job requests preempt, one CPU-only task, four CPUs and 16G. It places Slurm stdout/stderr and runtime logs on node-local storage. It writes only E3.json and logs.tgz under real `X/o/<job>/`, using temporary names during replacement. SLURM_TMPDIR, its available bytes and `df -B1` output appear in E3.json; allocation-local diagnostics remain available if publication fails.

Mint every value of sealed k/y.json `objects`, suffixed with `.j<job>.part00-of-04` through `.part03-of-04`. SESSION_NAMES.template.list enumerates all 108 names. The fixture uses m100, ck00, ckstop and o for the inherited checks, plus ck01 for the rate payload: 20 objects. The ck01 parts each contain 536,870,912 bytes in the real run. The other 88 sessions are required by prepare but unused by the fixture. Failed allocations need new job IDs and new sessions.

The driver verifies its pins, complete kit membership, hashes, BUILD seal and the kit's checker. It probes unshare -Urm and tmpfs, installs the real sessions in a private 16 MiB X before filling it to zero free bytes, and executes pc.sh/pc.py with the sealed gc.py helper. Production uploads use GCS status queries and 16 MiB Content-Range requests, bounded upload quanta, atomic receipts and server-confirmed resume offsets. Completed parts are skipped. The observer records only returned name, size, generation, md5Hash and crc32c; it never records session URLs.

The final fixture retries full-X publication for 140 seconds without consuming the allocation's full deadline. It then uploads the rate payload through the same Copier.send and writer path. E3.json reports local SHA256, bytes, response fields and receipts for every part. Its rate table gives decimal MB/s and seconds for each of the four ck01 parts and their total. The total includes copier overhead; it excludes random-payload generation. Per-part time includes retries from that part's first attempt.

All 14 E2 checks remain required, including archive_while_full, final_order, automatic_recovery and exact archive recovery. The rate check is the fifteenth. Final order is stop checkpoint, exports (stop export first when identified), logs, exit archive, then ordinary checkpoints. The private X grows to 64 MiB for recovery; the same publisher must recover within its unchanged 600-second cadence. The local dry run uses a transport simulator and accelerates the copier polling clock; its MB/s values are not network measurements.

On trinity-3-30, n_ops8 can run the operator-side reader in its credentialed shell after copying the small report through the authorized channel:

```bash
nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B readback.py E3.json --bucket BUCKET
```

The reader uses the bucket selected during minting. It pins each generation, reads serially at no more than 8 MiB/s, compares name, size, SHA256, md5Hash and the returned crc32c field, and verifies the concatenated four-part exit archive. Its token travels through curl stdin and is never printed. It requires 20 objects. Concatenate each object's four parts in numeric order to restore its bytes. RESULT.json is inside the gzip-compressed exit archive.

The readback helper SHA256 is `'''+sha(E/'readback.py')+'''`. It, this usage file and the session template are operator-side helpers, not additional Orchard uploads.

The N launch remains NO-GO for the two source-scope guarantees in ../NEEDS_OTHER_FILE_24M4Z5.md. E3 tests publication and rate with synthetic payloads; it does not test training, immediate native stop identification or preservation of a shell variable lost before publication.
'''
(E/'E3_USAGE.md').write_text(usage)
checks=load(W/'RESULTS.json');assert all(r['status']=='PASS' for r in checks)
suites=load(D/'FINAL_SUITES.json');assert all(r['returncode']==0 for r in suites)
seals=load(D/'FINAL_SEALS.json');e3report=load(D/'e3_final/n/E3.json');assert e3report['status']=='PASS'
archive=next(r['result'] for r in checks if r['name']=='exit_archive_full_sink')
rows=[
 ('1','FAIL: an incomplete export receives one attempt when archive destinations are complete.','PASS: all seven pending destination classes retry, including logs and ordinary checkpoints.','complete.log; pass_after_final.log'),
 ('2','FAIL: an empty cache passes prepare; writes lack fsync.','PASS: complete 108-name mapping, JSON, owner and modes checked on cache use; atomic writes survive interruption.','complete.log; owner.log; resume.log'),
 ('3','FAIL: live archive upload bypasses stop priority; provisional archive misses the final log tail.','PASS: live archive upload is disabled; final snapshot follows stopped log writers and retains fixed bytes across retries.','pass_after_final.log; archive_final.log; enospc_final.log'),
 ('4','FAIL: an exit before the embedded call fabricates rooms_rc=0. Normal embedded rc/rr are already frozen by the old archive.','PARTIAL: real embedded values remain unchanged on X and in the final archive; unavailable rr is null. Persisting rr before shell exit requires k/j.json.','pass_after_final.log; ../..//out/NEEDS_OTHER_FILE_24M4Z5.md'),
 ('5','FAIL: ordinary checkpoints run in the export phase before logs/archive.','PASS: stop, exports (stop first), logs, archive, ordinary checkpoints; ordinary uploads are deferred out of the live loop.','pass_after_final.log; complete.log; final_loop_final.log'),
 ('6','FAIL: fixed 140/150-second final window; gc.py restarts a part from byte zero.','PARTIAL: allocation deadlines and resumable byte ranges pass; immediate stop identification requires a native stop marker.','resume.log; complete.log; ../../out/NEEDS_OTHER_FILE_24M4Z5.md'),
 ('7','FAIL: exec wrapper has no final publication, catches only OSError and omits batch logs from the archive.','PASS: TERM/USR1 child traps run, exit 17 is preserved, final logs publish, arbitrary exceptions stay local and startup free space is recorded.','wrapper_signals_final.log; wrapper_validated.log; pass_after_final.log'),
 ('8','FAIL: E2 has no rate payload or per-part rate table.','PASS locally: E3 retains all 14 checks and adds rate, with 20-object readback. Real 2 GiB GCS test is NOT RUN.','e3_final.log; readback_final.log'),
 ('9','FAIL: review probes expose the three reported defects.','PASS: all required local suites and ten before/after probes pass; own/native seals and full baseline diff pass. The two source-scope guarantees remain open.','FINAL_SUITES.json; FINAL_SEALS.json; DELTA.json')]
report='''**NO-GO for the complete launch request.** The three kit-review findings are fixed and all local suites pass. Immediate stop-checkpoint identification and a rooms return code lost before the embedded archive call require edits outside the permitted files; see NEEDS_OTHER_FILE_24M4Z5.md. No real GCS session or 2 GiB rate test ran on this node.

Each numbered item has retained fail-before evidence against the saved 24m4z4 bytes in `work/build24m4z5/fail_before_final.log`. The ten after probes pass in `pass_after_final.log`. Row 9 combines those regressions with the required suite gates.

| Item | Fail before | After | Logs under work/build24m4z5 |
|---|---|---|---|
'''+''.join('| '+i+' | '+before+' | '+after+' | `'+logs+'` |\n' for i,before,after,logs in rows)+'''
`Q_ROOT` and `N` identify the same node-local directory: job.sh:20 defines N; job.sh:29 passes it to b/x.py; x.py:5 calls bootstrap; z.py:577 resolves that node path, z.py:603 passes it to launch_shell, and z.py:607 sets Q_ROOT. The decoded k/j.json:438 invokes o.py with rc and rr, after assigning rr at line 423. That call creates a provisional local archive and may copy it to X. The outer pc.sh finalizer runs later. Its last launch-evidence writer, ep.py, now runs at pc.sh:24 before pc.py freezes the archive. The final o.py call preserves existing RESULT.json, rebuilds the archive with final log tails and j2.log/j2.err, and writes frozen.json. It never overwrites real rooms_rc with the outer zero argument. If line 438 never executes, the real rr cannot be recovered from the permitted files; null marks that missing evidence.

The final loop examines stop checkpoint, exports, logs, exit archive, X archive copy and ordinary checkpoint receipts. It retries every incomplete destination until completion or the allocation deadline. A provisional X copy cannot satisfy the final archive receipt: its SHA256 must match the frozen bytes. Claims, cached sessions, ready/done receipts, part receipts and the small-copy receipt use .part, fsync, replace and a directory fsync. Prepare refuses empty, interrupted, malformed, incomplete, wrong-owner or wrong-mode cache files.

The live copier defers ordinary checkpoint uploads and never uploads an exit archive. Once a native final run report identifies last_step, it attempts the dedicated stop checkpoint first and the matching stop export first among exports. Each upload quantum is bounded; a failed or interrupted part queries its resumable session and continues at the server's acknowledged byte. Completed parts are never resent. The offline protocol test accepts one range and drops its response, retains three other completed parts, resumes at byte 262144, and verifies zero resent bytes. It also recovers a lost final response. These are simulated protocol results, not real GCS evidence.

**Allocation window and rate.** The supplied stop-checkpoint planning size is 113,000,000,000 bytes (about 113 GB), split into four approximately 28.25 GB parts. No measured stop-export size is available in the supplied launch material. k/y.json therefore records an explicitly conservative 113,000,000,000-byte export planning allowance; this is not a measured size or an upload cap. The copier uses each actual immutable archive's byte length. Native checkpoint_space.py:135–140 derives state/export budgets from measured tensors, including serialization and export-copy allowances.

The trainer's stated self-stop is TK_JOB_START + (86,400 - 3,600) = +82,800 seconds. The bulk deadline is allocation end minus 780 seconds, or +85,620 for the 24-hour fallback. That leaves **2,820 seconds (47 minutes)**. The next 180 seconds are reserved for logs/archive, and evidence finalization ends before TERM@600. Slurm's end timestamp takes precedence; otherwise the code uses TK_JOB_START plus the recipe time limit. A 113 GB checkpoint alone needs 40.07 MB/s. With the conservative 113 GB export allowance, both need 80.14 MB/s sustained, or **100.18 MB/s with 25% rate headroom**. If archive/export production or the missing stop marker costs d seconds, the required rate is 226,000/(2,820-d) MB/s before headroom; a 600-second delay raises the headroom target to 127.25 MB/s. Real E3 rate evidence must establish whether the allocation can meet this budget.

The exit archive retains at most 40,000,000 screened log bytes and 9,000,000 metadata bytes and enforces a compressed cap of 50,000,000 bytes. The final full-X fixture produced '''+str(archive['bytes'])+''' bytes, SHA256 `'''+archive['sha256']+'''`, with RESULT.json inside. No real-job archive size is asserted.

| Kit | 24m4z4 seal | 24m4z5 seal |
|---|---|---|
'''
for name in ('kit_n','kit_n_go'):
 old=load(D/'before'/name/'BUILD.json')['kit_sha256'];new=load(O/name/'BUILD.json')['kit_sha256']
 report+='| '+name+' | `'+old+'` | `'+new+'` |\n'
report+='''
The full comparison streamed all '''+str(delta['archive_members'])+''' baseline members from archive `'''+delta['source_archive_sha256']+'''`. Only b/o.py, b/pc.py, b/pc.sh, k/y.json, BUILD.json and SHA256SUMS.txt differ per N kit. The canonical N copy matches out/kit_n. N and N_GO differ only in k/a.json and their seals. Q, QD, rcj and both trees remain byte-identical; tree SHA256 is `'''+delta['tree_sha256']+'''`. Admission, census, preparation and the training loop are untouched.

The local gate covers four archive tests, eight current copier tests, five adapted legacy tests, the real final-loop retry test, the ENOSPC harness and existing copier suite, TERM/USR1 tests, exact wrapper-prefix recovery, full wrapper child signaling, cache-owner/atomicity tests, resumed ranges, the E3 local dry run and 20-object readback. FINAL_SUITES.json names every log. FAILURES.json retains failed setup/test output and its resolution; its two unresolved entries are the documented source-scope guarantees. E3's local 4 MiB rate substitute and accelerated polling are test adapters. No network, SSH, scheduler, GPU, Git or additional agent ran.

Card sentences:

- Keep N on hold: publication regressions pass, but immediate stop identification and the early-exit rooms return code need the two edits in NEEDS_OTHER_FILE_24M4Z5.md.
- Budget 47 minutes for bulk publication, 180 seconds for bounded evidence, then the TERM@600 grace. A 113 GB checkpoint plus the conservative 113 GB export allowance needs 100.18 MB/s with 25% headroom; measure the actual export and real E3 rate before accepting that budget.
- The final archive includes screened batch logs and preserves the embedded rc/rr. Its cap is 50 MB, and its bytes remain fixed across resumable retries.
- For E3, hold with `sbatch --hold "$X/e3/e3.sh"` (under one minute), mint and validate 108 fresh per-job sessions (allow 5–15 operator minutes), then `scontrol release <job>` (under one minute; queue delay unknown). Expect approximately 12–20 execution minutes within its one-hour allocation.
- After the two source-scope guarantees are settled, N uses the same hold/mint/release sequence with `$X/jn3.sh`, a fresh job ID and its own 108 sessions. jn3.sh retains job name a15_cot_apb2edfac4. The N training allocation is 24 hours; the operator-step estimates exclude queue and training time.

The requested fail-before comparisons and old/new seals are retained to make the review auditable.
'''
(O/'ENOSPC_24M4Z5.md').write_text(report)
failures=[]
for name,file,resolved in [('wrapper stdin adapter','wrapper_first.log','wrapper_validated.log'),('wrapper stdin argv adapter','wrapper_final.log','wrapper_validated.log'),('existing ENOSPC archive assertion','existing_enospc_first.log','existing_enospc_final.log')]:
 failures.append(dict(name=name,output=(D/file).read_text(),log=str((D/file).relative_to(J)),resolved_by=str((D/resolved).relative_to(J))))
failures.extend([
 dict(name='script capsule decoding',output='json.decoder.JSONDecodeError: Expecting value: line 1 column 1 (char 0)',resolution='k/j.json contains a base64 shell script, decoded without JSON parsing into j_decoded.sh.'),
 dict(name='nested shell quoting',output="/bin/bash: -c: line 6: syntax error near unexpected token `('\n",resolution='No edit script ran; structured apply_patch wrote edit.py.'),
 dict(name='encoded BUILD capsule',output="KeyError: 'kit_sha256'",resolution='seal.py decodes and re-encodes BUILD.json; own/native checkers pass.'),
 dict(name='tail syntax',output='tail: option used in invalid context -- 4',resolution='Read logs with tail -n.'),
 dict(name='named optional files absent',output="sed: can't read work/build24m4z4/final_checks.py: No such file or directory\nsed: can't read work/build24m4z4/e2_final.py: No such file or directory\nrg: work/tree_r1c/student_pilot/checkpoint_budget.py: No such file or directory\nrg: out/LAUNCH_CARD*: No such file or directory\n",resolution='Used the existing validate.py, e2_verified.py and checkpoint_space.py. No checks are claimed for absent paths.')])
write(D/'FAILURES.json',dict(local_suite_status='PASS',launch_verdict='NO-GO',unresolved=['Native completion marker has no stop intent before the final run report.','Embedded rr is not persisted if the shell exits before k/j.json:438.'],required_other_files='out/NEEDS_OTHER_FILE_24M4Z5.md',failures=failures,expected_fail_before=dict(log='work/build24m4z5/fail_before_final.log',output=(D/'fail_before_final.log').read_text()),cluster_killed_processes=[],real_GCS='NOT_RUN',real_2GiB_rate='NOT_RUN'))
lines=[
 'NO-GO for the complete launch request: two source-scope guarantees require the edits documented in NEEDS_OTHER_FILE_24M4Z5.md.',
 'The three kit-review findings are fixed; ten fail-before probes fail on 24m4z4 and pass on the new bytes.',
 'All required local suites pass, including ENOSPC, archive, current/legacy copiers, final retries, TERM/USR1, wrapper, E3 dry run and 20-object readback.',
 'Final publication retries all pending destinations in stop/export/log/archive/ordinary order; sessions and receipts are validated and atomic.',
 'The resumable protocol test retains completed parts and resumes an interrupted part without resending bytes; real GCS remains untested.',
 'The wrapper preserves its job name, forwards batch signals, publishes once after the child exits and returns the child status.',
 'Known embedded rc/rr survive the final archive; missing early-exit rr is null. Immediate stop identification needs a native stop marker.',
 'The 47-minute bulk window needs 100.18 MB/s with 25% headroom for a 113 GB checkpoint plus the conservative 113 GB export allowance.',
 'N and N_GO are resealed; the full 15cdc127 archive diff changes only four files and seals per N kit. Q, QD, rcj and tree 9d2bbb8a are unchanged.',
 'UPLOADS_24M4Z5, _GO and _E3 are separate and below 5 MB per file. The 2 GiB rate payload exists only in the pending Orchard job.',
 'The package contains out/work, excludes canonical trees, verifies its members and writes its checksum last.'
]
(O/'BUILD24M4Z5_REPORT.md').write_text('\n'.join(lines)+'\n')
print('Wrote manifests, usage, report and explicit NO-GO findings')
