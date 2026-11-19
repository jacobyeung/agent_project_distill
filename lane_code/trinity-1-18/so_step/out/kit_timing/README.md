# Fixed-plan production timing

Use the sealed patched checkout and a freshly admitted production configuration. Export `TREE`, `CONFIG`, a fresh `OUT`, and `PYTHON`; use the production thread environment unchanged. Export explicit scratch paths for `CUDA_CACHE_PATH`, `TRITON_CACHE_DIR`, and `TORCHINDUCTOR_CACHE_DIR` matching the production cache policy. Do not clear caches between arms. The profile README describes `RESUME_PIN` and optional `RESUME_CONFIG`; every arm restores the same checkpoint, or the same seeded initial state when both are omitted.

```bash
bash out/kit_timing/run.sh
```

The defaults are **three repeats, 20 discarded warm-up updates and 20 measured updates per arm**, with fixed row plans shared across all runs. Each repeat runs OFF/prefetch/OFF/cache/OFF/metrics/OFF; alternate repeats reverse the ON order. Every ON arm is compared with the average of its adjacent OFF arms at matching update indices. `REPEATS` accepts 3–30, `WARMUP` and `MEASURE` accept 10–100. Per-arm timeout is three hours (`ARM_SECONDS`, bounded to 60–43,200 seconds). A failure or timeout stops the entire script, without a retry. All runs are disposable and write only under `OUT`.

This is a precision experiment, not a short smoke test. At the measured 133-second steady-state rate, the default 840 updates alone take about **31 hours**, plus cold-start excess and model loading. That is an estimate, not a measured kit runtime. Plan the production allocation accordingly; the separate profile kit retains its 15-minute bound. Twenty warm-up updates put the measured window at updates 21–40, matching the supplied log's stable-analysis cutoff. The shorter ten-update setting is allowed for diagnostics but needs the same precision gate.

The summary uses the slowest rank for each update. It reports paired wall/data differences, forward/backward host time per microstep, first-step bitwise loss parity, and cache counters. Negative forward/backward host gains mean the producer slowed the training host work. It refuses mismatched plans, trainables, bindings, thread settings, or losses. It compares OFF brackets first, writes the timing table and parity diagnostics to `comparison.json`, then refuses loss mismatches. OFF nondeterminism invalidates switch attribution. `cache_before/after.json` inventories up to 4096 top-level cache entries with hashed names, size and mtime; it marks truncation and does not claim a recursive cache-content census.

**Minimum detectable difference:** treat each repeat's mean paired gain as one sample, because neighboring updates are correlated. With repeat standard deviation `s`, `n` repeats, two-sided alpha 0.05 and approximate 80% power, the kit reports `MDD = (t(.975,n-1) + t(.80,n-1)) * s / sqrt(n)`. It uses conservative Student-t critical values. With three repeats, MDD is **3.0969 × s**: repeat SD 1.0 s permits detecting about 3.10 s; SD 0.323 s permits about 1.0 s. These are planning calculations, not measured variance. No finite kit can guarantee detecting a zero gain. `resolved=false` forbids a positive speedup claim; `target_1s_resolved=false` means the estimated ≤0.1-second metrics gain remains unresolved unless the observed effect exceeds its reported MDD. Increase the preplanned repeats/steps for a fresh authorized experiment if needed; do not silently claim a small gain or relaunch a killed run. Reports with fewer than three repeats explicitly have no MDD or resolved result.

The delivered gains remain hypotheses until this kit produces production measurements. The decoded cache is expected to save at most zero seconds under low reuse: misses add a read and SHA-256. Its cumulative hit/miss/byte counters are recorded per step; use differences between consecutive records for hit rate and decode reuse. Cache and prefetch savings overlap.

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

For continuation acceptance, first run `write_plan.py --tree "$TREE" --config "$CONFIG" --receipt "$RECEIPT" --resume-pin "$RESUME_PIN" --steps 10 --out "$PLAN"`. The writer uses the same sampler arguments as native `run_steps`, starting at the pinned checkpoint step plus the configuration's row offset. Use a fresh plan file.

Run `data_only.py --steps 10 --require-coverage` for four rank projections and OFF/prefetch arms, serially, in separate processes. The exact commands are in [NOTE_FOR_TREE_REBUILD.md](../NOTE_FOR_TREE_REBUILD.md). This audit costs about 42 minutes estimated from the supplied data timer; allow 45–60 minutes including startup and hashing. `--full-plan` audits every supplied plan; the acceptance plan contains 10 updates.

The kit requires actual nonzero augmented pose calls, records worker thread names, and checks every emitted processor grid against `[32,20,26]`. It refuses missing augmented-pose coverage. Sidecars record the continuation step/pin, checked plans, grid and augmentation coverage, group tensor bytes including targets/audits, and Linux process `peak_rss_bytes`. RSS includes the worker's deep-copied receipt/processor and all startup allocations. The default 1-GiB group guard still applies; the audit keeps optional fallback OFF. `align_settings` follows the receipt so teacher-aligned pose targets receive the real validation.

This audit compares hashes and row draws, with unchanged Python/NumPy/torch RNG. It does not load a model or prove GPU loss/gradient equality. Hash time is included in wall time and reported separately. GPU-copy and simulated-consumer variants cannot establish a training speedup. Run on the actual production processor; the local CPU environment lacks torchvision.

For a short numerical acceptance replay, use [kit_profile/replay.sh](../kit_profile/replay.sh), not the long precision experiment above. It runs OFF, OFF, ON, one update each from the same checkpoint and audited plan. `replay_compare.py` requires bitwise ON losses when OFF repeats agree, otherwise ON deviations no larger than the per-scalar OFF spread, with identical CPU inputs in either case. It also requires ON step provenance. Estimated wall time is 30–60 minutes total; each leg has a 60-minute limit and no automatic retry. This acceptance policy is separate from the long timing experiment's stricter bitwise parity gate.

Both GPU kits refuse another compute process on a target or free memory below 76,699 MiB, the supplied production peak. The timing wrapper checks all visible targets before each arm; each rank checks its own target before `train()`. An unreadable GPU probe fails closed. These checks do not replace the existing allocation/admission requirement.
