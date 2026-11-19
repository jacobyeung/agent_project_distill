VERDICT: GO

Reviewer: independent, read-only, CPU only. Paths: `S=/scratch/jjyeung/orch_n30/so_step`, `T=S/work/b21_final/work/tree_r1` (patched build 21), `B=/scratch/jjyeung/orch_n30/so_xstore/in/tree21b/work/tree_r1`, `L=/scratch/jjyeung/orch_n30/so_in/scratch/jjyeung/orch_n30/swarm_opt/work/o`, `NOTE=S/out/NOTE_FOR_TREE_REBUILD.md`, `TF=/scratch/jjyeung/envs/p1cpu/lib/python3.12/site-packages/transformers`. Line numbers follow `grep -n` (LF-only) numbering.

## Answer

- **First launch of vehicle N (01, 02 and fallback OFF; 03 ON allowed): GO.**
  - The trainer patches are byte-identical to the round the previous review cleared. All-OFF output stays byte-identical to the base, with no `performance` or `cpu_prefetch` field.
  - The 31-test coordinator gloo gate passed on these bytes (`S/work/round3_b21_gloo_by_coordinator.txt`: `Ran 31 tests in 880.158s`, `OK`, `EXIT=0`, 12:55:19 UTC, all three proofs present).
- **First continuation with 01 ON under the note's acceptance and kill rules: GO.**
  - Previous HIGH 1 is fixed: both grid orientations pass, and all 288 real production rows pass the new cap.
  - Previous MEDIUM 2 is fixed: the replay rule is passable and sound enough to serve as a screen behind the strict CPU row-hash gate.
  - The remaining findings are LOW or INFO, and every one of them fails closed. Findings 1 and 2 are cheap to fix before the CPU audit and replay run. Finding 2 must be decided before the ON leg is seen, because the rule is pre-registered.

## Findings

1. **LOW: The audit's spatial cap (520 patches) is below the processor's own limit (576), so 16:9 or square sources would fail the audit although the trainer accepts them.**
   - **Evidence, processor limit:** The trainer passes `longest_edge = 32*384*384` (`T/student_pilot/batches.py:155`). The installed `smart_resize` keeps `t*h_bar*w_bar <= max_pixels` (`TF/models/qwen3_vl/video_processing_qwen3_vl.py:50-57`), so `h*w <= 384²/16² = 576` patches.
   - **Evidence, no fixed frame size:** `load_rgb` keeps each source's original resolution and enforces no size (`T/student_pilot/batches.py:84-91`).
   - **Computed with the installed function:**
     - 640×480 and 1920×1440 give `[32,20,26]`; the portrait versions give `[32,26,20]`.
     - 1752×1168 gives `[32,18,28]`.
     - 1920×1080 and 1280×720 give `[32,18,32]`; 512×512 and 480×480 give `[32,24,24]`. These are 576 patches.
   - **Reproduced:** `Coverage().observe` refuses `[32,18,32]`, `[32,32,18]` and `[32,24,24]` with "exceeds audited grid cap" (`S/out/kit_timing/audit.py:35-37`).
   - **Byte budget is not the constraint:** 8 rows at 576 patches hold 905,969,664 FP32 pixel bytes, under the 1 GiB guard. Pose targets are sparse points (`T/student_pilot/decoupled_v.py:174-195`).
   - **Impact on N:** All 288 real rows (`L/look2.out:694,698,702,706`) fall in `{[32,20,26],[32,26,20],[32,12,16],[32,16,12]}` and pass, so the audit can pass on run A's data. If N's first 10 updates contain a 16:9 or square source, the audit refuses and 01 stays OFF.
   - **Smallest fix:**
     - Use `grid[1]*grid[2] <= 576` and `grid[0] <= 32` in `audit.py:36`, and update `data_only.py:141` and `NOTE:90`.
     - Add `[32,18,32]` and `[32,24,24]` as accepted cases and `[32,20,30]` as a refused case.

