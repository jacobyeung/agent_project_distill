# Room-call pricing kit: Part A

This kit prices `<ground mode="room">` with the unchanged `room_v314` kernel and frozen DA3 Nested Giant-Large geometry. It trains nothing. Run from `/scratch/jjyeung/orch_n30/sb_roomkit`. All writes, temporary files and caches stay here. The sealed model runtime and local frames are external read-only dependencies; the tar does not duplicate them.

The supplied build is CPU-only. GPU execution needs independent review, the missing provenance receipts, and an orchestrator-authored GO note. Do not infer authorization from this guide or its template. Never automatically rerun a job killed by the cluster. Never overwrite a corrupt or stale capture receipt.

## Frozen decision

The baseline is R1 step 200, read 0, journal 4/0, file `evidence/direct_m200_room134.json`, SHA256 `c9b5994cc461420a0ccfb035cd252e27bac6da3016ab5d5a28f77a14239b319d`. Its 98 R0-dev rooms score 62.75510204081633 MRA; the unrounded bar is 67.75510204081633. A replacement requires a new registration before any R0-dev tower inference.

Only `da3_f32+R0` can pass: MRA must reach the unrounded direct score plus five and the paired 95% lower bound must exceed zero. NEAR reaches the observed margin without a positive lower bound. FAIL misses the margin. This establishes positive improvement with an observed five-point margin, not a true gain above five. The scorer jointly resamples physical rooms 10,000 times with `random.Random(17)`.

PASS/FAIL evaluates this complete measurement pipeline against R0 mesh labels, not geometry quality alone. Both arms retain the original labels. Those labels count mesh occupancy in 0.1 m xy cells; the call uses visible depth, 0.05 m cells, a height cut and two-frame support. A sensor-depth label audit is preregistered as diagnostic for every outcome. It cannot relabel, calibrate or reopen these rooms.

R0-dev is excluded from student training but has already been observed in direct-answer diagnostics. Those diagnostics cannot adjust this candidate. K1 held-out, R0-dev and benchmark rooms fit no rule, threshold, frame budget, admission policy or checkpoint. T10, u94, dev-S1 and all Part B results are report-only. No adaptive reruns are allowed. A PASS licenses the training-row plan under these exclusions. A trained-route claim requires a fresh unexposed set. Part B is exploratory and has a separate compute cost; the step-544 result cannot confirm adoption against this step-200 baseline.

“Unexposed” refers only to the audited student-training boundary. Tower pretraining overlap is unknown. The source design describes a benchmark-selected room rule; its relation to this kernel is unresolved. `configs/KERNEL_PROVENANCE.json` records MISSING rather than certifying a clean held-out design. No unreproducible power probabilities are used.

## CPU commands

Use the planner environment for conversion, tests and scoring:

```bash
cd /scratch/jjyeung/orch_n30/sb_roomkit
export PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES=''
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
P=/scratch/jjyeung/envs/planner_local_v1/bin/python
$P -B scripts/s0.py > out/S0.log 2>&1
$P -B vendor/kitcheck.py /scratch/jjyeung/geo_bakeoff_kit out/KITCHECK.json > out/KITCHECK.log 2>&1
$P -B scripts/reproduce.py > out/S1b.log 2>&1
$P -B tests/test_roomkit.py > out/TESTS.log 2>&1
$P -B scripts/score_room_pricing.py --direct evidence/direct_m200_room134.json --self-test > out/SCORER_SELF_TEST.log 2>&1
```

S0 verifies the full hashes in the review ledger, all 3,015 sealed files, five checkpoint files and all 15,228 PNGs. It pins the frame manifests and creates the 98-item R0-dev manifest. Missing or mismatched inputs are fatal. The full ledger verdict is `out/S0.json`; the original verifier also reports COMPLETE in `out/KITCHECK.json`. Its source is retained in `vendor/kitcheck.py`. The delivered KITCHECK receipt includes the input hashes from S0.

S1 uses the sealed runtime. Start only with at least 100 GB available RAM. Each process has six CPU cores and a 39 GiB address-space cap; two workers use twelve cores. Each runs the full 64-frame K1 forward, the 32-anchor forward, then one of the first two sorted R0-rl room scenes. No stored prediction substitutes for a tower forward.

```bash
source scripts/env.sh
export CUDA_VISIBLE_DEVICES=''
$GEO_BAKEOFF_ROOT/runtime/base/bin/python3 -B scripts/cpu_forward.py --capture scannetpp/067e2e4e61 --worker 0 > out/S1_worker0.log 2>&1 &
p0=$!
$GEO_BAKEOFF_ROOT/runtime/base/bin/python3 -B scripts/cpu_forward.py --capture scannetpp/036bce3393 --worker 1 > out/S1_worker1.log 2>&1 &
p1=$!
wait "$p0"
wait "$p1"
```

After these processes finish, use a fresh shell with the planner CPU environment above:

```bash
$P -B scripts/summarize_s1.py > out/S1_summary.log 2>&1
```

The 64-frame areas must lie within 5% of 14.73 and 39.35 m². Both 32/64 ratios outside [0.85,1.15] are reported without changing the protocol. R0-rl predictions under R0 and T10 are diagnostic only. S1b uses local stored predictions and local stored item rows because the trinity-3-30 tar and tree are unreachable here. It must match all 134 R0 rows and all 24 train table entries. It never fits held-out variants.

