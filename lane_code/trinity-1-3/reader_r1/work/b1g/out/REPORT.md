Package **e09e45fda45db** memoizes only G3T and runs the selector comparison first. The local gates and retained evidence are listed below. The expected five-hour cut falls in room; the full 786-item plan does not fit the timing proxy. SAM encode time and production peak RSS remain unmeasured.

| Change | Implementation | Behavior |
|---|---|---|
| Module membership | `out/src/b/e2e_reader/perception_memo.py:34`; `out/src/b/e2e_reader/perception_memo.py:226` | A missing module-list key fails even in off mode. Only listed modules enter the host store; an unlisted module skips hashing, lookup, copy and storage. Explicit-ID verification applies only to listed modules. |
| Production wiring | `out/src/b/e2e_reader/parity.py:226`; `out/src/b/e2e_reader/real.py:82` | The parity factory passes the mandatory list into the real reader. This kit lists g3t; SAM encodes freshly in every read that requests it. |
| Bindings and reuse | `out/src/orchard_h10/prepare.py:61`; `out/src/orchard_h10/runner.py:132`; `out/src/h1eval/h10/launch.py:199`; `out/src/h1eval/h10/parity_adapter.py:215`; `out/tower_pair.py:46` | Prepared settings, environment bindings, worker identity, resume, b04 reuse, and per-read journal pairing include the module list. |
| Read order | `out/tower_sequence.py:8`; `out/tower_sequence.py:14`; `out/tower_sequence.py:89` | Read 1 runs first with verify on its first 30 distance IDs. Read 0 then runs all five types in one worker with memo on. The two processes retain independent rules, identities, journals and margins. |
| Memory admission | `out/tower_sequence.py:106`; `out/tower_sequence.py:122`; `out/tower_bootstrap.py:20`; `out/node_check.py:63` | The operator computes the fixed-shape G3T bound and checks the allocation. Bootstrap and the CPU helper require no measured SAM memory receipt. The reader contains no new numeric memory cap. |

| Execution order | Read | Rule | Types | Memo | Verification IDs |
|---|---|---|---|---|---|
| 1 | 1 | candidates_argmax | 150 distance items | verify, then on by membership | Explicit first 30 distance IDs |
| 2 | 0 | null_argmax | 150 distance, 150 displacement, 150 rotation, 150 movement direction, 36 room | on | Empty list |

Both reads use tower, mode none, `perception_memo_modules=["g3t"]`, and `save_own_depth=false`. The verification list spans 11 captures and causes 19 hit recomputations. A mismatch serves the fresh value and disables memoization throughout that process. SAM results never enter this kit's memo. The worker preserves per-type manifest order and the existing call caps. Room has no served call in leg R1 and is scheduled last. `RETURN_MEMBERS.json` proves distinct process IDs for the two reads and one load per read; every started segment remains in the return.

