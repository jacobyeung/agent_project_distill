Package **c91bb8ec884e9** adds an in-memory perception memo to e47d0593fefec. The default is `off`. CPU tests prove identical responses, answers and scores for `off`, `on` and `verify` on the supplied deterministic fixture; `off` also matches the base payload. The 600-run replay has zero mismatches.

**The package is a review deliverable, not an all-gates-passed release.** The strict EAT-1 zero-new-findings gate is not met: its raw comparison adds 17 A3 bookkeeping findings and no A4 findings. Manual review finds no new rule that changes a response value. The raw findings and explanations remain in `EAT1_before.json`, `EAT1_after.json`, `EAT1_DELTA.json`, and `EAT1_GATE.json`; no allowlist was changed. No job was submitted.

**Artifacts and identity**

The sole new token is `c91bb8ec884e9`. The delivery is `1.tgz`; its payload is `0.tgz`. The payload changes nine memo or wiring files plus `9.json`; the other 917 members remain byte-identical to W2. `PATCH.diff` and `FILE_SHA256_DIFF.tsv` compare directly against W2's e47d0593fefec `0.tgz`.

| Artifact | SHA256 |
|---|---|
| base_payload_sha256 | `9bd9e343bc9f887a16284385057833d682f2eb0df7db85eda12553796540893e` |
| payload_sha256 | `e9794b2caed38f18603e7451ec15519b82ee3f8e748f113d47826df4898f9787` |
| plan_sha256 | `20d33802299d774d0d7e2ddc0773e255590e446227c7524358e52a7f43a2a2aa` |
| package_sha256 | `55ec007d513607a1dc2c1afad1486b2c1560d0821b44fec23aa82901e7abce36` |
| delivery_sha256 | `5aa955de84d7f2c35831c6d31b24bc4c5bc864751f2d7bea9ca983c39debfa25` |
| operator_sha256 | `658766fd86e928b998ccf81e787ea841de9efda2dbe8f9fd57e1d2cfcf6a8daa` |
| batch_sha256 | `6b08e24062a5d89622bc72e58bce3005d1c2b2e7b8f04e08f66716c46571fd9d` |
| read_plan_sha256 | `0416a0e2bc16e3684f8d72761080358f74f4ed69c4a1a72b15acd1db9c04abb1` |
| node_check_sha256 | `c6d579e1054bb00393255ce62b2043993b0be3ba7c703971889710c04d462c5e` |
| export_pin_sha256 | `798111bc92c146f64a1c031827a38381be022ae44304f864cc51f880d2fc754b` |
| inputs_sha256 | `025b4688121ac3df8d5ecf92798b1abadf6f4a8d055eb3980a606915ceea0207` |

The production builder retains its tar format, pinned inventory, admission, restore, five-hour limit and transport. The wrapper and CPU helper are authenticated in `PACKAGE.json`. The delivery includes the unchanged W2 input declarations and export pins. The fixed private logical namespace remains unchanged because the existing policy receipt binds it. Orchard job names use `a15_cot_apc91bb8ec884e9`.

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
| off | 3.8436 | 30 | 30 |
| on | 3.6013 | 5 | 5 |
| verify | 3.5072 | 30 | 30 |

W2's `off` fixture took 3.8120 seconds/read. All four response/answer/score serializations share SHA256 `dad282ee2bbfda788d183f52ddcfb7ee6b7fde615cda60140db7f45da060e02e`. `verify` recorded 50 matching hits, 25 per module. `MEMO_AB.json` retains every verification event. A planted signed-zero mismatch proves that the fresh value wins and every other memo policy becomes disabled.

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
| off | 786 | 7.594 | 8.594 | No |
| segment_local | 305 | 4.948 | 5.948 | No |
| one_process_hypothetical | 103 | 3.837 | 4.837 | Yes, conditionally |

The allowance is 1,800 seconds for staging and loading plus the 1,800-second stop margin. The 1,200-second return margin lies within the stop margin and is not counted twice. The deployed segment-local plan exceeds the stop deadline by 3,414 seconds under this estimate, so all 786 reads are not expected to fit. The hypothetical shared worker has only 585 seconds of slack and is not implemented. Hashing, copies, eviction, model loading and decode trajectories can change these estimates. Price remains five times the approved H100 hourly rate plus the separate CPU check; no rate was supplied.

**Operator commands**

