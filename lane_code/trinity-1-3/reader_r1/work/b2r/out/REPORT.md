Package `c3cc59fb4aae0` contains one room-only tower read for 134 items. Its payload and delivery are sealed in `0.tgz` and `1.tgz`. The package is **not fully validated for submission**: the local first-dev-S1 full-reader rehearsal needs the pinned dev-S1 frame tar. The R0 full-reader rehearsal passes. No GPU run or remote action occurred.

| Implementation | File and line |
|---|---|
| Room admission | `out/src/h1eval/room134.py:6` |
| Mixed frame binding | `out/src/h1eval/room134.py:33` |
| Manifest dispatch | `out/src/h1eval/items.py:116` |
| Frame-root extraction admission | `out/src/orchard_h10/job.py:42` |
| Durable type binding | `out/src/h1eval/h10/launch.py:192` |
| One read and settings | `out/tower_sequence.py:5` |
| Allocated frame check | `out/tower_sequence.py:77` |
| Scoring and pairing | `out/room_pair.py:15` |

The item manifest contains the exact 36 W5 dev-S1 room rows and 98 room rows from the supplied R0-dev qset. It preserves the questions verbatim, f32 indices, source FPS and frame totals, and records source line, qid, qset SHA256 and `gt.area_m2` label provenance. The ID sets and physical-room sets do not overlap across the two sources. The 36 dev-S1 captures span nine physical rooms; together the read spans 107 physical rooms. R0-dev and the combined manifest are development-only, with fitting forbidden. No fitting ran.

`item_set_sha256` is `381717700a175d54fe9fa8f19194c9b04366feceb99f278a733f611b853fd7ac`. The plan digest is `2b7a81eae786026fb052765e05d292698cd5c05b1288bacb44a1bee013cc8ee4`. `READ_PLAN.json` lists every key and the requested settings. Only `items/room134.json` appears under `items/` in the payload. The null selector slot and room's two-call cap remain unchanged.

The step-544 export descriptor, all artifact file pins, G3T weights/config, reader, heads, native tree, parity kit, official scorer and return implementation match W5 byte for byte. `PAYLOAD_AUDIT.json` records 918 identical members and 838 protected identical members. `PATCH.diff` compares the sealed payload with W5/out/src and the operator files with W5/out. Configuration and item/frame adapters are the only runtime changes outside the operator.

The supplied R0 tar has SHA256 `2ad8c67c111d5f286aa96ea688efd5c88218e116a8c09ae1a9b4bc71be893a21` and 797,685,760 bytes. Its actual members use opaque 24-hex room/frame names, rather than the source layout `frames/scannetpp/<scene>/<frame>.png`. The producer's `evidence/ID_MAP.json` maps qset line and qid to `assets/e52a690b.jsonl`; `kit/launcher/EXTRA.json` supplies each member's digest. `FRAME_CHECK.json` proves all 3,136 requested PNGs exist, match those digests, and are 640×480. `R0_FRAME_PROVENANCE.json` pins the mapping sources; the identifier key was neither read nor copied. The source scene-manifest digests are retained as provenance; they are not incorrectly claimed to be members of this opaque tar.

Staging extracts the R0 archive directly under the existing frame root, adding 795,282,085 expanded bytes. All 3,136 tar members are needed by this room read. W5’s other archives and template groups remain: the restore contract requires all pinned dependencies, and the existing stage function extracts whole authenticated archives. The unchanged reader can construct SAM/selector components even for a direct room read. No unverified archive was dropped or rewritten. The 798 MB tar stays outside W6 and is read in place.

