VERDICT: GO

Reviewer: independent, read-only, CPU only. Paths: `S=/scratch/jjyeung/orch_n30/so_step`, `T=S/work/b21_final/work/tree_r1` (patched build 21), `B=/scratch/jjyeung/orch_n30/so_xstore/in/tree21b/work/tree_r1`, `NOTE=S/out/NOTE_FOR_TREE_REBUILD.md`, `TF=/scratch/jjyeung/envs/p1cpu/lib/python3.12/site-packages/transformers`. Student-pilot files are under `T/student_pilot/`.

## Answer

- **First launch of vehicle N (01, 02 and fallback OFF; 03 ON allowed by the note): GO.**
  - The trainer patches are byte-identical to the round the previous review cleared.
  - All-OFF output keeps its input structure. The new fallback key appears in `performance` only when fallback is ON.
  - The coordinator's 31-test gloo gate passed on these bytes (`S/work/round3_b21_gloo_by_coordinator.txt`: `Ran 31 tests in 880.158s`, `OK`, `EXIT=0`, 12:55:19 UTC).
- **First continuation with 01 ON under the note's acceptance and kill rules: GO.**
  - Previous LOW 1 is fixed: the cap is 576 patches, so 16:9 and square sources pass and larger grids refuse.
  - Previous LOW 2 is fixed: replay and continuation kill rule 1 now pool D and M over all four ranks. The NOTE states both false-refusal rates and labels them as simulation.
  - Every remaining finding fails closed.
  - Before the CPU audit, r1_ops should run the one-line receipt check in finding 1.
- **Side effect of this review:** rerunning the documented `kits` test overwrote three CPU-profiler evidence files in `S/out/evidence/`. `ARTIFACTS.json` now fails 3 of its 200 hashes (finding 2). Patches, manifest, kits, NOTE and REPORT are untouched.

## Findings

1. **LOW: The 576 cap is correct for the default pixel budget, but it is derived from an encode path production does not use, and it ignores the r1/b7 per-frame budget.**
   - **Wrong source cited:** `S/out/kit_timing/audit.py:6-9` and `NOTE:100-107` derive the cap from `batches.py:155` (32 frames, `32*384*384`). That path requires `grid_t*2 == 32` (`batches.py:165`), so it cannot emit the production `[32,h,w]` grids.
   - **Actual production path:** duplicate layout repeats 32 frames to 64 (`carrier_c1_data.py:204-205`). It then calls `encode_frames` with `count=64` and `DEFAULT_PIXELS=(128², 384²)` per frame (`carrier_c1_data.py:208-209`, `pose_samples.py:37,214-215`). The installed `smart_resize` keeps `t_bar*h_bar*w_bar <= max_pixels` (`TF/models/qwen3_vl/video_processing_qwen3_vl.py:35,54-57`), so the spatial limit is still `384²/16² = 576`. The value is right for run A's configuration.
   - **When the budget differs:** a receipt with `b7_inputs` or `r1_training` sets `processor._b7_layout` (`carrier_c1_run.py:1268-1270`). `carrier_c1_data.py:209` then uses its `max_pixels`, a required integer (`b7_inputs.py:34-36`). N is bound through `cfg['r1_training']` (`r1_handover.py:30-37`), but the audit keeps 576 regardless.
     - If N's per-frame `max_pixels` is above 147456, the audit refuses (01 stays OFF).
     - If it is below, the cap is merely looser than the processor.
     - Repository r1/b7 fixtures use 147456 (`T/tests/test_r2_build7.py:25,166,207`), so a mismatch is unlikely. N's config is not among the supplied inputs.
   - **Test labelling:** `S/work/test_round5_kits.py:33-51` runs `smart_resize` with 32 frames and labels the result `[32,h,w]`, but a real 32-frame grid has t=16. The h and w equal the 64-frame production call, so the assertions still hold.
   - **Image grids:** the same cap applies to `image_grid_thw` (`audit.py:36-42`), while `encode_image_row` passes no size (`carrier_c1_data.py:406`). Run A has no single-image rows; if N has them, the audit refuses (fail-closed).
   - **Smallest fix:** before the audit, r1_ops checks that `$AUDIT_DIR/prepared_receipt.json` has neither `b7_inputs` nor `r1_training`, or has `max_pixels == 147456`. Alternatively, `data_only.py` passes `getattr(processor,'_b7_layout',{}).get('max_pixels',384*384)//256` to `Coverage` and records it in `grid_cap`. Either way, cite `carrier_c1_data.py:204-209` and `pose_samples.py:37,214-215` in place of `batches.py:155`.

