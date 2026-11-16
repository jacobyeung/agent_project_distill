# Codex build: run K1's downstream stages (tables, refit, render, report) on a declared capture set (kit copy only; phase code and manifest unchanged)

Model gpt-6-astra, effort high. Write only in /scratch/jjyeung/orch_n30/k1_ops3/work/codex_gtset/ (patched scratch kit copy, diff, new pins, tests, REPORT.txt). Read-only: /scratch/jjyeung/orch_n30/k1_ops3/kc/** (executed kit copy), /scratch/jjyeung/orch_cd/**, /scratch/jjyeung/k1/** (live run roots; never write there), /data2/jjyeung/agent_project_data/distill_design/REFREEZE_AMENDMENT_1_K1_RASTERS_20261115.md and REFREEZE_PREREGISTRATION_20261115.md. No Git, ssh, kill, GPU (CUDA_VISIBLE_DEVICES=''), network, deletion, or recursive search outside named folders. Read /home/jjyeung/.claude/CLAUDE.md "Key Trinity Cluster Rules" first. Python: /scratch/jjyeung/envs/p1cpu/bin/python (tests), /scratch/jjyeung/envs/sam3_capretry_native_v1/bin/python (torch). The node is CPU-starved: run tests with OMP/MKL/OPENBLAS threads = 1 and nice.

## Why
Amendment 1 scores K1 twice: a primary analysis on the 296 captures whose GT raster equals its manifest pin, and a sensitivity analysis on all 300, with unpinned rebuilt rasters for 4 (arkitscenes/41125829, 42899325, 45261532; scannetpp/ef69d58016). Every registered statistic, mark and rule stays the same. The kit refuses both today:
1. k1_pipeline.check_manifest(m,'downstream') runs B.checked(c['gt']) for all 300 (line 37), so the 4 absent rasters raise.
2. A 296-capture manifest fails 'K1 requires exact selected capture set' (line 27).
3. Changing c['gt'] changes B.digest(c), so cached() (line 90) refuses with 'Cache capture differs', and B.digest(m) changes, which the phase BINDINGs record.
4. k1_report.py takes expected_ids from every manifest row (line 76) and report() demands the full denominator.
Manifest: /scratch/jjyeung/orch_n30/k1_ops3/work/codex_arkit_timing/K1_MANIFEST.arkit_timing.json (sha 91a2dbf9...). It must stay byte-identical.

## Frozen inputs (do not regenerate or edit)
/scratch/jjyeung/orch_n30/k1_ops3/work/gt_sets/: GT_SET_PRIMARY_296.json (sha 2b82af52...) and GT_SET_SENSITIVITY_300.json (sha e305c4be...), format {canonical: {path, sha256, pinned[, manifest_pin]}}; SHA256SUMS. Read-only.

## Change (smallest that does it)
1. Build in a NEW copy of the kit under codex_gtset/ (copy kc/k1_build/work/kit_k1a there). Never write the executed kit copy kc/: a tower_sam run executes from it and verifies its files at start.
2. tables (and every downstream stage that reads GT or iterates captures: trace tables -> refit -> render/responses -> k1_report): an explicit `--gt-set FILE` option. With it, GT checks and reads use the set's entries (each file hashed against the set's sha256); captures outside the set are skipped; c, m and their digests are untouched, so cached() and the phase bindings keep working; TABLE_RECEIPT (and every later receipt) records the set's sha256, pinned/unpinned counts and the skipped canonicals. A pinned=false entry is refused unless an explicit `--sensitivity` flag is given; with it, the receipt and the report say SENSITIVITY in their first line. k1_report gains `--ids-from TABLE_RECEIPT` and restricts expected_ids to the rows of the tabled captures, recording the set sha and n. Without the options, behaviour is byte-for-byte unchanged.
3. Do not change k1_phases.py, native_kit/*, K1_RULES.json, or anything in B.source_identity() / the producer pins of phase receipts. Prove it (identity and sha before/after, as in work/codex_maxbytes/evidence/).
4. New DEPENDENCIES.json from kc/.../out/DEPENDENCIES.json with only the changed files re-pinned, keys at the kc/ deployment paths (the operator copies the patched files into kc/ after tower_sam ends); list each change.
5. Tests (each must fail or be meaningless on the old code where applicable):
 (a) with a set listing all captures of a fixture, tables and report outputs are byte-identical to the unchanged kit's;
 (b) a subset fixture tables only the listed captures and records the skipped list and the set's sha256 in TABLE_RECEIPT;
 (c) tables refuse a pinned=false entry without --sensitivity; with it, receipt and report first lines say SENSITIVITY;
 (d) tables refuse a listed capture whose cache is missing or differs;
 (e) caches written before the change are accepted: take two real capture dirs from /scratch/jjyeung/k1/run_tower_sam_2 (read-only; copy them into codex_gtset/ first) and show they pass cached()/the tables entry checks, stating the reason from the BINDING and DEPENDENCIES logic.
 Also run native_kit/test_kit.py and test_guards.py on the patched copy.
6. Say whether anything in the Orchard Part B package (/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events/k1_ops3/PART_B_JOB_DESCRIPTION.md) needs the change (phases are unchanged, so it should not); the own phase's output must be tabled by the same changed tables/report code.
Report (REPORT.txt): unified diff (difflib, file gtset.diff), new pins, identity proof, all test output, file hashes, and the exact operator commands for the primary and sensitivity analyses (tables -> refit -> render -> report). An independent review follows before use.