Room evaluation requires no external per-frame intrinsics or pose files. `src/b/e2e_reader/parity.py:35` builds the trainer input from RGB paths/digests, indices, timestamps, FPS, frame total and question. `src/tree/evalpath/runtime.py:126` uses the VQA prompt path; `src/tree/student_pilot/carrier_c1_data.py:416` builds camera targets only for the pose-training stream. Its frame loader reads PNGs. `src/b/e2e_reader/generate.py:30` constructs geometry lazily from in-memory predicted tensors if a call requests it. The direct R0 rehearsal forbids G3T invocation and reaches EOS without any camera-data input. Unexpected generated camera/ground calls could still invoke a tower; the zero-call timing estimate is an assumption from W5's room rows, not a hard reader restriction. The fixed memo memory bound admits up to 134 captures, below 200 GiB.

The timing proxy uses W5's measured room mean, 27.3328118579 seconds/item. Reads need 3662.597 seconds. Staging/loading retains W5's 1,800-second allowance and adds 120 seconds for the new archive. The overlapping stop/return margins require 7382.597 seconds in total. Of 02:00:00, 02:30:00 and 03:00:00, **02:30:00** is the smallest fitting walltime. It leaves 1617.403 seconds before stop admission under the proxy. Production throughput, RSS and staging time remain unmeasured. Price is 2.5 times the H100 hourly rate plus the CPU check; rates were not supplied.

The 134 replay rows imply 2,492,400 raw bytes and 428,800 compressed bytes. The archive estimate adds a 10 MB metadata/log allowance, totaling **10,428,800 bytes**. This leaves 79,471,200 bytes against the conservative 89.9 MB archive allowance and 89,571,200 bytes against an empty 100 MB pool. The production limiter actually caps compressed archives at 89,999,999 bytes. The shared pool's occupancy remains an operator check.

| Gate | Latest result | Tests | Log |
|---|---|---:|---|
| `out/tests/test_package.py` | PASS | 13 | `test_package_1794953559195631798.log` |
| `work/test_sequence.py` | PASS | 5 | `test_sequence_1794953563454883913.log` |
| `work/test_full_room.py` | FAIL | 2 | `test_full_room.log` |
| `out/tests/test_constraints.py` | PASS | 9 | `test_constraints_1794953560797956328.log` |
| `work/test_room_contract.py` | PASS | 5 | `test_room_contract.log` |
| `work/test_room_pair.py` | PASS | 2 | `test_room_pair_1794953580779024498.log` |
| `work/test_memo.py` | PASS | 8 | `test_memo.log` |
| `work/test_memo_binding.py` | PASS | 4 | `test_memo_binding.log` |
| `work/test_module_selection.py` | PASS | 3 | `test_module_selection.log` |
| `work/test_operator_memory.py` | PASS | 2 | `test_operator_memory_1794953565890218252.log` |
| `work/test_fixes.py` | PASS | 5 | `test_fixes_1794953574285523799.log` |
| `work/test_return_cli.py` | PASS | 1 | `test_return_cli_1794953574528280121.log` |
| `work/test_b1.py` | PASS | 8 | `test_b1.log` |
| `work/test_select_stubs.py` | PASS | 6 | `test_select_stubs_1794953563572453562.log` |
| `work/test_tower.py` | PASS | 7 | `test_tower.log` |

Latest tests: **79 passed, 1 failed**. `TESTS.txt` retains the command ledger, including failed setup assertions and their follow-up checks. `FRAME_CHECK.json` also records the full archive/member verification performed by `work/build_items.py`.

`FULL_R0.json` contains the finished R0 record from real launch, mixed native mapping, frame SHA256 checks and PIL decoding, capped ParityGenerator, generate_real, CallHook, decode loop and official scoring. Artifact audit, weights/model forward, tokenizer and prompt tensor construction are explicit CPU stubs. The first dev-S1 attempt stops at a missing pinned PNG before generation; no substitute image or hash bypass was used. `MEMO_BINDING.json` exercises real empty-root prepare and launch with restore, manifest creation and runtime-version stubs. `LOCAL_REHEARSAL.json` covers extraction, every payload pin, step-544 admission, one read and null-slot wiring. `RETURN_MEMBERS.json`, `STOP_PROOF.json` and `RETURN_CLI.json` cover journal return, draining, partial persistence and authenticated unpack. `SCORING_TEST.json` proves the synthetic 36/98/134 pairing, MRA, cap/malformed counts and refusal checks.