| Local gate | Result and evidence |
|---|---|
| Package / constraints | 14 / 9 pass. |
| B1 runtime / stubs / tower wiring | 8 / 6 / 7 pass. |
| Sequence / pairing / B1 report | 5 / 7 / 1 pass. Sequence asserts the literal requested order; pairing includes missing and mixed module-list refusal. |
| Memo / bindings / module selection | 8 / 4 / 3 pass. Includes explicit-ID resume, mutation, no IO, process isolation, bit identity, missing key failure, listed hits and unlisted fresh calls. |
| F1/F2/F4 / return CLI | Five tests pass; real subprocess journals return, top STOP drains the active item, deadline results persist, and b04 reuse rejects rule, mode, IDs and modules independently. Authenticated unpack accepts all six journals and rejects a missing one. |
| Multi-type A/B | Twelve reads across five types per mode. One model load per mode; G3T calls are 12/2/4 for off/on/verify, SAM calls are 10/10/10. Outputs and scores match, and room retains its call cap. Frozen modules and model forward are CPU stubs. |
| Empty-root preparation | Real prepare writes `d/settings.json`; real launch writes matching rule, mode, modules and verify IDs for both reads. Restore, manifest building and runtime-version receipts use documented stubs. `MEMO_BINDING.json` and `LOCAL_REHEARSAL.json` hold the receipts. |
| Memory admission | Two tests pass. SAM construction is forbidden during the fixed-bound helper test; bootstrap accepts a fitting fixed-shape receipt without a SAM measurement and rejects missing, nonfitting or mismatched policies. Seven CPU tensor dtypes retain bit-identical payload, shape, dtype and device. CUDA is untested. |
| Pre-memo baseline A/B | The 30-read baseline output hash matches current off/on/verify. |
| Replay | 600 runs, zero mismatches, eight matching expected errors, seven remaining candidate not-seen pairs per geometry. |
| EAT-1 | Zero new generate-path A3/A4 behavior versus a943 and e47. The raw a943 comparison has zero additions. The raw e47 comparison has two additions and two removals caused by the unchanged G3T body moving from __call__ to _fresh; AST equality proves the relocation. Raw scans and the unchanged reviewer scanner outputs remain available. |
| Broad legacy K1 suite | 31 pass; three failures and ten errors require absent K1 assets, matching W4. This is not a passing gate. See `legacy.log` and `TESTS.txt`. |

`TESTS.txt` records commands, exit codes, durations and logs, including setup failures and their passing follow-up checks. `EAT1_GATE.json` preserves the raw e47 delta and the AST relocation proof; no scanner or allowlist changed. Comparisons with the requested bases establish identity and are the only historical references retained under the no-archaeology skill.

The payload changes 9 members and retains 918 identical members versus a943. It changes 15 members and retains 912 identical members versus bf94. `PATCH.diff` and `FILE_SHA256_DIFF.tsv` use a943 as the default base; the explicitly named variants cover both requested bases. The PATCH diffs include operator-kit changes; the FILE_SHA256_DIFF tables cover sealed payload members. Protected decision/print files, frozen tree, heads, parity kit, reader core, items, scorers, statistics and row producers retain their bytes. `DELTA_AUDIT.json` records their hashes and the unchanged fresh-body and call-cap AST checks. Input and export descriptors remain pinned to their reviewed bytes; their internal logical namespace is unchanged.

| Artifact | SHA256 |
|---|---|
| `0.tgz` | `9f891bc1e761c09f264f575ee23db735102997df6addde21765bc6a7703f64f2` |
| `1.tgz` | `eadaba88d737c4b384e3fe6908c0420a35d78c3be6037b8302d154c7109f6fc4` |
| `PACKAGE.json` | `426f0d5653f6ce2bd145f28a7781ccf327238d10b4a5a775c63f269a8b23588b` |
| `tower_sequence.py` | `0cec6e0e91b8c7dab6d74e68bbca8e6a596e5df76e7f0e9166aec2231ecb3f38` |
| `tower_bootstrap.py` | `7914533e6d97263ad0bf1dd717f49c16d0bd19ccfa7941f31cefcd4d6ff1e8bd` |
| `node_check.py` | `8846151e74add7b81013759568294a86dc74203edcde92c2a75f314210462039` |
| `tower_pair.py` | `ea0ae8eb4a54821323a38c9f2701219b58ec4c29f8e84d93456e40f8851ce9ad` |
| `unpack_return.py` | `b8a2a6a498aebce3bff9a3d10d60bb78192368d320b1717a62c2720a15194a87` |
| `READ_PLAN.json` | `b061e3f7ba14fd79b9d4949c519d9b6641e10fae2d16daee2688b91cea8c980c` |
| `inputs_tower.json` | `025b4688121ac3df8d5ecf92798b1abadf6f4a8d055eb3980a606915ceea0207` |
| `export_544.json` | `798111bc92c146f64a1c031827a38381be022ae44304f864cc51f880d2fc754b` |
| `plan_sha256` | `06c7bc0dbeb2c6fd9d50faa27952f7e8ccdf07d4dddd3fedba2fbe2639441308` |
| `BATCH_sha256` | `a533c4fc31a2f843a88127fd614899c6c0da23853a35a6d14da1bc6430bfef13` |

