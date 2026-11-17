Package **a9439d0fb0487** implements F1, F2, F4, explicit-ID memo verification, and one worker per read. The required local suites, 600-run replay, return tests, and generate-path EAT-1 comparison pass. **This is not a production-ready release:** the full 786-read estimate is 5.167 hours with margins, and the real SAM footprint remains unmeasured because its pinned source and weights are absent from the authorized local inputs.

| Fix | Implementation | Evidence |
|---|---|---|
| F1: return every started segment | `out/tower_sequence.py:37` puts reads below returned metadata. `out/src/orchard_h10/runner.py:82` keeps caches at `r/cache/<read>`, outside returned members. `out/unpack_return.py:5` refuses missing journals/environments; `out/tower_pair.py:34` refuses empty reads. | `fixes_final.log`, `RETURN_MEMBERS.json`, `RETURN_CLI.json`: real subprocesses produce six journals; real `chain_save.members()` returns every journal, environment, progress, SUMMARY, STEPS and log, with no cache. The authenticated unpack CLI accepts all six and rejects an archive missing one. |
| F2: share top STOP | `out/tower_sequence.py:43`, `out/src/orchard_h10/runner.py:56`, `out/src/orchard_h10/runner.py:139` pass the same `r/metadata/STOP` to runner and worker. | `STOP_PROOF.json`: a parent thread writes top STOP while the real worker subprocess is inside an item; the worker drains cleanly and returns one durable record. The deadline test also retains a partial summary and progress. |
| F4: bind b04 reuse | `out/src/h1eval/h10/parity_adapter.py:215` compares explicit rule, memo mode and verify IDs in `LOAD_RECEIPT.json`. Missing keys refuse reuse. | `test_b04_reuse_rejects_rule_and_memo_from_launcher` in `fixes_final.log` exercises `launch.run --tower-from` and independently rejects all three mismatches with a structurally authenticated b04 receipt. |
| M1: remove reader bookkeeping thresholds | `out/src/b/e2e_reader/perception_memo.py:22`, `out/src/b/e2e_reader/perception_memo.py:75`, `out/src/b/e2e_reader/perception_memo.py:207` use explicit ID membership and an unbounded process-local host store. `out/src/b/e2e_reader/parity.py:245` supplies the item ID. | `memo.log`, `MEMO_BINDING.json`, `MEMORY_BOUND.json`: missing production setting keys fail; ID membership survives out-of-order resume; mutation, no-IO, key sensitivity, process isolation and signed-zero mismatch tests pass. CPU tensor hits retain dtype, shape, device and exact bytes across seven dtypes. CUDA was not available. |
| M2: retain one generator across types | `out/src/orchard_h10/runner.py:62`, `out/src/h1eval/h10/launch.py:329`, `out/src/h1eval/h10/launch.py:282` route one worker into ordered per-type journals. | `RETURN_MEMBERS.json` proves one subprocess per read and distinct PIDs between reads. `MULTITYPE_AB.json` proves one model load across all five types, response/score parity, cross-type memo hits and the room call cap through the real capped parity reader. |

`in/refute_members.py` and `in/eat.py` are retained unchanged. `work/refute_members.py` adapts only the reproducer's workspace, returned layout and six-type list; it prints all six journals. `work/reviewer_eat.py` preserves the reviewer's scan logic and changes only old/new roots. `reviewer_checks.log` records both runs. The original reproducer hard-codes the obsolete unreturned layout, so it cannot exercise the new layout unchanged.

The four protected source files remain byte-identical to c91: `stage1.py`, `grounding.py`, `servers.py`, and `perception_own.py`. This preserves W3's memo wiring and the reviewed decision/print logic. The fresh G3T body and call-cap factory retain identical ASTs. The tree, heads, parity kit, reader core, items, scorers, statistics and row producers retain their bytes. `DELTA_AUDIT.json` records full protected hashes. The payload has 919 identical members and eight changed members versus c91; it has 913 identical members and 14 changed or added members versus bf94. Both `FILE_SHA256_DIFF_vs_*.tsv` files include identical members as well as changes. Both `PATCH_vs_*.diff` files include payload and operator-kit changes; `PATCH.diff` is the bf94 comparison.

| Artifact | SHA256 |
|---|---|
| `0.tgz` | `98a9add60daf1c0b63dd53934447fb48e952760e5cf97b253ce9821b33f3251e` |
| `1.tgz` | `50c7ae132db7ba3960a7c123420a7eadf6aaf9a85e416d5964bdf2e5cc1ffa79` |
| `PACKAGE.json` | `208523054d8cb6ff683c0823e4044b3e9d3c4989142c2807b7c8cf4318893ecb` |
| `tower_sequence.py` | `a21c21426d3abeda3b9edb0a4184025677d605805f5467f090ce13d09a68668b` |
| `tower_bootstrap.py` | `ff36f38358d11d715a07be31304948b4aba29abc48c76e504f3f4c7c1a66a679` |
| `node_check.py` | `59de1f8810d81e0fd46c7be278e20eeb9e46c47bc8e1dd96056cc78df6df3ab5` |
| `READ_PLAN.json` | `258987eec1a6de265a1d2dc42d8e1404b509ebd942ab409ecb66abdf658012a7` |
| `inputs_tower.json` | `025b4688121ac3df8d5ecf92798b1abadf6f4a8d055eb3980a606915ceea0207` |
| `export_544.json` | `798111bc92c146f64a1c031827a38381be022ae44304f864cc51f880d2fc754b` |
| `plan_sha256` | `f7d33194d6ea74108c935c20b4f252d5086333436d0bd2b4e1ec23f5d5b1cb49` |
| `BATCH_sha256` | `76d4d7ed5c177471890e7688da270cdda425e56c5cd8e8ce531d95a53a4807f9` |