`room_pair.py` recomputes MRA from ground_truth using the unchanged official scorer and the parity think-close/strict-no-answer rule; it does not trust serialized native-answer scores. Malformed-call counts describe recorded diagnostics containing “malformed”; an unserved call without a diagnostic is not classified as malformed. Scores from missing items remain absent and each set reports completion separately.

All writes stayed in W6. CPU tests used the supplied Python with one thread per numerical library; no agent, SSH, Git, network, submission, process kill or deletion ran. Rebuild with `out/build_package.py`, `out/build_operator.py`, and `out/build_delivery.py`. `REMOVAL_CANDIDATES.md` records optional cleanup for the user. The report uses the no-archaeology and summary skills; the requested W5 comparison is retained because it establishes code identity.

| Artifact | Bytes | SHA256 |
|---|---:|---|
| `0.tgz` | 5036924 | `3ba30302eeeeca9f4257c16ecf2d94120e95a09f610b00f1602066933f6a052b` |
| `1.tgz` | 5040714 | `ce8b68febd1e8763fa0f8172a01b09ae82d195ae15f41f0ea575d76b326403b4` |
| `PACKAGE.json` | 626 | `f04c0547b1c750617b9e853b7d312314ed3d833fa2ec956278a682d3a1cc3fb1` |
| `READ_PLAN.json` | 5256 | `1757b7a7608d642371a479b1a0f7a274358ef4bcb113e76982e44eaf3e1871b6` |
| `inputs_tower.json` | 6405 | `206f81ec51f0ce38113b14289f9cf9896baded0e8a950e88ac6653764b24ac04` |
| `export_544.json` | 1498 | `798111bc92c146f64a1c031827a38381be022ae44304f864cc51f880d2fc754b` |
| `tower_sequence.py` | 8078 | `3eca3b0f13254ea006e004355f93bcec3022f13a82c627211e5e0ab3fd4a3fee` |
| `tower_bootstrap.py` | 1900 | `7914533e6d97263ad0bf1dd717f49c16d0bd19ccfa7941f31cefcd4d6ff1e8bd` |
| `node_check.py` | 5041 | `003cffb982ff5aca0fe29450c7917f3133b9553eed2950547ad4ce2ed3168f0a` |
| `room_pair.py` | 6011 | `0e8e5921a5fa7091015e93f7ded290e22de1e0d2b6b1c516bb9b2c8bd41a4d4b` |
| `unpack_return.py` | 2963 | `7bb3e2972e387d7f659a171626597ba4b9f07eaacfab50987a9372bd03bddb64` |
| `src/items/room134.json` | 486709 | `607ba5798f06b77e713069bc57a9ed3b0e80db78ef81faa945487fadddc5e9c7` |
| `src/inputs/room_captures.json` | 828159 | `f84f9b25df9de0f4dc73861b38ecb3bec0fd1adc5a412893f2f795f09cd985fd` |

Package `c3cc59fb4aae0` runs one development-only, 134-item room read at SFT step 544. The read uses tower, mode none, null_argmax, memo on for G3T only, no verification IDs, and no own-depth output. R0-dev must never supply fitting data.

The local dev-S1 full-reader rehearsal requires its pinned frame tar. `REPORT.md` records that gate's current status. Resolve that gate before submission. The real allocated CPU check and GPU run have not run in this lane.

Place the delivery from an existing opaque delivery directory. Set `D` to that directory. These are operator commands; this lane ran none of them.

