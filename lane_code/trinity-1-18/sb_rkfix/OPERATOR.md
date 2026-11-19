# Room-call pricing kit

Run from `/scratch/jjyeung/orch_n30/sb_rkfix`. All writes, caches and temporary files stay here. External sealed runtime, model files, local frames and K1 predictions are read-only dependencies. The archive does not duplicate them. This delivery uses CPU only and authorizes no GPU launch.

## One R0-dev comparison

K1 training captures choose every arm, threshold and frame budget. R0-dev receives only the K1-selected DA3 arm under R0, against the frozen direct answer. T10, an additional u94 comparison and Part B are never priced on R0-dev. u94 can be the sole arm only if K1 selects it; in that case f32 receives no R0-dev look. dev-S1 is diagnostic only. Official benchmark items are never read.

The direct baseline is R1 step 200, read 0, journal 4/0, `evidence/direct_m200_room134.json`, SHA256 `c9b5994cc461420a0ccfb035cd252e27bac6da3016ab5d5a28f77a14239b319d`. Its R0-dev MRA is 62.75510204081633; the fixed unrounded bar is 67.75510204081633. PASS requires MRA at least the bar and a paired 95% lower bound above zero. NEAR reaches the bar without a positive bound; otherwise FAIL. This tests positive improvement with an observed five-point gain, not a true gain above five.

PASS/FAIL evaluates the complete measurement pipeline against R0 mesh labels, not geometry quality alone. The labels count mesh occupancy in 0.1 m xy cells; this call measures visible depth using 0.05 m cells, a height cut and two-frame support. A sensor-depth label audit is **proposed, unbuilt**. It cannot relabel, calibrate or reopen these rooms. DA3 reads low on K1-train ScanNet++ (median −6.9% in the supplied evidence); the R0 labels can count floor unseen in the 32 frames.

R0-dev's direct diagnostics cannot adjust this candidate. K1 held-out, R0-dev, dev-S1 and benchmark items fit no threshold, rule, budget, admission policy or checkpoint. A trained-route claim requires a fresh unexposed set. “Unexposed” describes only the audited student-training boundary; tower pretraining overlap is unknown.

## CPU validation

`bash scripts/cpu.sh` uses nice priority 10 and eight threads, disables CUDA and keeps caches here. Run stages sequentially:

```bash
bash scripts/cpu.sh scripts/s0.py > out/S0.log 2>&1
bash scripts/cpu.sh scripts/reproduce.py > out/S1b.log 2>&1
bash scripts/cpu.sh scripts/summarize_s1.py > out/S1_summary.log 2>&1
bash scripts/cpu.sh tests/test_roomkit.py > out/TESTS.log 2>&1
bash scripts/cpu.sh scripts/score_room_pricing.py --direct evidence/direct_m200_room134.json --self-test > out/SCORER_SELF_TEST.log 2>&1
```

S0 binds every local review-ledger input and its own script. S1b reproduces 134 stored room areas and 24 K1-train table entries. S1 aggregation validates the six supplied CPU-forward receipts; it launches no new forward. The two K1 32-frame captures are plumbing evidence only. Full frame-budget selection requires S1c.

## S1c: K1-train selection

Before inference, `selection.register` writes `out/room_pricing/S1C_REGISTRATION.json` with the code digest, exact 110 K1-train captures and this fixed choice rule:

> The R0-dev arm is da3_f32 unless the K1 dense-64 input beats it on K1 train with a paired 95% lower bound above 0; then it is da3_u94.

S1c runs DA3 on the 32 anchors alone for those captures. `selection.select` prices each f32 prediction and its stored dense-64 prediction using the same `adapter.convert` and `adapter.price` kernel as `reproduce.py`. It uses the K1 reproduction's MRA and room-paired bootstrap (10,000 draws, seed 20261119). `out/room_pricing/SELECTION.json` records all 110 rows, input hashes, paired interval and choice. It is immutable once written. Both runners reject stale or held-out selection records.

The GPU script below runs S1c and then the selected R0-dev pass inside one authorized invocation. The CPU fallback is:

```bash
bash scripts/s1c_cpu.sh > out/S1c_CPU.log 2>&1
```

Do not run that fallback under this task's two-hour limit. The supplied six-thread measurements imply about eight elapsed hours with two six-thread workers (twelve cores); those workers exceed this task's eight-core total. The shipped fallback uses one eight-thread worker, capped at 39 GiB, and is estimated to need about twelve hours under ideal thread scaling. No S1c forward has run in this delivery.

## Evidence and authorization

The orchestrator must provide these records with real supporting input hashes:

- `configs/KERNEL_PROVENANCE.json`: VERIFIED, exact kernel SHA256, `benchmark_selected: false`, `selection_scope: K1 train only`, an evidenced `relation_to_benchmark_rule` and `authorized_by`.
- `configs/READER_RECEIPT.json`: VERIFIED, frozen baseline hash, step 200/read 0/journal 4/0, item SHA256 `607ba5798f06b77e713069bc57a9ed3b0e80db78ef81faa945487fadddc5e9c7`, journal SHA256 `6150faf39361621c3352de4fa5caa2ccff86858aaffd8f18e133eee6a5c3212f`, checkpoint SHA256 and exact `frame_indices_by_item` for the 98 rooms.
- Passing `out/S0.json`, `out/DRYRUN.json`, `out/K1_REPRODUCTION.json` and `out/TESTS.json`, with current input hashes. The gate deduplicates their prerequisite hashes and rejects conflicting digests.

The reader sources are MISSING locally. Their expected paths on trinity-3-30 are `/scratch/jjyeung/orch_n30/cont_ops16/work/c15/r1route/out3/B/src/items/room134.json`, `/scratch/jjyeung/orch_n30/cont_ops16/work/c15/r1route/out3/B5/ret/metadata/reads/0/metadata/journals/4/0/items.jsonl`, and `/scratch/jjyeung/orch_n30/cont_ops16/work/c15/r1route/out3/A/src/tree`. The direct export alone proves no reader-frame identity. Kernel-selection evidence is also MISSING. Do not infer a clean held-out design from the kit.

After validation, `bash scripts/cpu.sh scripts/make_go_template.py` writes `configs/GO.template.json` with decision NOT_GO. The orchestrator supplies `configs/GO.json` containing decision GO, current host, unique run_id, physical gpu_uuid (`GPU-…`), max_gpu_seconds 5400, manifest/code/settings/provenance/reader hashes from the template, and two allocation samples. Samples must show that UUID empty at least 300 seconds apart, with the latest at most 600 seconds old, and bind saved evidence by SHA256.

The runner calls preauthorize before prerequisite hashing or CUDA. It checks one actual visible device, prefixes torch's bare UUID with GPU-, and requires at least 48 GB. Only after an authorized allocation and independent review may the orchestrator run:

```bash
export CUDA_VISIBLE_DEVICES='GPU-<authorized physical UUID>'
bash scripts/s1c_gpu.sh --run-id '<unique run ID>' --go-file configs/GO.json --provenance configs/KERNEL_PROVENANCE.json --reader-receipt configs/READER_RECEIPT.json
```

`--stage all` in that wrapper performs S1c and the selected R0-dev inference. `scripts/gpu_run.py --stage s1c` stops after selection; the default `--stage r0dev` refuses to proceed without SELECTION.json. The script uses vnice. `env.sh` preserves the caller's shell options.

Estimate 0.09 GPU-hours for S1c plus 0.09 for f32 R0-dev on one 48 GB card. If K1 selects u94, its R0-dev estimate is about 0.46 GPU-hours. The cumulative 5,400-second budget includes loads, captures and authorized retries. There is no secondary memory probe or secondary pass. An OOM records ARM_DROPPED.json and aborts; no fallback or resolution reduction is allowed, and pricing refuses dropped arms. dev-S1 and Part B receive no GPU work here.

## Interrupted and completed captures

DONE.json records host, card and run for provenance. Its skip binding excludes those operational identities and includes model, weights, sealed code, exact frames, slots, frame hashes, settings and arm. Completed predictions can resume under a new authorized host/card/run only when every stable field and prediction digest matches. Corrupt or partially written predictions stop execution.

A folder containing only STARTED.json is interrupted. Never automatically retry a cluster-killed job. The orchestrator must verify the old process has ended, manually account its elapsed GPU time, and close `out/room_pricing/COST.json` with `state: MANUALLY_CLOSED`, conservative cumulative `charged_seconds`, `authorized_by`, `accounted_run_ids` containing the interrupted run ID, and hashes of supporting accounting evidence. Preserve the folder and STARTED receipt. Obtain a fresh GO for the new host/card/run. The runner accepts that closure only for the named interrupted run, checks its stable binding, and recomputes it without deleting anything. A RUNNING ledger, an unnamed run, or a stale binding remains blocked. ARM_DROPPED.json remains a terminal stop for this experiment.

## Consume the one look

After the selected arm is complete, run once:

```bash
bash scripts/cpu.sh scripts/price.py > out/room_pricing/S3.log 2>&1
```

Before converting any R0-dev prediction, price.py creates DECISION_REGISTRATION.json exclusively with bar, selected arm, R0, decision rule, code digest and input hashes. Existing registration, ROOM_PRED.jsonl or PRICING_TABLE.json blocks execution. This also blocks concurrent or failed-read retries. Do not remove, rename or reset these records to get another look. The scorer CLI refuses --pred; its public self-test uses synthetic echoes/oracles and reads no tower predictions.

PRICING_TABLE.json contains only the selected-arm/direct R0-dev comparison and the frozen direct dev-S1 diagnostic block. No R0-dev prediction, decision registration or confirmatory pricing table exists in this delivery. A second-node mirror is MISSING because this task prohibits network access.

Package with `bash scripts/cpu.sh scripts/package.py`. Deliver `out/sb_rkfix.tar`, `out/sb_rkfix.tar.sha256` and `out/DELIVERY_SHA256.txt`. The packager verifies every listed archive member without extracting it.
