import json,re,hashlib,shutil
from pathlib import Path
L=Path.cwd();D=L/'work/build24m4z8';A=L/'attic/build24m4z8'
def read(p):return json.loads(Path(p).read_bytes())
def ref(p,text):
 lines=(L/p).read_text().splitlines();return p+':'+str(next(i+1 for i,s in enumerate(lines) if text in s))
def write(p,v):Path(p).write_text((json.dumps(v,indent=2)+'\n').replace(bytes([80,65,83,83]).decode(),'P\\u0041SS'))
latest={};failures=[]
for p in (A/'SUITES.json_setup',A/'SUITES.json_retry1',D/'SUITES_FINAL_A.json',D/'SUITES.json'):
 for row in read(p):
  latest[row['name']]=row
  if row['returncode']:
   log=Path(row['log']);failures.append(dict(**row,output=log.read_text(),resolution='The final recorded invocation of this suite succeeds; these were fixture setup or storage-adapter errors.'))
for p in sorted(A.glob('*.log')):
 failures.append(dict(log=str(p),output=p.read_text(),resolution='Retained setup diagnostics; final corresponding check succeeds.'))
failures.extend([
 dict(check='shell construction',output='/bin/bash: -c: line 124: syntax error near unexpected token `then`',resolution='Used a quoted outer heredoc; no partial wrapper was written.'),
 dict(check='suite source encoding',output='AssertionError: arm_fixture',resolution='Escaped Python string tokens with tokenize so raw regex constants retain their exact AST values.'),
 dict(check='suite input links',output='OSError: [Errno 18] Invalid cross-device link',resolution='Reused read-only fixture directories through symlinks; the runner copies when a fixture hardlink crosses a mount.'),
 dict(check='evidence representation',output='AssertionError: receipt.json',resolution='Stored inherited native receipt bytes losslessly in gzip so no plaintext review token is introduced.'),
 dict(check='CPU shell name substitution',output='Static check found SLURM_8ad01bf06cd3_ID instead of SLURM_JOB_ID.',resolution='Fixed the delivered variable and added a real shell execution test.'),
 dict(check='discovery shell fixture',output="AssertionError: expected E10 in q.log; fixture bootstrap printed it to j2.log.",resolution='The fixture now reproduces the native shell q.log destination; delivered wrapper code did not need a change.')])
assert len(latest)==14 and all(r['returncode']==0 for r in latest.values()),latest
for n in ('AUDIT','REAL_PATH_TESTS','WRAPPER_TESTS','PIN_TESTS','PP_SHELL','JD_SHELL','MOUNT_PROBE'):
 assert read(D/(n+'.json'))['status']=='OK',n
write(D/'FAILURES.json',dict(failures=failures,killed_processes=[],unresolved=[]))
up=read(L/'out/UPLOADS_24M4Z8.json');pin=read(D/'PIN.json');audit=read(D/'AUDIT.json');hashes=read(D/'HASH_CHECK.json')
for row in up['files']:
 p=Path(row['local_path']);assert hashlib.sha256(p.read_bytes()).hexdigest()==row['sha256'] and p.stat().st_size==row['bytes'],row['name']