```bash
set -euo pipefail
umask 077
: "${D:?Set D to the existing opaque delivery directory}"
P=/project/community/jjyeung/c3cc59fb4aae0
printf '%s  %s\n' ce8b68febd1e8763fa0f8172a01b09ae82d195ae15f41f0ea575d76b326403b4 "$D/1.tgz" | sha256sum -c -
mkdir -m 700 "$P"
tar -xzf "$D/1.tgz" -C "$P"
chmod 700 "$P/a"
cd "$P"
CUDA_VISIBLE_DEVICES= /usr/bin/python3 -I -s -B 3.py check --gpus 1 --time 02:30:00
```

Coordinate staging IO before this allocated CPU check. It requests eight CPUs and no GPU. The helper creates a fresh private root, authenticates archives, restores the export, checks one read's settings, verifies and decodes the first item’s frames from each set, and writes the CPU and memory receipts. Model decoding remains a separate GPU operation. The CPU allocation limit permits staging; it is not a timing estimate.

```bash
env -i PATH=/usr/local/bin:/usr/bin:/bin HOME="$HOME" USER="$USER" CUDA_VISIBLE_DEVICES= \
  srun --account=mt01 --partition=general --nodes=1 --ntasks=1 \
  --job-name=a15_cot_apc3cc59fb4aae0 --cpus-per-task=8 --mem=200G \
  --time=02:30:00 --export=ALL \
  /usr/bin/python3 -I -s -B "$P/a/5.py" --package "$P" \
  --sequence "$P/a/6.py" --results "$P/a/c"
```

Submit only after the passing receipt exists. Record the shared return pool's current usage in the operator ledger; the production write test checks capacity before staging. Check the H100 resource type and pending priority jobs, then submit one GPU for 02:30:00.

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
JOB_REPLY=$(/usr/bin/python3 -I -s -B 3.py submit --gpus 1 --time 02:30:00)
JOB=${JOB_REPLY%%;*}
[[ "$JOB" =~ ^[0-9]+$ ]]
printf '%s\n' "$JOB" > "$P/a/8.txt"
```

Fetch after publication. The original pool and GCS transport remain pinned to W5.

```bash
JOB=$(<"$P/a/8.txt")
RET=$(/usr/bin/python3 -I -s -B - "$JOB" <<'PYCODE'
import sys
print('c3cc59fb4aae0'+format(int(sys.argv[1]),'08x'))
PYCODE
)
/usr/bin/python3 -I -s -B 3.py fetch --return-token "$RET" --out "$P/a/f"
```

Transfer only `a/f/0.tgz` and `a/f/EXIT.json` through the authorized operator channel into W6's `work/f/`. No transfer ran here. On Trinity, unpack and score:

```bash
cd /scratch/jjyeung/orch_n30/reader_r1/work/b2r
/scratch/jjyeung/envs/p1cpu/bin/python -B out/unpack_return.py \
  --archive work/f/0.tgz --exit work/f/EXIT.json --out work/ret
/scratch/jjyeung/envs/p1cpu/bin/python -B out/room_pair.py \
  --return-root work/ret --out out/scores
```

The scorer reports per-item MRA, dev-S1 (36), R0-dev (98), and all (134), plus capped reads and recorded malformed-call diagnostics. It recomputes MRA against each item's ground_truth with the unchanged official scorer. It pairs by exact ID and physical-room key, rejects changed bindings and duplicates, and lists missing items without inventing scores. A partial return remains explicitly incomplete. `--allow-fixture` is reserved for the synthetic test.

The stop margin is 1,800 seconds; the return margin is 1,200 seconds within it. The read estimate is 3662.6 seconds, staging/loading is 1,920 seconds, and the minimum total is 7382.6 seconds. Two hours fails; 02:30:00 leaves 1617.4 seconds of estimated slack. Price is 2.5 H100-hours plus the CPU check; no hourly rate was supplied.

The row estimate is 2,492,400 raw bytes and 428,800 compressed bytes. Adding 10,000,000 bytes for metadata and logs gives a 10,428,800-byte planning estimate, below the 89,900,000-byte archive allowance and 100,000,000-byte shared pool cap. These are estimates, not measured production returns. Shared pool occupancy can still prevent a return.