2. **LOW: The pooled replay rule requires each of the four ranks to pass separately, so its false-refusal rate under OFF nondeterminism can reach about 80%. The rate is not stated.**
   - **Evidence:** `S/out/kit_timing/replay_compare.py:21-25` computes `M <= 2*D` per rank, and `:93-95` requires every rank (`report['accepted'] &=`). `NOTE:147-156` and `NOTE:182-185` apply the same rule to the continuation's `components` and `stream_means`.
   - **Exact worst case:** When one scalar dominates a rank's spread, the rule passes iff ON lies in `[min(OFF)-D, max(OFF)+D]`. For three exchangeable runs, ON fails only when it is the extreme point and its gap exceeds the other gap, so the pass probability is exactly 2/3, independent of the noise distribution. Four independent ranks give (2/3)^4 ≈ 0.20.
   - **Simulated (Gaussian noise, n comparably noisy scalars per rank, four independent ranks):**

     | Rule | n=1 | n=4 to 5 | n=12 to 20 |
     |---|---:|---:|---:|
     | Per rank, k=2 (as delivered) | 0.20 | 0.57–0.65 | 0.88–0.95 |
     | Pooled across ranks, k=2 | 0.87 | 0.98 | ≥0.998 |

   - **Consequence:** Kill rule 1 uses only components and stream means. These are averages of the same microstep losses, so the effective n is smaller there than in the replay. A correct 01 must pass the rule twice.
   - **Mitigation:** The expected regime is the strict bitwise branch, which a correct ON passes with probability 1. First-update losses come only from forwards at the restored parameters (one optimizer step ends the update), so only forward-kernel nondeterminism can make the OFF legs differ. Soundness rests on the CPU row-hash gate, which is strict.
   - **Smallest fix, chosen before the ON leg runs:** Either:
     - pool D and M over all four ranks (same multiplier), or
     - state the false-refusal rate in `NOTE:147-156`.

     Add a test where each rank's single scalar falls outside `[min-D, max+D]` but inside the pooled bound.

3. **INFO: The continuation kill rules have no executable command.**
   - **Evidence:** `NOTE:180-198` names the fields and says to "apply the same `loss_acceptance` rule to this logged subset". The kits contain no script that reads `metrics_<attempt>.jsonl` and `off1`/`off2` `steps.json`, builds the sorted subset per rank, applies `loss_acceptance`, or computes the 20-update slowest-rank wall ratio. r1_ops must hand-code the key order and subset.
   - The fields exist and round-trip exactly: `json.dumps` floats at `T/student_pilot/carrier_c1_run.py:2509`, with `components` and `stream_means` at `:1739-1740`.
   - **Smallest fix:** Add a ~30-line `kit_timing/continuation_check.py` that reuses `loss_acceptance` and the wall-median rule. Test it with one passing and one failing fixture.

4. **INFO: The audit's processor manifest is operator-supplied and not tied to the trainer's model pin.**
   - **Evidence:** `S/out/kit_timing/data_only.py:58` loads `--manifest "$BASE_MANIFEST"`. The trainer instead uses the manifest that `prepared()` returns from `load(pinned(receipt['model']))` (`T/student_pilot/carrier_c1_run.py:792,800,2929,2940`).
   - **Smallest fix:** In `data_only.py`, either require `run.file_pin(args.manifest) == receipt['model']`, or use `run.load(run.pinned(receipt['model']))` and drop the flag.

5. **INFO: The line-number explanation for the production log is wrong.**
   - **Evidence:** `S/out/REPORT.md:216-217` and `NOTE:256-257` say the mirror "has eight extra config lines". `L/look2.out` is the same file. It contains 8 carriage returns (at LF-lines 421, 425-427), which Python's `splitlines()` counts as line breaks: 720 lines versus 712 by `wc -l`.
   - With standard numbering, the shape lists are at 694/698/702/706. `REPORT.md:18` cites `702,706,710,714`; line 710 is a `TOK` line and 714 does not exist.
   - The test itself (`S/work/test_round4_kits.py:31-42`) is correct because it pins the step identities.
   - **Smallest fix:** Cite 694/698/702/706 and state the carriage-return cause.

## Checks

The checks open with the two the dispatch asked for first, then follow its numbered checks (1)–(5).

**Grid audit and replay rule (previous HIGH 1, MEDIUM 2): fixed.**
- `audit.py:35-40` caps `t` and `h*w` independently of orientation and records one actual maximum-volume grid plus the set of observed grids.
- The test feeds all 288 real rows (5/7/9/6 portraits) and refuses `[33,20,26]`, `[32,22,26]` and `[32,0,26]`.
- The replay rule is passable in both branches: probability 1 in the bitwise branch, and at least 0.20 under OFF nondeterminism (finding 2).
- Kill rule 2 is concrete: slowest-rank median `wall_seconds` over updates 2–21 must be below 1.00× the first launch's last 20. Kill rule 1 reuses the replay rule against `off1`/`off2`.

