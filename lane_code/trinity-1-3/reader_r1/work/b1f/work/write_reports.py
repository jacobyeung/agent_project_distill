from pathlib import Path
import hashlib,json,re
W=Path.cwd();O=W/'out';B=W.parent/'b1p/out'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
token=(O/'TOKEN').read_text().strip();public=json.loads((O/'package/0.json').read_text())
ab=json.loads((O/'MEMO_AB.json').read_text());baseab=json.loads((O/'BASELINE_AB.json').read_text())
assert all(x['output_sha256']==baseab['modes']['off']['output_sha256'] for x in ab['modes'].values())
timing=json.loads((O/'TIME_PRICE.json').read_text());delta=json.loads((O/'DELTA_AUDIT.json').read_text());gate=json.loads((O/'EAT1_GATE.json').read_text())
hashes=dict(token=token,base_payload_sha256=sha(B/'0.tgz'),payload_sha256=sha(O/'0.tgz'),plan_sha256=public['plan_sha256'],
 package_sha256=sha(O/'package/PACKAGE.json'),delivery_sha256=sha(O/'1.tgz'),operator_sha256=sha(O/'tower_sequence.py'),
 batch_sha256=sha(O/'package/BATCH.sh'),read_plan_sha256=sha(O/'READ_PLAN.json'),node_check_sha256=sha(O/'node_check.py'),
 export_pin_sha256=sha(O/'export_544.json'),inputs_sha256=sha(O/'inputs_tower.json'))
(O/'DELIVERY_SHA256.json').write_text(json.dumps(hashes,indent=2)+'\n')
ops=(B/'OPERATIONS_TOWER.md').read_text().replace('e47d0593fefec',token).replace('1a60c9826f8d3d49081930e12dcf5434a3a876af805c2570585c7c29d4b98c03',hashes['delivery_sha256'])
ops=ops.replace('--job-name=a15_cot_ap'+token+'c','--job-name=a15_cot_ap'+token)
ops=ops.replace('# Step-544 two-read operator kit','# Two-read operator kit')
ops=ops.replace('Package `'+token+'` requests one GPU on `general`. These commands have not run.',
 'Package `'+token+'` requests one GPU on `general`. These commands have not run. The strict zero-new-findings static gate has not passed: EAT-1 adds 17 bookkeeping flags and no A4 flags. Read `EAT1_GATE.json` before any release decision.')
start=ops.index('The conservative estimate is');end=ops.index('\n\nGPU price',start)
ops=ops[:start]+'''The segment-local estimate is **4.95 hours of reads**, or **5.95 hours including 30 minutes for staging/loading and the 30-minute stop margin**. Full coverage does not fit the five-hour cap under this estimate. The stop and return margins overlap: admission stops 30 minutes before the deadline, draining ends 20 minutes before it, and return uses the final 20 minutes.

A hypothetical single worker with shared capture values would need 3.84 hours of reads, or 4.84 hours with the same allowances. The production runner starts a new worker for every type, so this kit keeps one process per segment. It cannot reuse read 0's distance encodings in read 1. Estimates assume no eviction and do not credit unmeasured SAM savings; they are not live GPU measurements.

Read 0 uses `perception_memo=verify`, `perception_memo_verify_reads=30`, and `perception_memo_verify_types=["object_abs_distance"]`; its later reads use effective mode `on`. Read 1 uses `perception_memo=on`. Each process may retain up to 64 GiB of array/tensor payload. The first 30 distance items span 11 captures in the registered order. Items are not reordered. The policy is identical across read 0's segments and enters each journal binding. On resume, verification follows the original item ordinal. Each read starts fresh perception after a process-wide verification mismatch. The mismatch and every verified hit are recorded under `output.perception_memo` in the ordinary item journal.''' + ops[end:]
ops=ops.replace('The inputs change only type selection and retain a null resume.','The inputs remain byte-identical to W2 and retain a null resume. The operator wrapper seals the memo schedule.')
ops=ops.replace('All part hashes, byte counts, preparation pins, environment pins, policy paths, and inventory declarations remain those in bf94\'s step-544 inputs.',"All part hashes, byte counts, preparation pins, environment pins, policy paths, and inventory declarations remain those in W2's step-544 inputs.")
ops=ops.replace('W2/work/f/','W3/work/f/').replace('locally in W2','locally in W3').replace('/work/b1p\n','/work/b1m\n')
ops=ops.replace('--own in/h10own/170631/items.jsonl in/h10own/170706/items.jsonl in/h10own/170694/items.jsonl',
 '--own ../b1p/in/h10own/170631/items.jsonl ../b1p/in/h10own/170706/items.jsonl ../b1p/in/h10own/170694/items.jsonl')