`OPERATIONS_TOWER.md` supplies placement, gate status and receipt prerequisites. These commands are written for the authorized operator and have not executed in this task. The package remains subject to the existing GO/review requirements and the unmet strict static gate.

```bash
set -euo pipefail
umask 077
: "${D:?Set D to the opaque delivery directory}"
P=/project/community/jjyeung/c91bb8ec884e9
printf '%s  %s\n' 5aa955de84d7f2c35831c6d31b24bc4c5bc864751f2d7bea9ca983c39debfa25 "$D/1.tgz" | sha256sum -c -
mkdir -m 700 "$P"
tar -xzf "$D/1.tgz" -C "$P"
chmod 700 "$P/a"
cd "$P"
```

```bash
CUDA_VISIBLE_DEVICES= /usr/bin/python3 -I -s -B 3.py check --gpus 1 --time 05:00:00
```

```bash
env -i PATH=/usr/local/bin:/usr/bin:/bin HOME="$HOME" USER="$USER" \
  srun --account=mt01 --partition=general --nodes=1 --ntasks=1 \
  --job-name=a15_cot_apc91bb8ec884e9 \
  --cpus-per-task=16 --mem=200G --time=04:00:00 --export=ALL \
  /usr/bin/python3 -I -s -B "$P/a/5.py" --package "$P" \
  --sequence "$P/a/6.py" --results "$P/a/c"
```

```bash
sinfo -N -h -p general -o '%G' > "$P/a/7.txt"
/usr/bin/python3 -I -s -B - "$P/a/7.txt" <<'PY'
import re,sys
from pathlib import Path
rows=[s.strip() for s in Path(sys.argv[1]).read_text().splitlines() if s.strip()]
gpu=[g for row in rows for g in row.split(',') if g.startswith('gpu:')]
assert rows and gpu
assert all(re.fullmatch(r'gpu:[^:]*[Hh]100[^:]*:[0-9]+(?:\([^)]*\))?',g) for g in gpu)
PY
squeue -u "$USER" -h -o '%j %T' > "$P/a/9.txt"
/usr/bin/python3 -I -s -B - "$P/a/9.txt" <<'PY'
import sys
from pathlib import Path
rows=[s.split() for s in Path(sys.argv[1]).read_text().splitlines()]
assert not any(len(r)>=2 and r[0].startswith('jjy_') and r[1] in ('PENDING','PD') for r in rows), 'Pending priority job; stop'
PY
JOB_REPLY=$(/usr/bin/python3 -I -s -B 3.py submit --gpus 1 --time 05:00:00)
JOB=${JOB_REPLY%%;*}
[[ "$JOB" =~ ^[0-9]+$ ]]
printf '%s\n' "$JOB" > "$P/a/8.txt"
```

```bash
JOB=$(<"$P/a/8.txt")
RET=$(/usr/bin/python3 -I -s -B - "$JOB" <<'PY'
import sys
print('c91bb8ec884e9'+format(int(sys.argv[1]),'08x'))
PY
)
/usr/bin/python3 -I -s -B 3.py fetch --return-token "$RET" --out "$P/a/f"
```

```bash
cd /scratch/jjyeung/orch_n30/reader_r1/work/b1m
/scratch/jjyeung/envs/p1cpu/bin/python -B out/unpack_return.py \
  --archive work/f/0.tgz --exit work/f/EXIT.json --out work/ret
/scratch/jjyeung/envs/p1cpu/bin/python -B out/tower_pair.py \
  --package out/src \
  --own ../b1p/in/h10own/170631/items.jsonl ../b1p/in/h10own/170706/items.jsonl ../b1p/in/h10own/170694/items.jsonl \
  --tower-null work/ret/0 --tower-candidates work/ret/1 \
  --out out/tower_results
```

**Local reproduction and retained files**

Run `out/build_package.py`, `out/build_operator.py`, then `out/build_delivery.py` with `/scratch/jjyeung/envs/p1cpu/bin/python -B` from W3. The package builder supplies an explicit reader inventory so repeated builds use the current source. `work/run_suites.py`, `work/test_memo.py`, `work/test_memo_binding.py`, `work/audit_memo.py` and `work/estimate.py` retain the checks. Replay uses the read-only W1 fixture directory and writes only to W3.

All task-created artifacts are in W3. No SSH, Git, network access or job submission ran. `REMOVAL_CANDIDATES.md` lists retained fixtures; no deletion command was issued. Baseline comparisons are kept because they define the identity proof; there is no superseded design narrative.