2. **LOW: Rerunning the documented `kits` suite rewrites hashed delivery evidence, and this review did so.**
   - **Evidence:** `S/work/test_kits.py:135,136,144` write `cpu_profiler_table.json`, `cpu_trace.json` and `cpu_phase_table.json` into `S/out/evidence/`. REPORT's runner includes this suite. The lane's own run regenerated them at 09:48 EST, before it wrote `ARTIFACTS.json` at 09:50.
   - **Effect of this review:** my rerun at 10:00:40 EST overwrote all three. `ARTIFACTS.json` now fails those three hashes; the other 197 match. These files hold CPU-fixture profiler output, not production measurements. The pre-rerun bytes cannot be restored: the `out_round5/` copies have different hashes. No other file under `S/out` changed (`find S/out -newer S/out/ARTIFACTS.json` lists only these three).
   - **Smallest fix:** point the three writes at `S/work/test_runs/`, then regenerate those three `ARTIFACTS.json` entries, or have the orchestrator accept the new hashes.

3. **INFO: The processor-manifest check compares a symlink-resolved path with the raw pin path.**
   - **Evidence:** `S/out/kit_timing/data_only.py:15-18` requires `run.file_pin(path) == receipt['model']`.
     - `file_pin` resolves symlinks (`p3_provenance.py:61-62`).
     - The trainer's `pinned()` uses the raw pin path (`p3_provenance.py:44-51`); no relocation scope is active in the audit.
     - A pin path containing a symlink component would therefore refuse the correct file (fail-closed).
     - The test fixture builds its receipt with `file_pin` itself (`test_round5_kits.py:100-104`), so it cannot catch this case.
   - **Smallest fix:** compare the SHA-256 values and `Path(path).resolve() == Path(receipt['model']['path']).resolve()`. Alternatively, drop `--manifest`, since `:18` already loads `run.pinned(receipt['model'])`.

4. **INFO: `continuation_check.py` uses exit 1 for both a rule refusal and an input error, and does not require an accepted replay.**
   - **Evidence, exit codes:**
     - A refusal returns 1 (`S/out/kit_timing/continuation_check.py:67`).
     - Any `ValueError` or `JSONDecodeError` also exits 1, through a traceback.
     - `metrics()` parses every line (`:13`), including a partly written last line while rank 0 is appending (`carrier_c1_run.py:2508-2509`).
     - `NOTE:274` says any nonzero exit blocks acceptance, and kill rule 1 then turns 01 OFF. A transient read error could therefore be taken for a kill.
   - **Evidence, replay acceptance:** the checker reads `off1`/`off2` `steps.json` and the ON manifest but never `acceptance.json`. `NOTE:216` makes an accepted replay a precondition.
   - **Smallest fix:**
     - Exit 2 on input errors, and tell r1_ops in the NOTE to rerun on exit 2.
     - Skip a final line that has no trailing newline.
     - Require `json.loads((replay_out/'acceptance.json').read_text())['accepted'] is True`.

5. **INFO: Round 5 edited earlier tests without listing the edits.**
   - `S/work/test_round4_kits.py:46` now refuses `[32,20,30]` in place of `[32,22,26]`, which at 572 patches is now legal.
   - `S/work/test_round3_kits.py:93` now expects `max_spatial_area=576`.
   - Both edits are correct for the new cap. The REPORT's finding table omits them.

## Checks

The first three checks are the ones the dispatch asked to run first; checks (1)–(5) follow its numbering.

**Audit cap equals the processor limit (previous LOW 1): fixed, with finding 1's caveat.**
- `MAX_SPATIAL_AREA = (32*384*384)//(32*16*16) = 576` (`audit.py:8-9`).
- The audit accepts `[32,18,32]`, `[32,32,18]` and `[32,24,24]`. It refuses `[32,20,30]`, `[32,30,20]`, `[33,24,24]` and `[32,0,24]`.
- By hand from the installed `smart_resize`: 1920×1080 at 64 frames with a 64·384² budget gives β = 3.75 and 288×512 px, which is `[32,18,32]`. The sidecar records the shared cap (`data_only.py:80,147`).

**Replay and kill rule 1 pool over ranks (previous LOW 2): fixed.**
- **Replay:** `replay_compare.py:41-54` concatenates the rank 0–3 vectors and calls `loss_acceptance` once. `:115-116` makes the pooled result the only gate; per-rank results stay as diagnostics.
- **Continuation:** `continuation_check.py:41` uses the same helper on `components` and `stream_means` (`micro=False`).
- **Stated rates:** `NOTE:185-212` labels them as simulation.
- **Independent Monte Carlo:** 200,000 trials, seed 12345, different from the lane's. False refusal, per-rank versus pooled:

  | Scalars per rank | Per-rank | Pooled |
  |---:|---:|---:|
  | 1 | 80.28% | 12.94% |
  | 4 | 42.39% | 1.92% |
  | 5 | 35.15% | 1.28% |
  | 12 | 11.93% | 0.21% |
  | 20 | 5.01% | 0.05% |

  These match the NOTE within Monte Carlo error. The analytic one-scalar per-rank value is `1-(2/3)^4 = 80.25%`.
