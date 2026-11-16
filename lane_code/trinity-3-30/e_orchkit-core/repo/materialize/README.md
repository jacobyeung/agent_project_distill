# Ground-truth materialization wrappers

This directory groups three source-preserving wrapper variants. Each contains `common.py`, `run_batch.py`, `validate_scene.py`, `launch_cpu.sh`, `test_wrapper.py`, and an example `CONFIG.json`. The implementations differ, so each config stays beside its matching code rather than sharing an incompatible implementation.

| Variant | Config purpose |
|---|---|
| `wrapper_codex_v1/CONFIG.json` | Materialize the clean ScanNet++ scene pool with the original r1313 preparer. |
| `wrapper_prep_v2/CONFIG.json` | Materialize ScanNet++ scenes whose instance memberships overlap, using the multilabel preparer. |
| `wrapper_scannet_v1/CONFIG.json` | Materialize ScanNet scenes with the ScanNet v1 preparer and sensor-frame alignment checks. This is not the corrected ScanNet v2 admission configuration. |

The configs are examples copied verbatim. They retain production paths, source hashes, coordination roots, and run identities. They are not new launch authorization. Do not execute the imported launchers unchanged: their paths and sealed-package checks still refer to the source deployment. A runnable deployment needs a committed config, a clean-tree provenance check, valid assets and coordination ownership, and the applicable admission review.

Runtime directories, plans, contracts, status files, logs, receipts, locks, and generated tests remain at their source under `/data2/jjyeung/agent_project_data/vsi_distill_training_20260917/runtime_control/gt_teacher_r1313/materialization_v2/`. The repository's `PROVENANCE.md` records the source contracts without importing those runtime artifacts.

Safe local syntax checks from the repository root:

```sh
for variant in wrapper_codex_v1 wrapper_prep_v2 wrapper_scannet_v1; do
  bash -n "materialize/$variant/launch_cpu.sh"
done
```

The inherited `test_wrapper.py` suites depend on original plans, contracts, scene receipts, and coordination fixtures. They are preserved for deployment validation, not presented as portable unit tests. This import does not run controllers or modify shared coordination state.
