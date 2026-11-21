from pathlib import Path
import base64,json,hashlib,re
J=Path.cwd();D=J/'work/build24m4z10';O=J/'out';E=O/'e3'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):
 v=json.loads(p.read_bytes());return json.loads(base64.b64decode(v['payload'])) if isinstance(v,dict) and 'payload' in v else v
def write(p,v):p.write_text(json.dumps(v,indent=2,sort_keys=True)+'\n')
baseline=load(D/'BASELINE_FILES.json');delta=load(D/'DELTA.json')
objects=load(O/'kit_n/k/y.json')['objects'];assert len(objects)==28
names=[v+'.j<job>'+f'.part{i:02d}-of-04' for v in objects.values() for i in range(4)]
used=[objects[k]+'.j<job>'+f'.part{i:02d}-of-04' for k in ('ckstop','m100','o','u') for i in range(4)]
for root in (E,O/'tgcs'):
 (root/'SESSION_NAMES.template.list').write_text('\n'.join(names)+'\n')
 status=used if root==E else [objects[k]+'.j<job>'+f'.part{i:02d}-of-04' for k in ('ck00','ckstop','m100','o','u') for i in range(4)]
 (root/'STATUS_NAMES.template.list').write_text('\n'.join(status)+'\n')
files=['b/o.py','b/pc.py','b/pc.sh','k/y.json','SHA256SUMS.txt','BUILD.json']
def entry(p,name,old=None):
 assert p.stat().st_size<5_000_000
 return dict(name=name,relative_path=str(p.relative_to(J)),local_path=str(p),bytes=p.stat().st_size,sha256=sha(p),mode=format(p.stat().st_mode&511,'04o'),baseline_sha256=old,action='replace' if old else 'add')
normal=[entry(O/'kit_n'/n,'n/'+n,baseline['work/build24/kits/n'][n]['sha256']) for n in files]+[entry(O/'jn3.sh','jn3.sh')]
go=[entry(O/'kit_n_go'/n,'n_go/'+n,baseline['out/kit_n_go'][n]['sha256']) for n in files]
e3=[entry(E/n,'e3/'+n) for n in ('e3.sh','e3.py','observe.py','run.sh','k.tgz','pins.json','trinity.sh','trinity.py','readback.py','SESSION_NAMES.template.list','STATUS_NAMES.template.list')]
for suffix,rows,armed in (('',normal,False),('_GO',go,True),('_E3',e3,False)):
 stem='UPLOADS_24M4Z10'+suffix
 write(O/(stem+'.json'),dict(build='24m4z10',files=rows,GO=armed,uploaded=False,launched=False,training_gate='NO-GO',total_bytes=sum(r['bytes'] for r in rows),tree_sha256=delta['tree_sha256'],baseline='24m4y2 reviewed overlay'))
 (O/(stem+'.list')).write_text(''.join(r['name']+'\n' for r in rows))
