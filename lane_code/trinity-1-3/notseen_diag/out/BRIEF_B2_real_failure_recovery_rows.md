# Codex build brief B2: recovery rows whose `not seen` statuses come from the real reader (rows only)

Written by lane notseen_diag on 2026-11-17 and not dispatched; the orchestrator dispatches it. Suggested call: `codex_dispatch.sh implement <workdir> <this file> --model gpt-6-astra --effort high --label b2_realmiss`. Workdir is a fresh folder on /scratch. Do not ssh, kill processes or use Git, do not submit any job or write outside the workdir, and do not modify any other lane's files (copy inputs in read-only).

## Why
Tree build 9 admits 1,532 `a0_recovery` rows (sha256 f5166900). Every one carries exactly one simulated `not seen`, then stops calling and answers from the frames. The continuation is right: after a real miss, step 544 keeps calling and 33 of 150 dev-S1 distance reads hit the call cap. The failures it simulates are wrong (`DD/H1_0_NOT_SEEN_DIAGNOSIS_20261117.md`, Answer 6):
- **Names:** door, bed, tv, table and refrigerator lead the simulated misses (434 rows), and they fail on 1 of 89 real pairs. The real top names (heater, computer mouse, paper bag, blanket, bucket, nightstand, shoe rack, shoes, power strip, radiator, slippers) are rare or missing.
- **Datasets:** ScanNet++ is 58% of rows against 77% of real failed pairs.
- **Two misses:** no row misses both objects, but 11 of 62 real failure reads do.

Real failures come from the selector head's null slot on low-presence or small SAM 3 candidates (67 of 74 pairs), and from SAM 3 finding nothing (6 of 74). Rows built on the reader's own statuses teach the model what it will actually meet.

## Inputs (the orchestrator stages these into `<workdir>/in/`)
1. `a0_recovery.jsonl` from `trinity-1-3:/scratch/jjyeung/orch_n30/tree_rebuild_w/work/rows_slices/slices_final/` (sha256 f5166900). Its builder is the A0 rows builder named in each row's `provenance.builder` (`work/a0/build.py` of the rows lane that produced build 9's slices), with the formatter `trace_format/box_v313.py:513-567`.
2. The reader's stage-1 code from the H1-0 payload: `b/e2e_reader/{stage1,grounding}.py`, `b/heads/selector/**`, `tree/student_pilot/{routed_candidates,routed_features,geometry_profiles}.py` and `tree/trace_format/box_v313.py`. A partial copy is at `trinity-1-3:/scratch/jjyeung/orch_n30/notseen_diag/work/f3/p446`; the full payload is on Orchard `okh7/e6fc152498/p446`. Add the selector head weights `run_iso` (sha256 6d97c524) from the b04 lane (`trinity-1-18:/scratch/jjyeung/n30_mirror/b04_e2ehook/` or `trinity-3-30:/scratch/jjyeung/orch_n30/b04_e2ehook/heads/selector/work/run_iso`).
3. The raw-prompt SAM 3 proposals and G3T geometry of the row captures. Today these are the K1 raw tables and caches of the b04 lane (`trinity-1-18:/scratch/jjyeung/orch_n30/b04_e2ehook_sl/full_raw`, `data/pull_raw.tar` sha256 4831304f) and the K1 SAM 3 teacher pass (`DD/OWN_GROUNDING_HEAD_K1_20261116.md`, 286 captures). The row captures of `a0_recovery` must be joined to these by canonical scene; report the join coverage.
4. The evidence bundle `EV/notseen_diag/notseen_evidence_20261117.tgz` (sha256 7a5b17d9), whose `pairs_cache.json` holds the real-failure distribution. `EV` = `/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events`.

## Build
1. **`stage1_replay.py` (CPU).** Given a capture's raw-prompt SAM 3 proposals (480x640 RLE, score, presence, joint >= 0.05, cap 30), a geometry and the selector head, it reproduces the reader's stage 1 exactly: `cache_for`, `routed_candidates.lift` (floor 0.3), `link`, `scene_candidates` with the name alone, `accept_features`, `selector_inputs.candidate_vectors`, `with_null` and argmax. It returns the status the reader prints, either `<name>: not seen` or the selected candidate, which `box_v313.ground` then renders. The geometry is a `ProfileGeometry` built either from G3T x scale (now) or from own depth and pose arrays (once B1's per-read `.npz` dumps or an own-geometry prefill exist; take the arrays as input, never as a constant). It must match the reader within 1e-9 on the b04 fixture `tests/test_stage1_k1.py` and on a hand-built fixture with a known null decision.
2. **Status census.** Run the replay on every (capture, name) operand pair of the `a0_recovery` source rows, and of any other distance training rows the orchestrator names, under G3T x scale geometry. Write `CENSUS.jsonl` with the per-pair status, candidate count, null and best logits, presence, mask area and dataset. Compare its per-name and per-dataset not-seen rates with the dev-S1 real distribution in `pairs_cache.json`, and report the overlap.
3. **Rows.** Rebuild the recovery slice with the existing A0 builder and formatter. The only changes:
   - The missed operands are the pairs whose replayed status is `not seen`.
   - The status bytes are the replay's, through `box_v313.ground`.
   - Rows where both operands replay as `not seen` keep both misses, in call order, and the row stops calling after the second miss.
   - The share of each name and dataset follows the census, capped so that no name exceeds 10% of rows.

   Keep the continuation form, the GT answer, the unit text and every admission gate of build 9 unchanged. Rows whose replayed status is seen do not become recovery rows. Report the row count and why rows were dropped.
4. **Own-geometry variant (kit only).** Write `own_geometry_prefill.md` and the script that would run step-544 prefill on the census captures to dump own depth (32 x 51 x 51), `pose9` and gravity, in the layout B1 dumps. Price: about 0.5 H100-h for 300 captures on Orchard general. Do not run it. The census and rows rerun from those arrays with `--geometry own`.

## Tests (CPU, log in `out/TESTS.txt`)
- Replay identity on the fixtures above. Planted variants must fail: floor 0.25, a null that never wins, cross-name pooling switched on, and a 640x480 canvas swap.
- Any rebuilt row with no real miss renders byte-identical to the build-9 row of the same source (same builder, same seed).
- Every recovery row's status line equals the replay's status, through the formatter, byte for byte.
- Distribution report: tables of simulated (build 9), census and rebuilt rows by name, dataset and misses per row.

## Deliverables (`<workdir>/out/`)
`stage1_replay.py` and tests, `CENSUS.jsonl` with its sha256, the rebuilt `a0_recovery_real.jsonl` with its sha256 and row counts, `REPORT.md` (join coverage, distributions, what the next leg's mix should take, open gaps), the own-geometry kit and `REMOVAL_CANDIDATES.md`. Admission of the new slice into a training tree stays with the rows owner and one cross-family review, because it changes training rows.