The adapter extracts only `attempt` and `areas` from the hashed harness source. It imports no harness module, global write hook or fixed-root initialization. It consumes the `(area, refusal)` tuple at `areas()['R0']`. Its explicit legacy adapter maps `depth_grid64` to `depth_grid` and `anchor_slots` to `item_slots`. S1b, S1 pricing and S3 share this converter and deployed kernel. `scripts/env.sh` overrides every kit cache and TMPDIR into this workspace.

## Required evidence before GO

An authorized owner must supply source evidence and complete these records; placeholders cannot pass the gate:

- `configs/KERNEL_PROVENANCE.json`: `status: VERIFIED`, exact kernel SHA256, `benchmark_selected: false`, `selection_scope: K1 train only`, an evidenced `relation_to_benchmark_rule`, `authorized_by`, and full `input_sha256` of locally supplied source records. If benchmark outcomes selected this kernel, do not certify the clean held-out protocol.
- `configs/READER_RECEIPT.json`: `status: VERIFIED`, frozen baseline SHA256, `step: 200`, `read: 0`, `journal: 4/0`, item SHA256 `607ba5798f06b77e713069bc57a9ed3b0e80db78ef81faa945487fadddc5e9c7`, journal SHA256 `6150faf39361621c3352de4fa5caa2ccff86858aaffd8f18e133eee6a5c3212f`, full checkpoint SHA256, exact `frame_indices_by_item` for all 98 R0-dev IDs, and full hashes of supporting source receipts available locally. The direct export alone does not prove frame identity.
- `out/S0.json`, `out/DRYRUN.json`, `out/K1_REPRODUCTION.json` and `out/TESTS.json` must pass, with unchanged hashed inputs. Revalidate tests after code edits. Seal the code before creating a GO note.

Missing source paths on trinity-3-30 are listed exactly in `configs/READER_RECEIPT.json` and `review/REVIEW_VERDICT.md`. The remote reproduction inputs are `/scratch/jjyeung/n30_mirror/b14_k1towers/geo_k1_mirror_1600Z.tar` and `/scratch/jjyeung/orch_n30/b14_k1towers/k1towers`. This lane makes no network request and cannot authenticate them.

## GO note format and GPU command

`configs/GO.template.json` is an unsigned, non-authorizing template. The orchestrator supplies a JSON note at `configs/GO.json` with:

- `decision: GO`, exact `host`, unique `run_id`, physical `gpu_uuid` such as `GPU-…`, `max_gpu_seconds: 5400`;
- `manifest_sha256`, `code_sha256` (canonical hash of the Python, shell and test code-hash mapping), `settings_sha256`, `provenance_sha256`, `reader_receipt_sha256`, as printed by `scripts/make_go_template.py` after the inputs are final;
- `allocation_samples`: two records with `unix_time`, `gpu_uuid`, `process_count: 0`, and `input_sha256` of saved allocation readings. Readings must be at least 300 seconds apart; the second must be at most 600 seconds old at launch.

The runner validates the note before touching CUDA, starts the cumulative budget, then checks the actual CUDA device count, UUID and capacity against the note. Exactly one device must be visible. The orchestrator must follow Trinity's allocation and vnice rules and arrange independent review; no GPU launch is authorized by this CPU task. On trinity-1-18, after authorization, the exact command is:

```bash
cd /scratch/jjyeung/orch_n30/sb_roomkit
source scripts/env.sh
export CUDA_VISIBLE_DEVICES="$(python3 -c 'import json; print(json.load(open("configs/GO.json"))["gpu_uuid"])')"
run_id="$(python3 -c 'import json; print(json.load(open("configs/GO.json"))["run_id"])')"
/data3/shared/scripts/vnice/vnice.sh "$GEO_BAKEOFF_ROOT/runtime/base/bin/python3" -B scripts/gpu_run.py --run-id "$run_id" --go-file configs/GO.json --provenance configs/KERNEL_PROVENANCE.json --reader-receipt configs/READER_RECEIPT.json
```

The 0.6 GPU-hour cost is an estimate. The cumulative 5,400-second budget includes model loads, captures, the first u94 memory measurement and any ordinary authorized retry. An OS elapsed-time alarm terminates the GPU runner at the deadline, including inside native calls; a reserve also stops new captures before the limit. The ledger reserves the entire remaining budget while RUNNING; an interrupted or deadline-expired ledger stops subsequent launches. A cluster-killed run requires a new orchestrator decision and manual accounting, never a relaunch loop.

The first u94 capture records allocated and reserved peak memory before the rest of that pass. CUDA OOM drops the secondary arm without lowering resolution. Every primary item remains mandatory. An incomplete u94 arm is excluded from its full-set table, with its drop receipt retained. A completed receipt is skipped only when predictions, exact frames and slots, weights, sealed code and settings still match. Corrupt, partial or stale receipts stop execution.

The optional dev-S1 guard is skipped in this kit because its authenticated reader-frame receipt is MISSING; it costs an estimated additional 0.050 GPU-hours if later preregistered with local frames. Part B is not implemented or authorized here and costs separately. Neither can change the confirmatory decision.

After S2, run S3 in a fresh planner CPU shell:

```bash
$P -B scripts/price.py > out/room_pricing/S3.log 2>&1
```

Outputs include the primary decision, paired intervals, diagnostic arms, refusals, label terciles, signed and absolute errors, supported/filled-cell ratio, u94 minus f32, per-capture timing/memory, total GPU-hours and input hashes. No R0-dev inference or confirmatory table exists in the CPU delivery. A second-node mirror is MISSING because this task forbids network access; the orchestrator can transfer the supplied tar.

Raw evidence and copied manifests retain their original bytes and schemas. Their full digests are recorded in the snapshot ledger and S0; newly generated JSON results carry `input_sha256`.