The fixed G3T shapes bound payload at **3,335,080 bytes per capture**. The operator adds 1 MiB per capture for Python/allocator overhead, three transient capture copies, and a 64 GiB runtime allowance. Read 0 retains at most 84 captures and read 1 at most 60; their planning totals are **64.355 GiB** and **64.257 GiB**, below the 200 GiB allocation. Separate worker lifetimes keep these totals separate. SAM memo retention is zero. This bounds retained memo data; the runtime allowance is not a measured full-model peak RSS bound. Fresh SAM activations are transient runtime memory.

The estimate uses measured own-read means as timing proxies and 19.8 seconds per fresh G3T call. Fresh SAM work is present in those own-read measurements, but its encode-only contribution is **unmeasured**. The estimate credits no SAM memo savings and does not double-count an additional SAM time. G3T needs 79 calls for read 1 and 84 for read 0, including verification. Reads total **15,002.702 seconds**; staging/loading and stop margin add 3,600 seconds, yielding **5.167 hours**. The 1,200-second return margin lies inside the 1,800-second stop margin.

| Segment | Estimated incremental seconds | Fresh G3T calls |
|---|---:|---:|
| Read 1: object_abs_distance | 5390.579 | 79 |
| Read 0: object_abs_distance | 5014.379 | 60 |
| Read 0: camera_displacement | 1543.232 | 23 |
| Read 0: camera_rotation | 732.112 | 1 |
| Read 0: camera_movement_direction | 1338.419 | 0 |
| Read 0: room_size_estimation | 983.981 | 0 |

With 1,800 seconds for staging/loading, the stop deadline leaves 14,400 seconds for reads. Both distance reads and all camera types consume 14,018.721 seconds, leaving **381.279 seconds for room**. Thirteen room items finish before the proxy stop time; the fourteenth, `room_scene0515_01`, starts before it and may drain within the return margin. The expected return therefore contains about **764 of 786 items**, including every distance and camera item. Unmeasured overhead above the pre-room slack could move the cut earlier; ordering protects the selector comparison by running it first. Price is five times the approved H100 hourly rate plus the CPU check; no rate was supplied.

All work stayed in W5 and used the supplied CPU Python. No SSH, Git, network, submission, process kill or deletion ran. The real allocated CPU check and GPU reads remain operator actions. Rebuild with `out/build_package.py`, `out/build_operator.py`, then `out/build_delivery.py`; refresh audits with `work/audit_payload.py` and this report with `work/write_delivery_report.py`. `REMOVAL_CANDIDATES.md` identifies retained fixtures and unused copied scripts for user review.

Place the delivery from an existing opaque directory and check metadata. Set `D` to that directory. These commands have not run in this lane.

```bash
set -euo pipefail
umask 077
: "${D:?Set D to the existing opaque delivery directory}"
P=/project/community/jjyeung/e09e45fda45db
printf '%s  %s\n' eadaba88d737c4b384e3fe6908c0420a35d78c3be6037b8302d154c7109f6fc4 "$D/1.tgz" | sha256sum -c -
mkdir -m 700 "$P"
tar -xzf "$D/1.tgz" -C "$P"
chmod 700 "$P/a"
cd "$P"
CUDA_VISIBLE_DEVICES= /usr/bin/python3 -I -s -B 3.py check --gpus 1 --time 05:00:00
```

Coordinate staging IO before the allocated empty-root CPU check. This requests eight CPUs and no GPU. The helper restores authenticated inputs, checks default and per-read settings, rehearses selector wiring, and writes `a/c/CPU.json` and `a/c/MEMORY.json`. It checks the fixed G3T memo bound against 200 GiB without loading SAM for a memory measurement. The bootstrap requires the passing receipt bound to this payload, input descriptor and operator. A real evaluation-item decode remains outside this check.