The read schedule is `(0,3),(0,0),(0,1),(0,2),(0,4),(1,3)`. Types 3, 0, 1, 2 and 4 mean distance, displacement, rotation, movement direction and room, respectively. Each type preserves manifest order. Read 0 verifies the explicit first 30 distance IDs and then uses hits without recomputation; read 1 uses memo `on`. Reads use separate processes, rules, settings, identities and journals. A verification mismatch serves the fresh value and disables all memo instances in that process. The settings bind `perception_memo_verify_ids`; production launch refuses a missing mode, ID list or selector rule.

| Local gate | Result |
|---|---|
| Package / constraints | 14 / 9 pass. |
| B1 runtime / stubs / tower wiring | 8 / 6 / 7 pass. |
| Sequence / pairing / B1 report | 5 / 6 / 1 pass. |
| Memo / bindings | 8 / 4 pass; includes A/B, sensitivity, defensive copies, no eviction, no IO, mismatch disable, process isolation, prefill sensitivity and explicit-ID resume. |
| F1/F2/F4/deadline | Five tests pass, plus authenticated unpack CLI tests and the adapted reviewer return reproducer. |
| Multi-type A/B | Twelve reads across all five types per mode. Off/on/verify outputs share one hash; model loads are 1/1/1, G3T calls are 12/2/4 and SAM encodes are 10/2/4. Room reads stop at the unchanged two-call cap. Frozen modules and model forward use CPU stubs. |
| Memory helper / bootstrap | Two CPU tests pass: the probe measures a stub encoding and the bootstrap rejects missing or nonfitting measured receipts. The real production encoding remains unmeasured. |
| Empty-root preparation | Real `prepare.run` writes `d/settings.json`; real launch writes matching environment bindings for both read policies. Restore, manifest construction and version receipt use documented stubs. `LOCAL_REHEARSAL.json` validates payload pins and the two worker argument sets. |
| Pre-memo baseline A/B | The 30-read pre-memo fixture matches the current off/on/verify output hash. |
| Replay | 600 runs, zero mismatches, eight matching expected errors; candidates retain seven not-seen pairs per geometry (six SAM-empty and one raster case). |
| EAT-1 | Zero new A3/A4 findings in generate-path files versus c91. The expanded reader scan falls from 45 to 39. The bf94/e47 count is also 39; two existing file literals move from `TowerG3T.__call__` to `_fresh`, with unchanged fresh-body AST. |
| Broad legacy K1 suite | 31 pass; three failures and ten errors require absent K1 assets, matching W3's limitation. This is not a passing gate. |

`TESTS.txt` records commands, exit codes and logs, including failed setup attempts and their passing final checks. The W3 scan method retains all changed-file findings: 140 before, 133 after, 8 operator additions and 15 removals. The additions are journal paths and the segment deadline in `launch.run_types`, outside `generate()`. No allowlist or scanner changed, and no finding was hidden. `EAT1_GATE.json`, the raw scans and `REVIEWER_EAT.json` explain the scope and relocation.

The host-memory plan measures tensor payload directly; it does not infer safety from a byte cap. G3T's fixed shapes bound retained scalar payload at 3,335,080 bytes per capture using eight bytes per scalar. For measured one-frame SAM payload B, a capture retains at most `32*B + G3T + 1 MiB` in this plan. Read 0 retains 84 captures; read 1 retains 60. The plan adds three transient capture copies and a 64 GiB runtime allowance, then compares against the 200 GiB allocation. The runtime allowance is not a measured full-model RSS bound.

`MEMORY_BOUND.json` deliberately reports `production_measurement_available=false`. Its shape sensitivity allocates CPU feature tensors and measures their exact payload: one 256-channel 72×72 level in each of two FP32 pyramids fits; three 288/144/72 levels do not. These are scenarios, not measurements of the pinned SAM model. `out/tower_sequence.py:123` makes the allocated CPU helper encode an authenticated frame using real SAM weights at FP32, writes the measured bound, and refuses an oversized result. The bootstrap requires this measured receipt. CPU copies are bit-identical; a CUDA-device proof and real production memory measurement remain outstanding. The advisory real-item CPU decode gate also remains unrun.

For reference, the measured shape scenarios give these read-0 planning totals. Neither row identifies the pinned model's actual feature shapes.

