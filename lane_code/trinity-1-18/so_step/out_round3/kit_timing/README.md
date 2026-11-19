# Fixed-plan production timing

Use the sealed patched checkout and a freshly admitted production configuration. Export `TREE`, `CONFIG`, a fresh `OUT`, and `PYTHON`; use the production thread environment unchanged. Export explicit scratch paths for `CUDA_CACHE_PATH`, `TRITON_CACHE_DIR`, and `TORCHINDUCTOR_CACHE_DIR` matching the production cache policy. Do not clear caches between arms. The profile README describes `RESUME_PIN` and optional `RESUME_CONFIG`; every arm restores the same checkpoint, or the same seeded initial state when both are omitted.

```bash
bash out/kit_timing/run.sh
```

The defaults are **three repeats, 20 discarded warm-up updates and 20 measured updates per arm**, with fixed row plans shared across all runs. Each repeat runs OFF/prefetch/OFF/cache/OFF/metrics/OFF; alternate repeats reverse the ON order. Every ON arm is compared with the average of its adjacent OFF arms at matching update indices. `REPEATS` accepts 3–30, `WARMUP` and `MEASURE` accept 10–100. Per-arm timeout is three hours (`ARM_SECONDS`, bounded to 60–43,200 seconds). A failure or timeout stops the entire script, without a retry. All runs are disposable and write only under `OUT`.

This is a precision experiment, not a short smoke test. At the measured 133-second steady-state rate, the default 840 updates alone take about **31 hours**, plus cold-start excess and model loading. That is an estimate, not a measured kit runtime. Plan the production allocation accordingly; the separate profile kit retains its 15-minute bound. Twenty warm-up updates put the measured window at updates 21–40, matching the supplied log's stable-analysis cutoff. The shorter ten-update setting is allowed for diagnostics but needs the same precision gate.

The summary uses the slowest rank for each update. It reports paired wall/data differences, forward/backward host time per microstep, first-step bitwise loss parity, and cache counters. Negative forward/backward host gains mean the producer slowed the training host work. It refuses mismatched plans, trainables, bindings, thread settings, or losses. It compares OFF brackets first, writes the timing table and parity diagnostics to `comparison.json`, then refuses loss mismatches. OFF nondeterminism invalidates switch attribution. `cache_before/after.json` inventories up to 4096 top-level cache entries with hashed names, size and mtime; it marks truncation and does not claim a recursive cache-content census.

**Minimum detectable difference:** treat each repeat's mean paired gain as one sample, because neighboring updates are correlated. With repeat standard deviation `s`, `n` repeats, two-sided alpha 0.05 and approximate 80% power, the kit reports `MDD = (t(.975,n-1) + t(.80,n-1)) * s / sqrt(n)`. It uses conservative Student-t critical values. With three repeats, MDD is **3.0969 × s**: repeat SD 1.0 s permits detecting about 3.10 s; SD 0.323 s permits about 1.0 s. These are planning calculations, not measured variance. No finite kit can guarantee detecting a zero gain. `resolved=false` forbids a positive speedup claim; `target_1s_resolved=false` means the 0–3-second metric estimate remains insufficiently resolved unless the observed effect exceeds its reported MDD. Increase the preplanned repeats/steps for a fresh authorized experiment if needed; do not silently claim a small gain or relaunch a killed run. Reports with fewer than three repeats explicitly have no MDD or resolved result.

The delivered gains remain hypotheses until this kit produces production measurements. The decoded cache is expected to save approximately zero seconds under low reuse. Its cumulative hit/miss/byte counters are recorded per step; use differences between consecutive records for hit rate and decode reuse. Cache and prefetch savings overlap.

## Data-only variant for one 48 GB GPU or CPU

The smaller kit reads real staged rows and runs the real processor, without model/FSDP/optimizer work. It supports `--gpu-copy` and optional `--pin`; CPU is the default. ON arms require the OFF output and compare every encoded batch/target row SHA-256, including shape, dtype and raw tensor bytes. It also compares each ordered `row_draws` triple (stream, planned index, admitted candidate). The `all` arm tests prefetch plus decoded caching together. All arms also require unchanged global Python/NumPy/torch RNG state.

```bash
python out/kit_timing/data_only.py --tree "$TREE" --receipt "$RECEIPT" \
  --manifest "$BASE_MANIFEST" --config "$CONFIG" --plan "$PLAN" \
  --out "$OUT/data_off.json" --arm off
python out/kit_timing/data_only.py --tree "$TREE" --receipt "$RECEIPT" \
  --manifest "$BASE_MANIFEST" --config "$CONFIG" --plan "$PLAN" \
  --out "$OUT/data_all.json" --arm all --baseline "$OUT/data_off.json"
```

`PLAN` can be `r0_l0_off/rank0/plan.json`. The default consumes its first ten plans; `--steps` accepts 1–100 within the available plan length. Before any production prefetch ON run, supply a complete epoch plan and use `--full-plan` on every rank projection, serially. This option removes the step cap and records every group's conservative tensor-storage bytes (batch, targets and audit tensors), per-step `max_group_tensor_bytes`, and sidecar `peak_group_tensor_bytes`, rank, world and plan coverage. The sidecar records `full_plan=true`; the operator must verify that the supplied plan is the entire epoch. OFF auditing fails after writing its output if any group exceeds 1 GiB. The same storage can count more than once, matching the producer's conservative guard; these counts do not measure RSS. Repeat the ON command with `--arm prefetch` and `--arm cache` for individual comparisons. The sidecar manifest records effective thread settings. Hashing cost is reported separately and included in wall time; it is a parity test, not a training speedup measurement. `--consumer-ms` introduces only a simulated delay. This variant cannot establish loss/gradient parity, inter-rank admission, FSDP overlap, model-memory fit or end-to-end GPU gains. Run it with the actual production processor assets before enabling threaded prefetch.

Both GPU kits refuse another compute process on a target or free memory below 76,699 MiB, the supplied production peak. The timing wrapper checks all visible targets before each arm; each rank checks its own target before `train()`. An unreadable GPU probe fails closed. These checks do not replace the existing allocation/admission requirement.