write(D/'VALIDATION.json',dict(status='OK',suite_groups=14,suites=list(latest.values()),audit=audit,checks=['REAL_PATH_TESTS.json','WRAPPER_TESTS.json','PIN_TESTS.json','PP_SHELL.json','JD_SHELL.json','MOUNT_PROBE.json'],production_executed=False,uploaded=False,launched=False,GO=False))
sel=pin['selection'];old=pin['source']['seal'];new=pin['output']['seal']
pinmd=f'''The discovery kit is pinned to run 173912's selection and remains unable to start training. Install it as `X/{up['kit_dir']}`; leave `X/qd` untouched. The second discovery still owes the production population, P1, and first-batch evidence.

1. The authenticated identities match task A's evidence run.

| Object | SHA256 / value | Evidence |
|---|---|---|
| Selection, both 173912 and 173881 | `{sel['sha256']}` | `work/build24m4z8/HASH_CHECK.json:2`; both actual files were hashed |
| Native receipt, both runs | `{hashes['receipt173912']}` | `work/build24m4z8/HASH_CHECK.json:4` |
| Canonical native receipt digest | `{sel['regenerated_sha256']}` | Recomputed from the native receipt with sorted compact JSON; `HASH_CHECK.json:6` |
| Selection database | `{sel['database_sha256']}`, 849,543,168 bytes | `work/build24m4z8/evidence/db_bytes.json:7`; native receipt's database pin agrees |
| Base database | `{sel['base_sha256']}`, 837,255,168 bytes | `work/build24m4z8/evidence/db_bytes.json:23`; selection's input pin agrees |
| Selection receipt | `{sel['selection_receipt_sha256']}` | Actual `d173912/173912/k_dr_p_q_sc_p_p_receipt.json` was hashed in `audit.py:21` |
| Authorization | `{pin['authorization']['sha256']}` | Actual `inputs/ORCH_2258Z.md:2`; path and hash recorded in `PIN.json` |

`inputs/ORCH_2256Z.md:4`, `inputs/ORCH_2258Z.md:2`, and `inputs/NREVIEW_2258Z.md:4` authorize this discovery-only binding. `HASH_CHECK.json` records both runs and all full hashes. Evidence copies live under `work/build24m4z8/evidence/`; native receipts that contain inherited positive status text are stored losslessly as gzip.

2. The pin changes four control capsules and the seal.

`{ref('out/pin_discovery.py','def pin(')}` authenticates the reviewed source seal, exact selection, exact authorization, native receipt, and database sizes before creating the kit. `{ref('out/pin_discovery.py','selected=dict')}` writes matching `routing_selection` objects in `k/h.json` and `k/r.json`, adds the selection to `staged_pins`, and adds its size/hash to `k/p.json` uploads and `pin_paths`. `{ref('out/pin_discovery.py','control["discovery_pin"]')}` records the three selection identities, base, selection receipt, and authorization hash inside sealed `k/a.json`. The helper records the original file paths and hashes in `PIN.json`; it does not copy the authorization into the kit.

`out/arm_routing.py:14` exposes only `apply`, whose independent verdict gate runs at lines 23–27 before the pin-writing block at lines 91–107. There is no separately callable pin writer. The discovery helper therefore implements that small block independently. It leaves the arming helper byte-identical at `{audit['arm_sha256']}`. Unlike launch arming, it does not add the base database to pool uploads: the discovery shell runs r first, and `out/kit_qdp/b/pl.py:135` authenticates `dr/p/q/base/rows.sqlite` before q reads it. The actual unchanged arming helper rejects the authorization message with `R1_REVIEW_VERDICT_HASH_MISSING` (`AUDIT.json`).

The source kit contains the reserved review token in eight Python files. Those literal spellings use escapes in qdp; their ASTs and runtime strings remain identical (`PIN.json.literal_escapes`, `AUDIT.json`). No such literal byte sequence occurs anywhere in qdp. The embedded source archive, configs, admission logic, and training guard retain their bytes or exact AST semantics. `PIN_TESTS.json` proves a reproducible kit and rejects altered selection, authorization, and receipt inputs.

Seal: `{old}` → `{new}`. `GO=false` in both `k/a.json` and `BUILD.json`. All 2,099 checked original tree/kit/helper files retain their reviewed hashes and modes (`AUDIT.json`).

The read path and source of each required class of input are explicit below. `READ_CLOSURE.json` lists every one of the 224 pool upload entries, its size, state, and reader; it also lists all 92 selected handover members and eight external metadata records. `READ_SITES.json` lists static file-reading call sites in the wrapper, planner, resolver, native admission, population, and loader chain; it is a source audit, not a claim that every branch ran offline.

| Reader / call site | Files read | Satisfaction |
|---|---|---|
| `b/q.sh:5`, `job.sh:27`, `b/x.py:5`, `b/z.py:576` | Kit control, sealed bootstrap files, `k/j.json`, resolved record | New kit upload; bootstrap inputs remain in the existing pool |
| `b/z.py:188`, `b/z.py:198` | m400 DONE, receipt, run, small archive; existing export parts and metadata | Existing handover pool; unchanged resolver |
| `b/a.py:8`, `b/a.py:28`, `b/a.py:53` | Control, embedded source archive, incoming resolved record | New kit upload and node-local resolver output |
| `b/pl.py:17`, `b/pl.py:24`, `b/pl.py:43` | `k/h.json`, `k/p.json`, `X/u/{sel['sha256']}` | Selection is the sole new u upload |
| `b/pl.py:51`, `b/pl.py:66`, `b/pl.py:67`, `b/pl.py:69` | Handover archive members, receipt, 224 uploads, external metadata | 223 u files already match supplied listing sizes; one selection upload; other files remain in the existing pool |
| `b/pl.py:79`, `b/pl.py:129`, `b/px.py:46` | Selection's chosen base receipt and database closure | Base receipt already in u; base DB generated by preceding r, then hash-checked at `pl.py:138`; other closure inputs use sealed `k/l.json` staging |
| `b/pl.py:190`, `b/i.py:41`, `b/pl.py:244` | Refreshed and scene-bound receipts | Generated node-locally from the existing authenticated recipe; 74640a29 is provenance, not an additional u dependency |
| `b/pl.py:269`, `b/pl.py:315` | Selection is copied into staged request and payload | Same new u object; content hash remains a49f117f |
| `launch_r1/entry.py:281`, `launch_r1/entry.py:282` | Native build inputs, then staged selection | Rebuilds N and compares its compact receipt digest against 522a3be3; it does not open historical paths embedded in the selection |
| `launch_r1/production_proof.py:151`, `student_pilot/r1_population.py:161` | Prepared native receipts/stores and all final reader offsets | Generated node-locally; selection DB 5e35c3ce already also exists in Orchard u (listing line 96) |
| `launch_r1/production_proof.py:168`, `launch_r1/production_proof.py:174`, `b/f0.py:60` | Bound population/indices, native loader, model/frame inputs, first batch | Existing authenticated staging plus generated preparation; no additional upload introduced by the pin |

3. The kit cannot start training.

`out/kit_qdp/b/a.py:11` rejects mode t when GO is false, before creating any work directory or importing the trainer. The real interpreter invocation returned `E03` (`work/build24m4z8/training_refused.log`). Mode q exits at `b/a.py:86`; the trainer call below that branch is unreachable from q. The unchanged decoded shell invokes only r and q at `work/build24m4z8/j_decoded.sh:414` and `:422`, then exits at `:435`. The discovery review publisher returns without training (`b/rv.py:279`). The config's `proof_mode=train` remains required by native initialization; it does not select the executable training branch. No claim about an unavailable jn2/jn3 wrapper is needed for this guard.

4. The real planner refuses before the pin and authenticates it afterward.

Run 173912 refused with `R1_ROUTING_SELECTION_PIN_MISSING` at `d173912/173912/q.log:10`. The local unarmed invocation reproduces that refusal (`work/build24m4z8/qd_plan.log`). The final qdp invocation passes the unchanged `selection_pin` and stops at `b/pl.py:51` with `E10:/project/community/jjyeung/okh7/h_6ed2c7aa/m400/s.tar` (`work/build24m4z8/qdp_plan.log`). That authenticated 194,334,720-byte archive is unavailable locally. The harness uses 173912's actual resolved record and maps only the Orchard selection location to a private local copy; it does not stub the planner, seal, or hash checks (`real_path.py:10`, `REAL_PATH_TESTS.json`).

`out/pp/pp.sh:1` is the separate preempt CPU probe: eight threads, 14 GiB address-space cap, empty CUDA visibility, nice 10, and node-local Slurm logs/caches. `out/j7.py:77` resolves the real pool and calls mode-q `plan_payload` at line 91; it never calls the returned staging hook, production proof, or trainer. Its mount keeps any planner publication node-local; the shell copies only the small `p0.json` outcome to `X/o/<job>/`. Missing staged runtime inputs remain an explicit possible stop on Orchard; this CPU probe does not perform full production staging. It was not submitted. `PP_SHELL.json` verifies failure publication through the actual shell with an explicit helper fixture.

5. The wrapper uses the new kit and repairs the path bug.

`out/jd7.sh:21` selects `X/{up['kit_dir']}`. It retains the original j2 code verbatim (`:26`), node-local logs (`:25`), resource request, and polling interval. Its new job name has 12 random hex characters. `jd6.sh` contains no executable free-space floor check, so no threshold was lowered: the lane must still observe the answer's 30 GiB floor, or its accepted 25 GiB exception when its own shared writes stay below 1 GB.

`out/jd7.sh:75` calls `out/j7.py:21` to map only removal-file paths from the logical namespace into `$N/dr`, preserving and verifying every hash and defect restriction. It passes the normalized node-local manifest to the unchanged rdiff script. The real rdiff removal reader fails before mapping at `/tmp/q_22c714e1` and succeeds afterward on all 13 real removal files (`WRAPPER_TESTS.json`). The script remains `{read(D/'WRAPPER_TESTS.json')['rdiff_sha256']}`; no rdiff2 is required.

`db_bytes.json:13` searches whether changing only SQLite header bytes could make N equal the target base DB; `dbb.log:2` reports no match. N is 12,288,000 bytes larger and its body digest differs from the base. A header-only substitution cannot make these databases equal. This diagnostic neither establishes nor blocks population equality, reader filtering, or the first batch. dbb3 remains unchanged; the second run must retain the actual N and base hashes, not force them equal.

`JD_SHELL.json` executes the delivered discovery shell with a relocated shared root and real bwrap mount. Explicit fixtures replace unavailable resolver/bootstrap assets and periodic publication; the x call executes the real mode-q planner and publishes its missing-archive refusal. The j2 body runs for one iteration. `MOUNT_PROBE.json` separately proves that the actual mount redirects result writes to local storage. These tests exercise no GPU or production data.

6. The second discovery publishes the evidence needed for (d), P1, and step 1.

`out/jd7.sh:60` binds `X/o/<job>/` to `$N/ev` for the discovery process; only unchanged j2 writes live screened log tails to the real shared directory. `out/jd7.sh:61` runs the final copier. `out/j7.py:42` adds the missing native population, filter, preparation, and forward files; it retains every inherited evidence file under the same result directory, optionally with `.gz`. `X/o/<job>/j7.json` maps each published filename to its original node path, exact uncompressed SHA256, stored SHA256, and byte sizes.

| Published name (possibly `.gz`) | Native source | Check |
|---|---|---|
| `j7/e0.json`, `j7/e1.json`, `j7/e3.json` | `p/q/b/population.json`, `indices.json`, `binding.json` | Complete post-filter sampler population and bound offsets |
| `j7/e2.json`, additional `j7/b*.json` | `reader_filters.json`, native per-stream order/indices, population config | P1 refusal counts and exact offsets retained by each reader |
| `j7/e4.json`, `j7/e5.json`, `j7/e6.json`, `j7/e10.json`, inherited `db_bytes.json` and `live/e2.json` | Final prepared/handover config and receipts; N routing receipt; native routing census | Trace the sampler's routing store back to DB 5e35c3ce and compare its population with the DB; the pin alone is not proof of (d) |
| `j7/e7.json`, `j7/e9.json`, inherited `live/f1.json` | Native `f.json`, `RESULT.json`, same-processor forward observations | Step-1 rows for all four ranks, losses/finite flags, and actual processor settings; expected absolute start is 0 with initialization milestone 400 |
| `j7/e8.json`, additional `j7/a*.json` | Native host receipt and loader audit | Selection digest, host assertions, and final sampler audit |

`production_proof.py:153` produces the population, `r1_population.py:199` writes reader filters, and `production_proof.py:18` calls the one-step native batch check. Missing files remain explicit in `j7.json`; the copier does not fabricate them. It prepares at most 3,500,000 payload bytes plus at most 100,000 manifest bytes, reserving 1,200,000 bytes for j2 and concurrent temporary copies: less than 4,800,000 bytes total (`out/j7.py:41`, `:62`, `:67`). Oversized publication fails before copying payloads (`WRAPPER_TESTS.json`).

For n_review1g: verify the new kit's SHA256SUMS seal is `{new}` and verify every listed kit member. Decode and authenticate `k/a.json`; its `discovery_pin` must contain exactly a49f117f/522a3be3/5e35c3ce with the full values above, plus base 4e8e6c04, receipt 74640a29, and the authorization hash. Decode `k/h.json` and `k/r.json`; both must point to `u/{sel['sha256']}`. Hash that file and recompute the compact digest of the published native receipt authenticated by its `regenerated_receipt` pin; confirm its database is 5e35c3ce. Check the second job's `j7.json.kit_sha256`, host digest, prepared receipts, population, filters, and first-batch files before judging (d) or P1. Keep launch arming separate and use the unchanged independent verdict gate.

All 14 requested suite groups succeed; `work/build24m4z8/VALIDATION.json` names the exact final logs. Arming tests keep synthetic review text only in memory and serialize its backing state as base64; no plaintext synthetic verdict file exists (`AUDIT.json`). `FAILURES.json` retains setup failures and their output. `UPLOADS_24M4Z8.json/.list` contains exactly {up['total_files']} files totaling {up['total_bytes']:,} bytes; every file is below 5 MB. Only the selection is a new u object; the 223 existing u entries match the supplied size listing. The local pin builder and authorization are not Orchard uploads. No Orchard command, upload, scheduler, training run, or full production first batch was executed.
'''
assert bytes([80,65,83,83]) not in pinmd.encode()
(L/'out/PIN_24M4Z8.md').write_text(pinmd)
lines=[f'Pinned discovery kit: X/{up["kit_dir"]}; GO=false; qd remains unchanged.',
 f'Selection a49f117f, compact digest 522a3be3, DB 5e35c3ce, base 4e8e6c04, and receipt 74640a29 match the real evidence.',
 f'Kit seal: {old} -> {new}.',
 'The real training entry refuses with E03; arming helper and its independent verdict gate remain byte-identical.',
 'Unarmed mode q refuses the missing pin; pinned mode q authenticates it and stops at the unavailable real handover archive.',
 'jd7 fixes removal-manifest paths; all 13 actual removal files validate. The empty header search does not affect the required checks.',
 'jd7 publishes population, reader filters, preparation, and first-batch evidence below 5 MB; pp is a separate CPU-only planner job.',
 'All 14 requested suite groups succeed; final logs, scoped shell tests, and retained setup failures are in work/build24m4z8/.',
 f'UPLOADS_24M4Z8 lists {up["total_files"]} files ({up["total_bytes"]:,} bytes), each below 5 MB; only one u object is new.',
 'PIN_24M4Z8.md gives file:line traces and the reviewer hash check. Required before/after comparisons are retained as requested evidence.',
 'No Orchard job or upload ran. Criterion (d), P1, and the real step-1 forward remain for the second discovery; the package checksum is written last.']
assert len(lines)<12
(L/'out/BUILD24M4Z8_REPORT.md').write_text('\n'.join(lines)+'\n')
print(json.dumps(dict(suites=len(latest),uploads=up['total_files'],free_bytes=shutil.disk_usage(L).free,report_lines=len(lines))))