| CPU FP32 feature scenario | SAM bytes per frame | Retained memo, GiB | Memo + transient copies + runtime allowance, GiB | Fits 200 GiB? |
|---|---:|---:|---:|---|
| one_level_fp32 | 10,616,858 | 26.921 | 91.883 | True |
| three_levels_fp32 | 222,953,498 | 558.484 | 642.429 | False |


The time estimate uses W2's measured own-read means and the supplied 19.8-second fresh G3T cost. Own-read time totals 11,775.302 seconds. Read 0 needs 84 fresh captures plus 19 verification-hit recomputations; read 1 needs 60 fresh captures. Thus 163 G3T calls add 3,227.4 seconds, giving 15,002.702 seconds (4.167 hours) of reads. Adding 1,800 seconds for staging/loading and the 1,800-second stop margin gives **5.167 hours**, 602.702 seconds above the cap. The 1,200-second return margin lies inside the stop margin. Even staging plus only the return margin gives 5.00075 hours. SAM savings and GPU decode/copy overheads are unmeasured. All 786 reads therefore do not fit under this estimate. The job still stops at the fixed deadline and returns partial journals. Price is five times the approved H100 hourly rate, plus the separate CPU check; no rate was supplied.

The following operator commands are exact and have not run. `OPERATIONS_TOWER.md` contains the same commands and prerequisites.

```bash
set -euo pipefail
umask 077
: "${D:?Set D to the existing opaque delivery directory}"
P=/project/community/jjyeung/a9439d0fb0487
printf '%s  %s\n' 50c7ae132db7ba3960a7c123420a7eadf6aaf9a85e416d5964bdf2e5cc1ffa79 "$D/1.tgz" | sha256sum -c -
mkdir -m 700 "$P"
tar -xzf "$D/1.tgz" -C "$P"
chmod 700 "$P/a"
cd "$P"
CUDA_VISIBLE_DEVICES= /usr/bin/python3 -I -s -B 3.py check --gpus 1 --time 05:00:00
```

Run the allocated empty-root CPU check once, after coordinating its staging IO. This command requests no GPU. It authenticates and restores the inputs, checks both read settings, rehearses selector wiring, and measures one real SAM encoding in CPU float32. It writes `a/c/CPU.json` and `a/c/MEMORY.json`; the bootstrap requires a measured, fitting memory receipt bound to this payload and operator. It does not decode a real evaluation item.

```bash
env -i PATH=/usr/local/bin:/usr/bin:/bin HOME="$HOME" USER="$USER" \
  srun --account=mt01 --partition=general --nodes=1 --ntasks=1 \
  --job-name=a15_cot_apa9439d0fb0487 --cpus-per-task=8 --mem=200G \
  --time=04:00:00 --export=ALL \
  /usr/bin/python3 -I -s -B "$P/a/5.py" --package "$P" \
  --sequence "$P/a/6.py" --results "$P/a/c"
```

The submission command below remains conditional on the memory check, existing review requirements, and acceptance of a partial result under the five-hour cap. The current estimate does not support completing all 786 reads. Record the shared return pool's usage before submitting; the production write test also checks capacity before staging. Check the current `general` resource types and pending priority jobs:

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

Fetch after the return is published. The transport can label a clean partial result as failed because it lacks full-plan completion. Its summaries distinguish that case from a worker failure.

```bash
JOB=$(<"$P/a/8.txt")
RET=$(/usr/bin/python3 -I -s -B - "$JOB" <<'PYCODE'
import sys
print('a9439d0fb0487'+format(int(sys.argv[1]),'08x'))
PYCODE
)
/usr/bin/python3 -I -s -B 3.py fetch --return-token "$RET" --out "$P/a/f"
```

Transfer the bounded `a/f/0.tgz` and `a/f/EXIT.json` through the authorized operator channel into W4's `work/f/`. No transfer ran here. Then unpack and score locally:

```bash
cd /scratch/jjyeung/orch_n30/reader_r1/work/b1f
/scratch/jjyeung/envs/p1cpu/bin/python -B out/unpack_return.py \
  --archive work/f/0.tgz --exit work/f/EXIT.json --out work/ret
/scratch/jjyeung/envs/p1cpu/bin/python -B out/tower_pair.py \
  --package out/src \
  --own ../b1p/in/h10own/170631/items.jsonl ../b1p/in/h10own/170706/items.jsonl ../b1p/in/h10own/170694/items.jsonl \
  --tower-null work/ret/metadata/reads/0 \
  --tower-candidates work/ret/metadata/reads/1 \
  --out out/tower_results
```

A started segment without a journal makes unpacking fail. A journal-less read makes pairing fail. Valid partial journals remain partial; missing items cannot establish the camera comparison bar. Candidate-rule differences are in-sample.

Rebuild from W4 with `out/build_package.py`, `out/build_operator.py`, and `out/build_delivery.py`, using `/scratch/jjyeung/envs/p1cpu/bin/python -B`. Run `work/audit_payload.py` and `work/write_delivery_report.py` to refresh comparisons and report hashes. All task-created files stay in W4; its retained size is below 3 GB. No deletion command ran. `REMOVAL_CANDIDATES.md` lists fixtures and unused copied scripts for user review. The no-archaeology skill governs this report; comparisons with the requested bases remain because they establish identity, not revision history.
