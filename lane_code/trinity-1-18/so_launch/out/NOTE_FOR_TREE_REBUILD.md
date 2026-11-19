Apply these four **source-tree** patches after N's first proof, before building a new sealed kit. This delivery covers S1 only. It preserves full configuration identity and native receipt bytes, so a new logical run misses; R2 caching is unfinished.

1. Apply from the repository root, in this order:

   ```bash
   patch --batch --fuzz=0 -p1 -i "$L/out/patches/01_prepared_input_cache.diff"
   patch --batch --fuzz=0 -p1 -i "$L/out/patches/02_parallel_frame_sha.diff"
   patch --batch --fuzz=0 -p1 -i "$L/out/patches/03_checkpoint_verify_memo.diff"
   patch --batch --fuzz=0 -p1 -i "$L/out/patches/04_launch_phase_timing.diff"
   ```

   Each patch also applies independently to build 20. Check patch SHA256 and base-file hashes in `patches/manifest.json`. Build 21 may need a reviewed port; reject patch failures or fuzz. Do not apply directly to an already sealed/running kit.

2. Rebuild the source archive, source/config seals, executable inventory and scan certificate through the normal builder. The new `b/pc.py` must enter that inventory. Retain the native review, authorization, frame-host, parent and all-rank first-step gates. Changing code intentionally invalidates existing cache keys.

3. Run the delivered tests with CUDA hidden, bytecode disabled and OMP/MKL/OpenBLAS capped at eight; run Python under `nice -n 10` using `/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B`. Set `TEST_TMP_ROOT`, `TMPDIR` and `LANE_TEST_OUTPUT` to owned scratch directories. Execute the five test scripts named in REPORT.md's command table, then its native runner. Fresh standalone and combined applications passed **49 new tests and 51 selected native regressions**. Exact outputs: `tests/20261119T072417Z/`. Five failures in the separate stale admission fixture also reproduce on the untouched input; REPORT.md identifies them.

4. Keep all switches OFF for the normal proof. For a later controlled canary, enable one change at a time:

   | Switch | Additional setting | Check |
   |---|---|---|
   | `TK_LAUNCH_TIMING=1` | None | Steps log separates guard, chooser and stage-lock time. |
   | `TK_PARALLEL_FRAME_SHA=1` | `TK_FRAME_SHA_WORKERS=4` | Every digest still verifies; watch storage contention. |
   | `TK_PREPARED_INPUT_CACHE=1` | Absolute `TK_PREPARED_CACHE_ROOT` outside the run's inputs | First eligible producer reports BUILT; matching consumer reports HIT. |
   | `TK_CHECKPOINT_VERIFY_MEMO=1` | Existing job ID/allocation clock | First check hashes fully; only an unchanged repeat in that allocation hits. |

5. Seed the producer with an absent target; the cache does not relabel an unregistered native journal. Inspect `o/<job>.prepared-cache.json` and its SHA-pinned producer receipt. Confirm source job, full key, source/target paths and every file/frame digest. Test corruption, missing/partial source, pool purge and a code/config change: each must rebuild or use an intact native journal. Compare native seals, prepared rows, sampling and actual first-step admission. Retain the source until its verified copy finishes; preserve refused artifacts for inspection.

Measured cold mode p costs 140.57–145.27 minutes. The cache's **estimated 120-minute saving** assumes an absent same-logical-run target, retained source, warm frames and 20–25 minutes of verification/copying; production verification time is unmeasured. An already complete native journal or a new logical run has **zero estimated rebuild saving**. Parallel SHA has a conditional **0–17.5-minute estimated range**. Timing saves no time directly; the checkpoint memo saves time only on a duplicate chooser check. The second-stage bypass, first-step warmup and slot destination-verify changes are not built.
