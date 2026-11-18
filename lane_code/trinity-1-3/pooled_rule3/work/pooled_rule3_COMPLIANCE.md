# pooled_rule3_COMPLIANCE: fix 2 (export provenance) of COMPLIANCE_POOLED_V2.md, now enforced by pooled_harm_rule_v3.py

The rule's statistics are unchanged: `W`, `stat`, `draws`, `ci`, `decide` are byte-identical between v2 and v3, so the simulations (`sim_exec.py`) and fixes 1, 3, 4, 5 and 6 carry over. v3 changes only the provenance checks. All line numbers refer to `pooled_harm_rule_v3.py` (sha256 3c7661fe28589f8ef12003d4c0ade78f9ae12fbc0fe0514cfa2a508ecb84d880).

## Refusal cases the brief requires
| Case | Where it is refused | Test (`test_pooled_rule_v3.py`) |
|---|---|---|
| Fetched archive missing from the manifest (any read but the two pinned baselines) | `check_manifest` :171-172; malformed entry :173-175 | `test_point1_omitted_archive` :270 |
| Archive missing on disk or changed | :176-177 | (v2 test `test_read_not_from_fetched_archive_refused`) |
| Archive's decoded ITEMS.jsonl hash differs from the manifest | :178-179 | `test_point1b_archive_content_differs` :279 |
| Receipt with empty or malformed bindings | :186-188 | `test_point2_empty_bindings` :286 |
| Receipts leave unbound run (via `run.artifact_path`, :159-161 ties path to run and step), artifact sha256, step, arm, reader package, read token, plan hash, archive sha256 | `RUN_BINDS`/`ARCHIVE_BIND` :67-69; check :195-197 | `test_point2b_each_required_binding` :297 (each of 8 fields, both sets) |
| Export artifact not the one the training run's `runs/<run>/m<step>/artifact.json` registers: receipt absent, path of another run or step, sha256 differs, `step` differs | `check_export_receipt` :201-213, called :313-314 (required for decisions; CLI :439-441) | `test_point3_invented_artifact` :311, `test_decision_cli_requires_receipt_and_ledger` :351 |
| Read sha256 (or export sha256) already recorded under another run or step, in the pinned prior reads or the ledger | `PRIOR` :70-79; `ledger_check` :390-397 | `test_point4_read_hash_recorded_elsewhere` :331 |

The reviewer's constructed case (D0 m200's read relabelled as R1 step 200, invented artifact eeee..., archive omitted, checksum-valid receipts with empty bindings) is refused at each point on its own: point 1 on the case itself; point 2 on the case with its archive restored; point 3 by `check_export_receipt` on the case's run block, and alone on an otherwise real manifest; point 4 by the prior reads (D0 m200's read is pinned under 359fcc3c step 200) and by a ledger line. `test_whole_case_refused` :264 refuses the whole case in decision and calibration mode.

## What still passes
- Both real baseline manifests pass `check_manifest(..., baseline=True)` and bind all of `RUN_BINDS` (`test_two_real_baseline_manifests_pass`); their sha256 are unchanged (dev-S1 e08a1d34..., R0-dev 86c8f993...).
- The three real reads give the registered object-size intervals to three decimals (`test_three_real_reads_object_size_intervals`): D0 m200 [-10.641, -1.668] / [-11.148, -1.208]; D0 m100 [-8.345, -0.967] / [-8.947, -0.588]; H1-1 m100 [-8.326, -0.711] / [-9.279, -0.275]; and v3 equals v1 on every type and the mean (`test_v2_equals_v1_on_three_reads`).
- CLI calibration with `--ledger` on D0 m200 printed "would STOP" and wrote two `kind: calibration` lines (`work/clitest/`).

## Open for the operator
- The export receipt is the run's `artifact.json` for the step, fetched unchanged (under 20 MB) from the run's home mirror `runs/673bc60f/m<step>/` into `<dir>/runs/673bc60f/m<step>/artifact.json`. The tool requires its `step` field; it does not pin the artifact schema name.
- No independent review of v3 yet.

