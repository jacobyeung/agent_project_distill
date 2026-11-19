# Disposable production profile

Run only on the already allocated, admitted four-GPU production host. `TREE` must be the sealed patched checkout; `CONFIG` must have fresh native admission for that tree. The kit never checkpoints, exports, publishes, or updates the production output. Receipts and locks go under `OUT/trainer`.

```bash
TREE=/scratch/reviewed_tree CONFIG=/scratch/admitted_config.json OUT=/scratch/profile_fresh \
  PYTHON=/path/to/production/python bash out/kit_profile/run.sh
```

The shell bounds the whole run, including imports, admission and model loading, to 895 seconds plus a five-second termination grace. It instruments **one optimizer step immediately**, with no separate warm-up. A cold first step took 440.3 seconds in the supplied production log; budget roughly 440 seconds plus startup and instrumentation, rather than assuming steady state. Completion within 15 minutes is not guaranteed when startup is slow. Exit 124 or an incomplete progress record means INCOMPLETE. Do not retry a killed run automatically.

`progress.json` exists before torch imports. `heartbeat.json` and `SO_PROGRESS` update every 30 seconds. Each completed microstep emits `SO_MICROSTEP` and a nonblocking `phase_partial.json`; TERM/INT also saves partial completed scopes. A stuck C++ call may defer the Python signal handler, but the last heartbeat/partial table remains. Partial event totals exclude unfinished scopes and unfinished events. They are lower bounds, not a full-step measurement.

CUDA events record on the calling thread's actual current device stream, including autograd device workers. `_unshard` uses its explicit all-gather stream; reduction hooks run on the native post-backward stream. The CPU row producer never records CUDA events. A shared backward flag and autograd graph-task ID identify recompute. Phase ranges overlap and nest: do not add their stream elapsed times. `phase_table.json` is the full-step table; `profiler_table.json` and the scrubbed `trace.json` cover a bounded prefix (four microsteps by default, maximum eight). `trace_summary.py trace.json` computes interval unions without double counting. CUDA attribution has mocked-stream tests here; real CUDA validation remains a production task.

`RESUME_PIN` names a JSON file containing the native `{path, sha256}` pin of a completed checkpoint manifest. A checkpoint from the same sealed configuration works directly. To measure a production checkpoint written under a different source seal, also set `RESUME_CONFIG` to that checkpoint's original configuration JSON:

```bash
RESUME_PIN=/scratch/pinned_checkpoint.json RESUME_CONFIG=/scratch/production_config.json \
  TREE=/scratch/reviewed_tree CONFIG=/scratch/admitted_patched_config.json \
  OUT=/scratch/profile_resume_fresh PYTHON=/path/to/production/python \
  bash out/kit_profile/run.sh
```

Before model loading, the read-only bridge verifies the pinned checkpoint's schema, original config identity, original source commit, world size, unchanged training configuration, and equal prepared data. It allows only source/provenance differences already excluded from native training identity. The native restore reads the original binding and retains shard-layout, buffer, RNG and file-pin checks. Native authentication and admission still apply to the patched tree. It never rewrites the checkpoint. A missing original config or changed data/training setting fails early with a specific error. Without a checkpoint, omit both resume variables.

The kit inherits production CPU-thread and tokenizer settings. Each manifest records effective intra-op/inter-op counts and OMP/MKL/OpenBLAS/tokenizer environment variables. Do not impose the Trinity test runner's eight-thread setting on production.

`probe.sh` runs one Python command in the real production environment after its kernel overlay. It prints acceptance booleans and hashed bindings. Binding slots 0–4 are convolution, convolution-update, chunk rule, recurrent rule and gated norm, respectively. A true linear-kernel gate with a false convolution gate identifies partial fallback; both false identify full fallback. Actual layer bindings are hashed in the run manifest. Range names use `lin_attn/*`; class/module/parameter names are opaque. Trace text, trainer receipts and shell logs pass through the output filter; the raw trace lives only in a memory file descriptor before scrubbing.

Before `train()`, each rank refuses another compute process on its target GPU or less than 76,699 MiB free, the maximum production usage observed in `look2.out`. The GPU probe fails closed and writes `gpu_guard.json` on success. This check runs inside the 895-second limit and does not grant allocation or prevent a later co-tenant race; the host must already be exclusively admitted for these target GPUs.

## Continuation acceptance replay

`replay.sh` uses `launch.py --mode replay`: one update, zero warmup and no profiler. It runs OFF, OFF, ON in that order from the same explicit `RESUME_PIN` and CPU-audited `PLAN`. Set `AUDIT_DIR` to the eight completed data audits and `OUT` to fresh scratch. Hold 03 constant with `REPLAY_METRICS=0|1`; 02 and fallback remain OFF. `RESUME_CONFIG` supplies the original checkpoint configuration when needed by the source-only bridge.

The exact invocation, CPU plan writer, metric fields and acceptance rules are in [NOTE_FOR_TREE_REBUILD.md](../NOTE_FOR_TREE_REBUILD.md). Estimate 50–75 minutes total for three cold one-step replays and startup/restore. Each leg has a 3,600-second cap, heartbeat and no retry. This replay is separate from the 895-second instrumented profile above. `kit_timing/replay_compare.py` checks the completed legs and writes `acceptance.json`; missing ON `performance.C1_CPU_PREFETCH="1"` fails the gate. The plan writer’s merged receipt is a private operational input whose lossless JSON escapes preserve paths without literal model words; it must remain outside published reports.
