# Task: fifth change in H1-0 package b01ec87a6f29b (CPU only): optional type restriction from a/1.json
Workspace /scratch/jjyeung/orch_n30/h10_stage/work/k330 (K = kit). Same hard rules: no git, ssh, network, GPU, kills, deletion; write only inside k330.

## Why
ORCH ruled: the next Orchard job reads only types 3 and 4 (object_abs_distance, room_size_estimation); camera types are already banked from job 170631. The runner today always walks all five ORDER types.

## Change (minimal, default behavior unchanged when the key is absent)
- job.check_inputs: accept optional `inputs['types']`: a non-empty list of unique names from common.ORDER, in ORDER order; anything else refuses ("Invalid type selection").
- job.main: pass `types=inputs.get('types') or list(ORDER)` into run_cfg.
- runner: run/summarize/identity walk only the selected types, keeping each type's index t = ORDER.index(kind) for journal dirs and dispatch names (so type 3 stays journals/3/<gpu>); IDENTITY gains `types` (keep `order` = full ORDER); SUMMARY counts only selected types; the optional phase logic is unchanged.
- Nothing else (no scorer, reader, admission or staging change).

## How
1. Edit K/orchard_h10/job.py and K/orchard_h10/runner.py; rebuild from the CURRENT package (0.tgz e01ada41..., the sl118 fix) replacing payload members orchard_h10/job.py and orchard_h10/runner.py only, updating only their pins. Back up current package to K/orchard_h10/package_e01ada41/. Self-test no-change rebuild first.
2. Verify byte-identity of all other members; load_helpers/verify_config/opacity/compile; rerun the 4 package checks, test_fsw_bind, test_distance_imports, and the existing runner/summary tests in K/tests (find them with grep in K/tests only, e.g. test_build9.py, test_h10.py) — run what can collect on this node; report collection errors with cause.
3. New test K/tests/test_types_selection.py: with the runner's injectable launcher/clock (as existing runner tests do), types=['object_abs_distance','room_size_estimation'] launches only t=3 and t=4, journals under 3/ and 4/, SUMMARY expected counts only those; absent key = all five; invalid lists refuse in check_inputs.
4. Append <=14 lines to k330/REPORT_terminator.md: new 0.tgz sha+bytes, plan, PACKAGE.json + five file hashes, tests.