ops=ops.replace('and the tower selector socket with stub weights.','the explicit memo/rule settings, and the tower selector socket with stub weights.')
(O/'OPERATIONS_TOWER.md').write_text(ops)
rows='\n'.join(f"| {k} | `{hashes[k]}` |" for k in ('base_payload_sha256','payload_sha256','plan_sha256','package_sha256','delivery_sha256','operator_sha256','batch_sha256','read_plan_sha256','node_check_sha256','export_pin_sha256','inputs_sha256'))
mode_rows='\n'.join(f"| {m} | {v['seconds_per_read']:.4f} | {v['g3t_calls']} | {v['sam_encode_calls']} |" for m,v in ab['modes'].items())
time_rows='\n'.join(f"| {name} | {v['g3t_calls']} | {v['read_hours']:.3f} | {v['total_hours_with_staging_stop_margin']:.3f} | {'Yes, conditionally' if v['fits_with_stop_and_return_margin'] else 'No'} |" for name,v in timing['case'].items())
report=f'''Package **{token}** adds an in-memory perception memo to e47d0593fefec. The default is `off`. CPU tests prove identical responses, answers and scores for `off`, `on` and `verify` on the supplied deterministic fixture; `off` also matches the base payload. The 600-run replay has zero mismatches.

**The package is a review deliverable, not an all-gates-passed release.** The strict EAT-1 zero-new-findings gate is not met: its raw comparison adds 17 A3 bookkeeping findings and no A4 findings. Manual review finds no new rule that changes a response value. The raw findings and explanations remain in `EAT1_before.json`, `EAT1_after.json`, `EAT1_DELTA.json`, and `EAT1_GATE.json`; no allowlist was changed. No job was submitted.

**Artifacts and identity**

The sole new token is `{token}`. The delivery is `1.tgz`; its payload is `0.tgz`. The payload changes nine memo or wiring files plus `9.json`; the other {delta['unchanged']} members remain byte-identical to W2. `PATCH.diff` and `FILE_SHA256_DIFF.tsv` compare directly against W2's e47d0593fefec `0.tgz`.

| Artifact | SHA256 |
|---|---|
{rows}

The production builder retains its tar format, pinned inventory, admission, restore, five-hour limit and transport. The wrapper and CPU helper are authenticated in `PACKAGE.json`. The delivery includes the unchanged W2 input declarations and export pins. The fixed private logical namespace remains unchanged because the existing policy receipt binds it. Orchard job names use `a15_cot_ap{token}`.

**Memo contents and keys**

`b/e2e_reader/perception_memo.py` owns the store. G3T memoizes the entire fresh dictionary: raw poses, depth, confidence, points, grid coordinates, anchor slots, frame indices and source size. Those values depend on the input frames and frozen tower only. The grid coordinates, index arrays and source size need no additional store because they already travel in that dictionary.

SAM memoizes only the anchor-image feature pyramids and image sizes. These values precede text grounding. Its ownership marker is reattached to the current SAM instance; the tower and its mutable backend are never copied into the store. The stage-1 detector still executes text grounding, mask production, linking, featurization and selection for each read and name.

The SHA256 key uses typed, length-delimited input encoding. It covers every component file's pinned relative path, SHA256 and size; device, dtype/precision, dense and anchor counts, G3T depth chunking, SAM batching configuration; each image's mode, size, palette when present and every raw pixel byte; and all frame index/slot lists. Lazy file-backed PIL frames are rejected. A new object with identical content hits; changed bytes, index lists, configuration or weight pins miss. Selector rules, questions, names, tokens and prefill state do not enter the key.

Own gravity, own-depth scale, geometry derived from those heads, question-dependent SAM detections, selector outputs, responses and scores remain fresh. A dedicated test changes prefill depth on identical frames: G3T hits once while the printed response and scale change. Another test crosses selector rules without changing the G3T key.

The store copies arrays and tensors on insertion and return, preserving dtype, shape, device and bytes. Tensor copies stay on their existing device. Byte comparison also distinguishes signed zeros and preserves NaN payloads. Mutating a returned array or feature tensor cannot alter subsequent hits. The configured limit controls eviction only. It counts retained array/tensor payload plus basic scalar content, not Python allocator overhead or transient copies. The API default is 16 GiB; this kit requests 64 GiB per worker. Eviction can reduce reuse.

The memo performs no file IO, creates no files, and uses no shared memory or interprocess service. Its state is process-local; inherited owners detect a changed PID and start empty. Tests simulate that transition. Fresh model calls retain their existing artifact-bound weight loading; the no-IO claim concerns memo operations, not initial model restore.

**Switch and binding**

- `off`: call the original fresh path, with no memo event field or response changes.
- `on`: reuse defensive copies after a matching key; misses compute fresh.
- `verify`: recompute every hit and compare all arrays/tensors and scalars exactly. Each hit records module, key prefix, equality, fresh seconds and hit seconds. The first mismatch disables every memo policy for the rest of that process, clears stored values and serves the fresh result.

Read settings bind the switch, byte limit, verification count and optional type scope. Launcher environment bindings, settings digests and runner identities include them. Resume, tower reuse and shard merge reject different memo settings. The pairing helper also checks memo identity. Low-level APIs default to `off`; prepared production settings explicitly contain both `stage1_select_rule` and `perception_memo`, and a missing key fails instead of silently defaulting.

The operator keeps the existing order: distance under `null_argmax`, distance under `candidates_argmax`, camera displacement, camera rotation, camera movement direction, then room. Read 0 has 636 items; read 1 has 150. Their identities and journals remain separate. Read 0 binds `verify`, 30 reads and a distance-only verification scope. Its cameras and room therefore use effective `on` while retaining the same policy identity. Read 1 binds `on`. Stable selected-item ordinals preserve the first-30 rule on resume. The registered first 30 distance items cover 11 captures, giving 19 verified G3T hit recomputations under ideal reuse. No items were reordered.

The production runner invokes and waits for a new subprocess for each type. It exposes no persistent worker interface for multiple logical reads. This kit therefore keeps one process per segment. The memo does not span segments or reuse read 0's encodings in read 1. Changing the worker lifecycle remains outside this switch.

**CPU proof**

The A/B fixture runs 30 reads over five captures through `generate_real`, the real decode loop, CallHook, OwnDepthScale, geometry conversion, StageOne, stage-1 socket, grounding session, response formatter, servers and scorer. G3T, SAM's frozen backend, the carrier forward and the selector head are deterministic stubs. Every read uses all 32 anchor frames and fresh image objects. The carrier emits camera, two ground and one gap call. These are CPU fixture timings with two-millisecond fresh-module delays, not measured GPU speedups.

| Switch | Stub seconds/read | G3T fresh calls | SAM encode calls |
|---|---:|---:|---:|
{mode_rows}

W2's `off` fixture took {baseab['modes']['off']['seconds_per_read']:.4f} seconds/read. All four response/answer/score serializations share SHA256 `{baseab['modes']['off']['output_sha256']}`. `verify` recorded 50 matching hits, 25 per module. `MEMO_AB.json` retains every verification event. A planted signed-zero mismatch proves that the fresh value wins and every other memo policy becomes disabled.

`TESTS.txt` records commands and exit codes. It retains the initial fixture setup failure and its successful checks; it also records the legacy missing-fixture non-passes.

| Gate | Result |
|---|---|
| Package tests | 14 pass. |
| W2 constraints | 9 pass; retained production-reference checks plus the new-token policy check. |
| B1 runtime / stub tests | 8 / 6 pass. |
| Tower wiring / sequence / pairing / B1 report fixtures | 7 / 5 / 6 / 1 pass. |
| Memo tests | Eight distinct tests pass across the recorded runs: A/B, sensitivity, mutation, eviction, exact mismatch, no IO, process isolation, prefill and wiring coverage. |
| Memo binding and production policy | Four distinct tests pass, including actual `parity.make_real` wiring and stable resume ordinals. |
| Legacy broad suite | 31 pass; 3 failures and 10 errors require absent K1 assets, matching W2. |
| Replay | 600 runs, zero mismatches; eight expected geometry errors match. Candidate rule retains seven not-seen pairs for each geometry variant. |
| No file IO | `open`, `io.open`, `np.load` and `torch.load` raise during both primitive memo operations and the actual G3T/SAM memo boundaries; all checks pass. |
| Empty-root rehearsal | Payload pins, admission, six argument sets, both policies, real preparation settings assignment and environment bindings pass with documented restore/manifest stubs. |
| Static EAT-1 | Strict gate fails: 17 new bookkeeping flags, zero new A4 flags; two additional listed findings are unchanged file literals relocated with the G3T function. |

`DELTA_AUDIT.json` proves AST identity of the fresh G3T body and StageOne's decision methods. Grounding, servers, call hook, scorer, statistics, call caps, tree, heads, parity kit, items and row producers retain their base bytes. `LOCAL_REHEARSAL.json` and `MEMO_BINDING.json` distinguish local fixture evidence from a real restore.

The production assets and GPU runtime are not staged in W3. No live GPU determinism, GPU hit timing, model restore, SAM memory footprint or full-read completion was measured. The delivered CPU operator command performs the real staging check separately; local fixture receipts cannot replace it.

**Time and budget**

`TIME_PRICE.json` derives own seconds/read from W2's three `in/h10own/*/items.jsonl` files. Means are displacement 7.252, rotation 4.749, direction 8.923, distance 25.509 and room 27.333 seconds. For 786 reads, their total is 11,775.302 seconds. The supplied fresh G3T cost is 19.8 seconds.

Segment capture counts are 60 + 60 + 51 + 49 + 48 + 18 = 286. Adding 19 verify-hit recomputations gives 305 fresh G3T calls. A hypothetical shared worker could use 84 + 19 = 103. Both calculations assume identical keys per capture and no eviction. They do not subtract unmeasured SAM encoding savings or claim that own-arm decoding perfectly predicts tower-arm time.

| Scenario | Fresh G3T calls | Read hours | Hours with staging + stop margin | Fits five hours? |
|---|---:|---:|---:|---|
{time_rows}

The allowance is 1,800 seconds for staging and loading plus the 1,800-second stop margin. The 1,200-second return margin lies within the stop margin and is not counted twice. The deployed segment-local plan exceeds the stop deadline by 3,414 seconds under this estimate, so all 786 reads are not expected to fit. The hypothetical shared worker has only 585 seconds of slack and is not implemented. Hashing, copies, eviction, model loading and decode trajectories can change these estimates. Price remains five times the approved H100 hourly rate plus the separate CPU check; no rate was supplied.

**Operator commands**

`OPERATIONS_TOWER.md` supplies placement, gate status and receipt prerequisites. These commands are written for the authorized operator and have not executed in this task. The package remains subject to the existing GO/review requirements and the unmet strict static gate.

'''
# Keep the exact executable blocks in the report as requested.
report+='\n\n'.join('```bash\n'+block+'```' for block in re.findall(r'```bash\n(.*?)```',ops,re.S))
report+='''

**Local reproduction and retained files**

Run `out/build_package.py`, `out/build_operator.py`, then `out/build_delivery.py` with `/scratch/jjyeung/envs/p1cpu/bin/python -B` from W3. The package builder supplies an explicit reader inventory so repeated builds use the current source. `work/run_suites.py`, `work/test_memo.py`, `work/test_memo_binding.py`, `work/audit_memo.py` and `work/estimate.py` retain the checks. Replay uses the read-only W1 fixture directory and writes only to W3.

All task-created artifacts are in W3. No SSH, Git, network access or job submission ran. `REMOVAL_CANDIDATES.md` lists retained fixtures; no deletion command was issued. Baseline comparisons are kept because they define the identity proof; there is no superseded design narrative.
'''
(O/'REPORT.md').write_text(report)
size=lambda root:sum(p.stat().st_size for p in root.rglob('*') if p.is_file() and not p.is_symlink())
candidates=[(p,size(W/p)) for p in ('work/tmp','work/pytest_tmp','work/existing_full','out/tests','out/reader_repin','out/baseline')]
(O/'REMOVAL_CANDIDATES.md').write_text('Retained local fixtures are optional cleanup candidates after review. No files were deleted, and no deletion command is queued or executed. Keep `out/1.tgz`, `out/0.tgz`, the descriptors, source, reports, tests and evidence until review finishes.\n\n| W3-relative path | Bytes |\n|---|---:|\n'+''.join(f'| `{p}` | {n} |\n' for p,n in candidates)+'\nThese directories contain CPU fixture roots, extracted baselines and reproducible staging files. The user controls cleanup.\n')
print(json.dumps(hashes,indent=2))
