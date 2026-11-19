# Review package for build 21b — keep cross-run adoption disabled

Apply this additive patch **after N's first proof**, for review and CPU experimentation. It is not a completed cross-run preparation store. The patch provides a native CPU entry, a small-input dependency-recorder prototype, an object-store library, a comparison CLI, and tests. It adds no GPU-wrapper hook. Do not treat the store's self-consistent hashes as training admission.

The base is `in/tree21b/work/tree_r1`, source seal `b262e7a757d93e2485a523765916507b2bf3305fe3213cffca100007d19f2ce8`. Verify `out/patches/manifest.json`, including the complete base-tree pin, before applying with no fuzz:

```bash
patch --batch --fuzz=0 -p1 -i "$L/out/patches/01_native_cpu_and_store_groundwork.diff"
```

All 936 existing source files remain byte-identical. Added files still change the source inventory. Rebuild the source archive, source/config seals, kit inventory and scan certificate through the native builder before any real invocation. A different base, including a later build, needs a fresh port and validation. The current patch does not depend on the per-node cache patch from `so_launch`; do not enable that cache.

## CPU-only native preparation

The CPU entry requires `TK_NATIVE_CPU_PREPARE=1`; it defaults OFF. Run it only after the selected parent export and its authenticated handover closure are available and all inputs/RGB are staged. It uses the same `student_pilot.s1_admission.admit` function as mode p, including all native parent/source/data/frame checks. It preserves existing journals on refusal. No GPU query or scheduler call is made by this entry.

The example assumes the exact reviewed config and native logical input namespace are already available. `CONFIG_SHA256` must come from the reviewed configuration pin. `OUTPUT` is a new owned node-local directory; use `--resume` only for that same native request. The entry refuses any indicated GPU allocation, including device index zero in `SLURM_JOB_GPUS`.

```bash
nice -n 10 env TK_NATIVE_CPU_PREPARE=1 CUDA_VISIBLE_DEVICES='' \
  OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 \
  TOKENIZERS_PARALLELISM=false PYTHONDONTWRITEBYTECODE=1 \
  /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B \
  scripts/preparation_cpu.py \
  --config "$CONFIG" --config-sha256 "$CONFIG_SHA256" \
  --output "$OUTPUT" --frame-root "$FRAME_ROOT" \
  --threads 8 --memory-gib 30 --max-seconds 21600
```

Thirty GiB is the local test ceiling, **not a measured production requirement**. The CLI supports an explicit larger memory ceiling on an authorized CPU host, but this lane did not run one. Eight-core production walltime is unknown. The measured mode-p envelopes used native admission configured for 16 threads. Full preparation RAM/disk sizing must come from phase telemetry and storage measurements, not from the GPU allocation's memory request.

This entry writes the existing path-bound journal and separate `cpu_telemetry_<attempt>.json`. Its telemetry explicitly states `store_published=false` and `cross_run_adoptable=false`. It does not solve transfer to another node/run. The GPU wrapper currently requests 16 CPU threads, while this bounded entry supports at most eight; native request equality also prevents treating its journal as a transparent wrapper cache. A completed native adoption interface must regenerate the destination request.

## Comparator and tests

The experimental primitives require `TK_XSTORE_EXPERIMENT=1`; they also default OFF. The comparator accepts two supplied roots and compares every named object without normalizing differences:

```bash
nice -n 10 env TK_XSTORE_EXPERIMENT=1 \
  /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B scripts/compare_preparation_stores.py \
  --left "$STORE_A" --left-root "$ROOT_A" \
  --right "$STORE_B" --right-root "$ROOT_B" --key "$EXPECTED_KEY"
```

`EXPECTED_KEY` must be independently established. This package has no native planner to establish it for N. The delivered cold-store equality test is a protocol fixture, not two native preparation runs or two-node evidence.

From `$L`, run `source work/env.sh`, then the exact test/package commands in `out/REPORT.md`. `work/run_gloo.sh` is an optional runner for the tree's existing Gloo baseline tests only; it has not been executed here and does not implement the requested prepare/adopt loss comparison.

## Required work before enabling an adopter

Separate content production from native run/config/source bindings, including N's handover target map. Route every consumed config/environment/file/runtime input through an enforceable native planning and execution interface; the prototype recorder's 64 MiB reader and Python audit hook are insufficient for N's production data. Define portable native receipt and SQLite schemas before testing determinism. Implement verified fetch, private materialization, native admission regeneration, atomic destination publication, and receipt-backed fallback without displacing partial/foreign journals. Bind the root to a trusted producer or independently recompute its output; a hash/key match alone is insufficient.

Then run two independent cold builds and every-rank first-loss comparisons against full in-job preparation. All six mismatch twins must fall back and retain the baseline loss. Run the independent admission review against those exact source/config/store pins before enabling adoption.

On first real use, measure CPU prepare walltime, peak RSS, CPU utilization, input/output/temp bytes, object count, upload/fetch bytes and time, full SHA verification time, native adopt time, fallback overhead, and all-rank first loss. Calculate launch saving as the measured cold mode-p envelope minus measured fetch/verify/adopt/remaining-frame cost. Do not report a speedup from fixture timing.