## Test output (`cd work && python3 -W ignore -m unittest -v test_pooled_rule_v3`)
```
test_three_real_reads_object_size_intervals (test_pooled_rule_v3.Baselines) ... ok
test_two_real_baseline_manifests_pass (test_pooled_rule_v3.Baselines) ... ok
test_crosswalk_partition_equals_label_partition (test_pooled_rule_v3.Crosswalk)
The crosswalk changes no cluster: its rooms partition the items exactly as the read's room labels do. ... ok
test_every_item_maps_to_exactly_one_room (test_pooled_rule_v3.Crosswalk) ... ok
test_label_of_another_room_refused (test_pooled_rule_v3.Crosswalk) ... ok
test_no_physical_room_in_both_sets (test_pooled_rule_v3.Crosswalk) ... ok
test_rebuild_equals_pinned (test_pooled_rule_v3.Crosswalk) ... ok
test_scenes_of_one_room_are_clustered (test_pooled_rule_v3.Crosswalk) ... ok
test_unmapped_item_refused (test_pooled_rule_v3.Crosswalk) ... ok
test_unpinned_crosswalk_refused (test_pooled_rule_v3.Crosswalk) ... ok
test_draw_missing_a_type_is_redrawn (test_pooled_rule_v3.Draws) ... ok
test_real_reads_have_no_redraw (test_pooled_rule_v3.Draws) ... ok
test_baseline_manifests_describe_real_receipts (test_pooled_rule_v3.Provenance) ... ok
test_config_differs_from_baseline_refused (test_pooled_rule_v3.Provenance) ... ok
test_decision_read_must_be_r1 (test_pooled_rule_v3.Provenance) ... ok
test_internally_inconsistent_manifest_refused (test_pooled_rule_v3.Provenance) ... ok
test_missing_manifest_refused (test_pooled_rule_v3.Provenance) ... ok
test_mixed_export_refused (test_pooled_rule_v3.Provenance) ... ok
test_one_read_per_boundary_and_arm (test_pooled_rule_v3.Provenance) ... ok
test_read_file_named_by_no_manifest_refused (test_pooled_rule_v3.Provenance) ... ok
test_read_not_from_fetched_archive_refused (test_pooled_rule_v3.Provenance) ... ok
test_type_filter_claim_checked (test_pooled_rule_v3.Provenance) ... ok
test_valid_reads_pass (test_pooled_rule_v3.Provenance) ... ok
test_console_table (test_pooled_rule_v3.Reporting) ... ok
test_size_split (test_pooled_rule_v3.Reporting) ... ok
test_v2_equals_v1_on_three_reads (test_pooled_rule_v3.Reproduction) ... ok
test_decision_cli_requires_receipt_and_ledger (test_pooled_rule_v3.ReviewerCase) ... ok
test_point1_omitted_archive (test_pooled_rule_v3.ReviewerCase) ... ok
test_point1b_archive_content_differs (test_pooled_rule_v3.ReviewerCase) ... ok
test_point2_empty_bindings (test_pooled_rule_v3.ReviewerCase) ... ok
test_point2b_each_required_binding (test_pooled_rule_v3.ReviewerCase) ... ok
test_point3_invented_artifact (test_pooled_rule_v3.ReviewerCase) ... ok
test_point4_read_hash_recorded_elsewhere (test_pooled_rule_v3.ReviewerCase) ... ok
test_whole_case_refused (test_pooled_rule_v3.ReviewerCase) ... ok
test_reviewer_case_unrounded_bounds_decide (test_pooled_rule_v3.StopAtZero)
Every interval lies below zero by less than the display rounding: v1 rounded first and stayed SILENT. ... ok
test_zero_difference_is_silent (test_pooled_rule_v3.StopAtZero) ... ok

----------------------------------------------------------------------
Ran 36 tests in 57.156s

OK
exit 0
```