**(1) OFF byte-identical: pass.**
- I re-applied the four diffs to `B` in a temp dir under `S/work/test_runs/`: zero offset or fuzz. The result is identical to `T` (949 files, 22 touched). All 22 manifest output hashes and the four patch hashes match, and `out/patches` equals `out/patches_b21` and `out_round4/patches_b21`.
- With all switches `'0'`:
  - `record()` returns `{}` (`T/student_pilot/c1_switches.py:34-36`).
  - `cpu_prefetch` appears only under fallback `'1'`, and `decoded_cache` only when the cache is non-zero (`carrier_c1_run.py:1729-1734`).
  - The startup payload stays the original three values (`:2922-2923`).
- These are the bytes on which the previous review ran its cross-tree all-OFF parity check.

**(2) ON semantics: unchanged.**
- No trainer bytes changed.
- New `S/work/test_round4_mixed.py` mixes fallback and prefetched groups on one rank. Records, gradients, weights and optimizer state are exact, and its all-fallback mutation fails as intended.
- Resume-time readers of `metrics_*.jsonl` use named fields or `.get`, with no strict key-set check (`carrier_c1_run.py:1321-1329,2777-2800`), so 03 ON's `performance` key is safe across the resume.

**(3) Kits executable as written: yes.**
- `write_plan.py:32-50` calls the trainer's `prepared(cfg)`. `train()` builds `Rows` from `prepared(cfg, admission=True)`; `admission` only adds a warning in final mode (`carrier_c1_run.py:793-797,2921,2989`). The merged receipt is pinned in the plan. All pins are absolute (`p3_provenance.py:44-51`), so the plan writer does not depend on its working directory.
- `input_json` round-trips through the trainer's `load` (tested).
- The pose path imports `augment` at call time (`carrier_c1_data.py:159,189-199`), so the coverage wrapper observes real calls.
- The audit's success sidecar is written with `open('x')` only after every check passes. `replay_compare.py:82-85` re-checks `grid_rows` and worker augmentation.
- Every field `replay_compare` reads is written by `launch.py:101-106,183-195` and by `data_only.py:135-146,155-156`.
- Runtimes:
  - Audit about 42 min, 45–60 with startup. Hashing about 6.8 GB per rank-update at a measured 1.6 GB/s adds about 9 min over 80 legs, so the range is plausible.
  - Replay 50–75 min, with a 3,600-s cap per leg.

**(4) Earlier findings: each fixed with a test that fails before.**
- On the snapshot, `S/out/evidence/round4_kits_before.txt` shows `failures=11, errors=1`. The error is the real portrait refusal.
- Coverage: findings 1, 2, 3 and 9 are code fixes with code tests; findings 4–8 are documentation with presence tests; finding 10 is a new mixed test with a mutation control.

**(5) Gain estimates: honest and unchanged.**
- 03 is about 0 (≤0.1 s).
- 02 is ≤0 at low reuse.
- 01 is 0–28.2 s and possibly negative.
- The wall-ratio rule is labelled as a no-regression threshold, not a speedup claim.

## Reruns by this review

All runs used `nice -n 10`, `taskset -c 0-7`, 8 threads, `CUDA_VISIBLE_DEVICES=''` and `PYTHONDONTWRITEBYTECODE=1`.

| Run | Result |
|---|---|
| `test_round4_kits.py` | 12 OK |
| `test_round4_kits.py` with `SO_KIT_BUNDLE=out_round4` | `FAILED (failures=11, errors=1)` |
| `test_round4_mixed.py` | 1 OK, `SO_MIXED_FALLBACK_PROOF` |
| `test_round4_mixed.py` with `SO_MIXED_MUTATION=1` | FAILED at the transition assertion |
| `test_round3_kits.py` | 7 OK |
| `test_round3_plan_cli.py` | 1 OK |
| `run_cpu_tests.py --local-only` (so_round3, prefetch, cache, metrics, review, round2, joint) | 26 OK; 3 socket cases not run |
| `ARTIFACTS.json` | 173 hashes OK |

Also run: patch replay, the grid-cap and processor `smart_resize` probes, and the replay-rule Monte Carlo.

Side effects: one `cr5_patch_*` directory and test `so_*` directories under `S/work/test_runs/` only.