```bash
env -i PATH=/usr/local/bin:/usr/bin:/bin HOME="$HOME" USER="$USER" \
  srun --account=mt01 --partition=general --nodes=1 --ntasks=1 \
  --job-name=a15_cot_ape09e45fda45db --cpus-per-task=8 --mem=200G \
  --time=04:00:00 --export=ALL \
  /usr/bin/python3 -I -s -B "$P/a/5.py" --package "$P" \
  --sequence "$P/a/6.py" --results "$P/a/c"
```

After the CPU check passes, use the existing review requirements and accept the documented partial-run estimate before submitting. Record the shared return pool's usage; the production write test checks its capacity before staging. The following commands check resource types and pending priority jobs, then submit one GPU for five hours.

```bash
sinfo -N -h -p general -o '%G' > "$P/a/7.txt"
/usr/bin/python3 -I -s -B - "$P/a/7.txt" <<'PYCODE'
import re,sys
from pathlib import Path
rows=[s.strip() for s in Path(sys.argv[1]).read_text().splitlines() if s.strip()]
gpu=[g for row in rows for g in row.split(',') if g.startswith('gpu:')]
assert rows and gpu
assert all(re.fullmatch(r'gpu:[^:]*[Hh]100[^:]*:[0-9]+(?:\([^)]*\))?',g) for g in gpu)
PYCODE
squeue -u "$USER" -h -o '%j %T' > "$P/a/9.txt"
/usr/bin/python3 -I -s -B - "$P/a/9.txt" <<'PYCODE'
import sys
from pathlib import Path
rows=[s.split() for s in Path(sys.argv[1]).read_text().splitlines()]
assert not any(len(r)>=2 and r[0].startswith('jjy_') and r[1] in ('PENDING','PD') for r in rows)
PYCODE
JOB_REPLY=$(/usr/bin/python3 -I -s -B 3.py submit --gpus 1 --time 05:00:00)
JOB=${JOB_REPLY%%;*}
[[ "$JOB" =~ ^[0-9]+$ ]]
printf '%s\n' "$JOB" > "$P/a/8.txt"
```

Fetch after the return is published. The transport may mark a clean partial return as failed because the full plan did not finish; inspect its summaries.

```bash
JOB=$(<"$P/a/8.txt")
RET=$(/usr/bin/python3 -I -s -B - "$JOB" <<'PYCODE'
import sys
print('e09e45fda45db'+format(int(sys.argv[1]),'08x'))
PYCODE
)
/usr/bin/python3 -I -s -B 3.py fetch --return-token "$RET" --out "$P/a/f"
```

Transfer the bounded `a/f/0.tgz` and `a/f/EXIT.json` through the authorized operator channel into W5's `work/f/`. No transfer ran here. Unpack and score locally:

```bash
cd /scratch/jjyeung/orch_n30/reader_r1/work/b1g
/scratch/jjyeung/envs/p1cpu/bin/python -B out/unpack_return.py \
  --archive work/f/0.tgz --exit work/f/EXIT.json --out work/ret
/scratch/jjyeung/envs/p1cpu/bin/python -B out/tower_pair.py \
  --package out/src \
  --own ../b1p/in/h10own/170631/items.jsonl ../b1p/in/h10own/170706/items.jsonl ../b1p/in/h10own/170694/items.jsonl \
  --tower-null work/ret/metadata/reads/0 \
  --tower-candidates work/ret/metadata/reads/1 \
  --out out/tower_results
```

Unpacking rejects a missing journal or environment for a started segment. Pairing rejects missing journals, mixed rules, mismatched module bindings and changed code hashes. Partial camera journals cannot establish the complete camera comparison. Candidate-rule comparisons remain in-sample. No cross-rule journal merge is permitted.