- **Previous review's fixture:** the lane is right that it cannot exist. For the rank with the largest D, the pooled bound equals that rank's own bound, so if every rank fails locally, the pooled rule fails too. The replacement test, in which each rank fails locally in turn while another rank supplies the spread, tests the intended property.

**Trainer patches byte-identical: yes.**
- The four diff hashes (`7ce3a5b6…`, `7695b70d…`, `c8712100…`, `ca65704e…`) and `manifest.json` (`238dd692…`) are equal across `out/patches_b21`, `out/patches`, `out_round5/patches_b21` and `out_round4/patches_b21`.

**(1) OFF byte-identical: pass.**
- Applying the four diffs to a copy of `B` with `patch --batch --fuzz=0 -p1` gave no offset or fuzz. `diff -rq` against `T` is empty, and both trees have 949 files.
- Executed `c1_switches`:
  - All switches `0`: `parse()=('0','0','0')` and `record()={}`, so there is no `performance` field and no fallback key.
  - 01 or 03 ON alone: three keys, without `C1_CPU_PREFETCH_FALLBACK`.
  - Fallback ON: adds the fourth key.
- `cpu_prefetch` is emitted only when fallback is ON (`carrier_c1_run.py:1730-1731`).

**(2) ON semantics: unchanged.**
- No trainer byte changed since the previous review.
- `test_round4_mixed.py`: 1 OK with `SO_MIXED_FALLBACK_PROOF` (records, gradients, weights and optimizer state bitwise).
- The coordinator's 31-test run is on these bytes.

**(3) Kits executable as written: yes, subject to findings 3 and 4.**
- The audit and replay commands are unchanged apart from the manifest pin check. `replay.sh` keeps the 3,600-s cap per leg.
- `continuation_check.py` reads only fields the trainer writes:
  - each metrics line is `{step, ranks}` (`carrier_c1_run.py:2508-2509`);
  - each rank entry carries `step`, `rank`, `components`, `stream_means`, `wall_seconds`, `data_seconds` and `performance` (`:1729,1735-1745`);
  - replay `steps.json[0]` and `manifest.switches` are written by `launch.py:101,183-195`.
- Because the checker runs with `-I`, its script directory is off `sys.path`. It inserts that directory itself (`:8`) and imports only `pooled_loss_acceptance`.
- Runtimes:
  - CPU audit: about 42 min (45–60 min with startup), estimated.
  - Replay: 50–75 min, estimated.
  - Continuation check: seconds; it only reads JSONL files.

**(4) Earlier findings: each fixed with a test that fails before.**
- `test_round5_kits.py` on `out_round5`: `FAILED (failures=6, errors=11)`. On `out`: 13 OK.
- What fails on the snapshot:
  - the four source subtests and the four pooled-replay subtests error on real refusals;
  - the continuation CLI tests fail because the script is absent;
  - the manifest test fails because the snapshot loads the processor before any pin check.
- INFO 5 (line citations): `look2.out` LF lines 694/698/702/706 are the shape lists.

**(5) Gain estimates: honest and unchanged.**
- 03 is about 0 (≤0.1 s).
- 02 is ≤0 at low reuse.
- 01 is 0–28.2 s and possibly negative.
- The wall ratio below 1.00 is labelled an operational no-regression threshold, not a speedup claim.

## Reruns by this review

All runs used `nice -n 10`, `taskset -c 0-7`, 8 threads, `CUDA_VISIBLE_DEVICES=''`, `PYTHONDONTWRITEBYTECODE=1` and all four switches `0`.

| Run | Result |
|---|---|
| `test_round5_kits.py` | 13 OK, `PROCESSOR_LIMIT: longest_edge=4718592; spatial_patches=576` |
| `test_round5_kits.py`, `SO_KIT_BUNDLE=out_round5` | `FAILED (failures=6, errors=11)` |
| `test_round4_kits.py` / `test_round3_kits.py` / `test_round3_plan_cli.py` | 12 / 7 / 1 OK |
| `test_review_kits.py` / `test_round2_kits.py` / `test_kits.py` / `test_kit_utilities.py` | 7 / 4 / 4 / 2 OK |
| `test_round4_mixed.py` | 1 OK, `SO_MIXED_FALLBACK_PROOF` |
| Patch replay onto `B` | Zero fuzz or offset; identical to `T` (949 files) |
| `ARTIFACTS.json` | 197 of 200 OK; 3 fail after this review's `test_kits.py` rerun (finding 2) |
| Monte Carlo and `c1_switches` probe | See the checks above |

## Side effects

- Three files in `S/out/evidence/` were overwritten by `test_kits.py` (finding 2).
- Created `S/work/test_runs/cr6_patch_bAem/` and the tests' own `so_*` directories under `S/work/test_runs/`.
- Nothing else was written outside this verdict.