table='| Destination relative to X | Bytes | SHA256 |\n|---|---:|---|\n'+''.join('| '+r['name']+' | '+str(r['bytes'])+' | '+r['sha256']+' |\n' for r in e3)
usage='''E3 uses the sealed N kit with GO=false. Its offline strict-sink checks pass; real-service throughput and resume remain to be measured. The bundle requires 112 session names (108 + 4 for the final upload log).

Upload the following files beneath X=/project/community/jjyeung/okh7/x_22c714e1. Each file is below 5 MB.

'''+table+'''
On trinity-1-18, the lane can first run the real-session interface:

    bash out/e3/trinity.sh <job_id> <sessions_file> <fresh_output_under_scratch>

The Trinity mode stages a 3 MiB checkpoint-like payload and 3 MiB export, uses a private root and a full 16 MiB tmpfs, and leaves E3.json plus logs under the supplied output directory. The build tested this exact interface with fake sessions and a method-only strict-sink adapter. This build used no network.

The Orchard CPU test requires hold, mint, release:

    sbatch --hold "$X/e3/e3.sh"
    # Install the complete fresh session mapping for the returned numeric job ID.
    scontrol release <job_id>

The job requests preempt, four CPUs, 16G and one hour. Its name is a15_cot_ap86b407cde192. Allow under one minute to submit held, 5–10 minutes to mint/install, and under one minute to release; queue time is unknown. Mint every name in SESSION_NAMES.template.list after replacing <job> with the allocation ID. Install X/n_s/sess_<job>.json with directory mode 0700 and file mode 0600, owned by the job user. Never print session values. Every cache use requires the exact 112-name set.

The Orchard job creates a 2 GiB random checkpoint-like payload on node-local disk. The build never creates that payload on Trinity. The job uploads ckstop, m100, o and u, four parts each, while X has zero free bytes. It verifies returned name, generation, size and MD5 against receipts and local SHA256; the readback tool also checks CRC32C. The u object contains the final upload diagnostics, including archive attempts and later data retries. Its four 512 KiB parts total 2 MiB; concatenate them in part order. Blank lines pad the two log snapshots. Part 0 becomes durable after the archive attempt, and parts 1–3 carry the final tail. The terminal response to u itself is verified through its receipt and remote metadata.

The observer patches methods on the original HTTPSConnection class. Its socket-free constructor check runs in each observer process. On ckstop part00, the observer closes the connection and raises a controlled interruption after GCS acknowledges a nonfinal chunk. A subsequent status query must return that Range, a subsequent data request must start at the acknowledged offset, and the part must finish with a valid receipt. E3.json records these events in resume_real, including real_service. Only status=PASS with real_service=true can justify the 1.5x stop-window factor. Offline PASS with real_service=false is protocol evidence only.

The real 2 GiB test uses the copier's normal 8 MiB chunks. Small Trinity/offline payloads use aligned 256 KiB chunks so a part has a nonfinal prefix. E3 records per-part receipt seconds and MB/s, total duration from the first part's start to the last part's completion, final-pass duration, SLURM_TMPDIR and free bytes. Total duration includes the forced retry delay. The interrupted part's receipt duration describes its successful resumed attempt; consult resume_real.events for its preceding attempt. No measured fixture rate is a real GCS rate.

STATUS_NAMES.template.list lists the 16 consumed part names, including all four u parts. The complete preparation set is 112 names. For independent remote readback on the credentialed node:

    python3 -I -s -B readback.py E3.json --bucket <bucket>

The readback tool performs serial, generation-pinned requests with an 8 MB/s limit and keeps credentials out of arguments and output. No real readback ran in this build.
'''
(E/'E3_USAGE.md').write_text(usage)
pc=(O/'kit_n/b/pc.py').read_text().splitlines()
def line(fragment):return next(i+1 for i,s in enumerate(pc) if fragment in s)
initial=load(D/'SEALS_INITIAL.json')
seals=[dict(kit=r['kit'],old=r['old'],new=sha(J/r['kit']/'SHA256SUMS.txt')) for r in initial if r['kit'].startswith('out/')]
write(D/'FINAL_SEALS.json',seals)
report='''The offline build passes. Training remains NO-GO until the lane measures the historical checkpoint write time W and the real E3 rate R, checks the stop-window formula, and reviews any resulting constant change. No real-service run or training job was submitted.

| Finding | Fail-before on 24m4z7 | Pass-after on this kit | Evidence |
|---|---|---|---|
| 1. Late stop upload | Nominal and explicit-stop checkpoints have no stop receipt before the export/report. A forecast stop re-sends an already uploaded checkpoint. | The nominal and signaled checkpoint uploads start without either marker. Forecast stops reuse the ordinary object's receipts and send zero checkpoint bytes again. X is full throughout the actual shell EXIT path. | work/build24m4z10/findings_final/RESULT.json; policy/RESULT.json |
| 2. Stop budget | The sealed constant is 3,600 s; no measured W/R pair establishes a safe window. | set_stop.py validates the allowed range and changes only the constant plus seals on copies, 3600 -> 6000. Native checkers pass and GO is unchanged. This is a tooling pass, not proof that 3,600 s is sufficient. | work/build24m4z10/findings_final/setting/; findings_final/RESULT.json |
| 3. Observers | Both socket-free constructors fail; the old tgcs observer produces no receipts through the actual exit path. | Both observers retain the stdlib class, patch methods, and construct HTTPSConnection('example.invalid',443,timeout=1). The full-X tgcs exit control has 16 valid receipts. | work/build24m4z10/findings_final/RESULT.json; tgcs_observers_pass/RESULT.json |
| 4. Durable final diagnostics | No final diagnostic object exists, and the frozen archive omits its upload attempts. | Four u parts contain a capped, masked 2 MiB log, including archive failure/success and every later data retry. The fixture compares all preceding non-u upload-log lines against sink bytes. | work/build24m4z10/findings_final/diagnostics_after/; findings_final/RESULT.json |
| 5. Strict ranges | bytes */not-a-size returns 308. | Malformed query/chunk/Range forms return 400, including completed sessions, duplicate headers and invalid numeric forms. Current, legacy, archive, ENOSPC, core, advanced, exit, E3 and tgcs suites pass with this sink. | work/build24m4z10/findings_final/RESULT.json; SUITE_RESULTS.json; SUITES_FINAL.json |
| 6. New E3 bytes | The old observers fail and provide no real-resume proof. | k.tgz exactly matches the new GO=false kit; pins, 112 names and usage agree. E3 passes 17 offline checks, forces interruption/resume, and the real Trinity entry point passes with a fake session file. Real throughput/resume are NOT RUN here. | work/build24m4z10/e3_sealed/RESULT.json; trinity_pass/RESULT.json |

The before/after comparisons above are requested controls. They retain the old bytes to establish each failure rather than describing an implementation history.

The stop checkpoint is written on node-local disk: job.sh:20 places N under SLURM_TMPDIR or /tmp; b/pl.py:221 and :226 set the effective output to p/q/r; decoded k/j.json:403 binds Q_ROOT at Q_NS. student_pilot/carrier_c1_run.py:2452 writes checkpoint_<step> there, and :2014 publishes complete.json after the payloads are fsynced. It does not write the checkpoint to /project. The copier's claims, spool, receipts and final log are local too. The decoded launch is retained at work/build24m4z7/launch.sh.

'''
report+=f"b/pc.py:{line('def nominal_stop')} reads wall_seconds and stop_before_seconds from the decoded recipe. b/pc.py:{line('def stop_marker')} compares complete.json mtime against the nominal threshold or stop.request mtime. The request-time marker is preserved by b/pc.sh:7. The live copier recognizes these checkpoints without waiting for an export or run report. Ordinary uploads are held after a stop request or the nominal threshold, including inside the writer. The 6,000-second copy test proves the threshold follows the encoded recipe rather than 82,800 hardcoded seconds.\n\n"
report+='''Known limit accepted by ORCH: a forecast self-stop earlier than the nominal threshold is identifiable only after run_*.json appears. If that checkpoint already has a complete ordinary upload, ckstop.json and its _stop.done receipt refer to the existing object and its four receipts; the dedicated ckstop sessions remain unused. The ordinary checkpoint is never re-sent in this case.

The budget rule is 2 x (W + B/R) + 150 s <= stop_before_seconds - 15 s. W is the measured checkpoint write time, B the transferred bytes, and R the measured real-service bytes/s. Use 1.5 x (W + B/R) + 150 s only after real E3 reports a successful resumed part (resume_real.status=PASS and real_service=true). For the whole stop sequence, include the export's measured write/preparation time and bytes in W and B as well. The checkpoint planning size is 113,000,000,000 bytes; the export size remains unmeasured. The archive reserve is 150 s, including up to the last 10 s for u. Its sizing basis is 50 MB at 1 MB/s with a factor of three; the final diagnostics share that reserve.

Choose S = 300 * ceil((factor * (W + B/R) + 165) / 300). The helper accepts only multiples of 300 within [3600,10800]. Run out/set_stop.py S on the final kit directory only after the measured inputs support S; this build does not invoke it on the shipped kits. The training-time cost is S - 3600 seconds, or (S - 3600) / measured_seconds_per_step steps. No write rate, step rate or safe numerical S is invented. The supplied 16 small real-GCS receipts verify the z7 local bytes, not a full-scale transfer, full-X run, or new-byte resume. Historical R1/H1-1/D0 checkpoint timing logs were not supplied in the named evidence. Their checkpoint_seconds samples are needed; the trainer records that duration at :2454 after the write at :2452.

The shipped recipe remains wall_seconds=86400 and stop_before_seconds=3600 at k/n.json:1 (decoded work/build24m4z7/config.json:448–449). Nominal stop is TK_JOB_START+82800. The allocation deadline is end minus 15 s, so the nominal window is 3585 s and the primary window before the shared reserve is 3435 s. These durations are configuration facts, not evidence that the 113 GB checkpoint fits.

The final log uses label u and four fresh allocation-specific sessions, making 112 names (108 + 4). Its first 512 KiB part is immutable after the archive attempt; the remaining 1536 KiB contain a final snapshot and are frozen before their retries. The log retains capped tails, masks URLs, and never changes a completed part. It includes the archive's own attempts and subsequent checkpoint/export retries. Its own terminal upload response cannot be embedded in its prior bytes; GCS metadata and the local receipt represent that response. The strict-sink test checks all preceding non-u log lines, including the forced archive retry.

'''
report+='| Kit | z7 seal | New seal |\n|---|---|---|\n'+''.join('| '+r['kit']+' | '+r['old']+' | '+r['new']+' |\n' for r in seals)
report+='''\nThe full archive diff streams all 192,840 baseline members from SHA256 15cdc1273ff7a1c794c79c895505d08a5a1e325b21029d3606eac999f5efa181. It changes only b/o.py, b/pc.py, b/pc.sh, k/y.json and the two seals per N kit. Q, QD, rcj and both trees are byte-identical; the tree remains 9d2bbb8ad209d91e21e56121785f62b0dddf3c8d9f14db8d23daf6dcd1d3591b. N and N_GO differ only in k/a.json and seals. gc.py, the trainer, admission and preparation are unchanged.

The final gates include the eight current tests, four archive tests, five legacy tests, ENOSPC recovery/refusal, signals, wrapper forwarding/exception/wait-race checks, seven core controls, eight advanced checks, final-loop retries, readback, both tgcs controls, E3 and the Trinity interface. FAILURES.json retains resolved fixture/setup failures with output. No SSH, network, Orchard submission, GPU work, Git, tmux, scheduler or other agent ran.

Card: use hold, mint/install 112 fresh sessions, then release the CPU E3 validation. Keep training held until measured W and R satisfy the formula and the constant-only review is complete. The copier recognizes nominal/signaled checkpoints before the report; early forecast stops retain the documented report-time limit and reuse completed ordinary uploads.
'''
(O/'ENOSPC_24M4Z10.md').write_text(report)
(O/'NEEDS_OTHER_FILE_24M4Z10.md').write_text('''The requested copier, observer, diagnostic-object and strict-sink changes fit the allowed files. No trainer or admission file was changed.

The accepted forecast-stop limit remains at work/tree_r1c/student_pilot/carrier_c1_run.py:2451 and :2014: an early stop decision has no marker before checkpoint/export completion. Guaranteeing early forecast identification before the report would require a trainer marker there; ORCH accepted the existing limit, so that change is not part of this build.

The numerical stop-window decision needs measured checkpoint_seconds from the historical R1/H1-1/D0 logs (written by the trainer at :2454) and a real E3 result. These measurements are absent from the named input evidence and cannot be produced by an offline copier edit. out/set_stop.py can change k/n.json:1 in N and N_GO, after measurement, without changing any other decoded recipe key or GO. The shipped constant remains 3600.
''')
short=[
'Offline build PASS; training remains NO-GO pending measured W/R and the stop-window decision.',
'The nominal/signaled stop path starts without an export/report; forecast stops reuse completed ordinary receipts.',
'The shipped stop constant remains 3600; set_stop.py passes 3600 -> 6000 copy-only tests and invalid-input refusal.',
'Both observers patch methods; strict range negatives, full-X exit controls and all regression suites pass.',
'The final upload log uses four u parts; the preparation set contains 112 names (108 + 4).',
'E3 contains the new GO=false kit and passes 17 offline checks, including forced resume; Trinity fake-session mode passes.',
'The full 15cdc127 archive diff changes only the four allowed files and seals per N kit; other kits and trees match.',
'ENOSPC_24M4Z10.md records seals, evidence, the measured-input formula and accepted limits.',
'UPLOADS_24M4Z10{,_GO,_E3}.json/.list give exact files and hashes; FAILURES.json preserves resolved failures.'
]
(O/'BUILD24M4Z10_REPORT.md').write_text('\n'.join(short)+'\n')
(O/'tgcs/READY').write_text('24m4z10 method observer; exact 112 sessions; offline full-X path PASS; real service NOT RUN by build\n')
print('Reports, upload manifests and 112-name templates written')

(E/"TRINITY_READY").write_text("READY: 17 offline checks and the Trinity fake-session interface pass.\n112 session names; 16 consumed part receipts; 3 MiB local payloads.\nThe Orchard CPU job uses a 2 GiB payload. Real-service execution is reserved for the lane.\n")
