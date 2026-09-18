# Import provenance

This repository assembles the distillation stack for REQ-20260917-232. Imports are code snapshots, not launch approval or benchmark-score nominations. The r1315 collector is explicitly pre-remediation; the separate remediation lane owns review findings R1–R6.

## Recording convention

All dates below are UTC. A directory mapping applies to every imported file below that destination, with the same relative path unless its inventory says otherwise. Git commits identify committed source trees; contract SHA-256 values identify copied candidate packages. An uncommitted source is identified as such rather than attributed to its repository's HEAD. Source packages and run artifacts remain untouched.

## Preserved baseline

On 2026-09-18, commit `861c27865fcfbcddc62e8ca8a314f177f692ef16` preserved the existing tree at `/home/jjyeung/agent_project_distill` without changing its contents. Its source was the unfinished local assembly, not a verified upstream checkout. The preserved paths are `.claude/`, `.devin/`, `agent/`, `collector/`, `docs/`, `tools/`, `CLAUDE.md`, and `.gitignore`. Git's existing ignore rules excluded outputs and caches.

The baseline included `agent/scratch/devin_lanes/repo_migration_20260918/devin.out`, because the original ignore rules did not cover that live log. The collector import stops tracking it without removing its working copy or rewriting the baseline. The added ignore rules also exclude `_quarantine/` and `venv/`.

## Collector

| Destination | Source | Immutable source identifier | Copy date |
|---|---|---|---|
| `collector/` | `/home/jjyeung/agent_project/agent/rounds/candidates/r1315_vsi_distill_gt_training_tolerant_sparse/` | `CONTRACT.json` SHA-256 `a22120745ebc96a19bdcfa2c610db65fcd0f7ea27d60879e4d5eac9bfc12fec8` | 2026-09-18 |

The source is untracked in the main repository at inspection time; its repository HEAD was `b3500228fa175058df3fd1d910b189beb4d67399`. The copy includes `CONTRACT.json`, `README_DELTA.md`, and all code, tests, and prompts. Bytecode caches are excluded. The partial collector snapshot is overwritten without changing source bytes.

Verification on 2026-09-18: `diff -rq -x __pycache__ <source> collector` returned 0. The requested `PYTHONDONTWRITEBYTECODE=1 python -B -m unittest discover -s collector -p 'test_*.py'` ran 20 tests in 8.198 seconds: 15 passed, 0 assertion failures, and 5 errors; exit 1. Two modules could not import `pytest`, and three sparse-grounding tests require the unset `SPARSE_FIXTURE_ROOT`. Errors are recorded, not fixed. Function-style pytest tests are not exercised by unittest discovery. The complete output is retained at `agent/scratch/devin_lanes/repo_migration_20260918/out/collector-tests.log`.

The preserved partial destination is `_quarantine/collector_partial_20260918T114433Z/`; no files were deleted. A fresh destination avoided the node's slow overwrite behavior. The source package remains untouched.

## Ground-truth adapters

The comparison baseline is `/home/jjyeung/agent_project_r1313_gt_teacher/agent/rounds/candidates/r1313_vsi_distill_gt_training/`, from clean source commit `1205888a3e76d74665ce9e105e23f1c894e12451`. Each ScanNet adapter was selected with `diff -rq` against exactly this directory, plus all source `test_*.py` files. All adapter copies were made on 2026-09-18 and verified byte-for-byte against their sources.

| Destination | Exact source directory | Source pin | Files |
|---|---|---|---|
| `gt_adapters/scannetpp_multilabel/` | `/home/jjyeung/agent_project/agent/rounds/candidates/r1313_vsi_distill_gt_training_prep_v2/` | `PREP_CONTRACT.json` SHA-256 `41ade5e4a989ea278d89204995d18152108e711be863d48a6a0c9487aaf0020a` | 12 |
| `gt_adapters/scannet_v1/` | `/home/jjyeung/agent_project/agent/rounds/candidates/r1313_vsi_distill_gt_training_scannet_v1/` | No CONTRACT exists; untracked source, inventory SHA-256 `bf4099d350b5c8740828f4e4bd20131b7cd285e57041c7cdd50714077567e08d` | 12 |
| `gt_adapters/scannet_v2/` | `/home/jjyeung/agent_project/agent/rounds/candidates/r1313_vsi_distill_gt_training_scannet_v2/` | `CONTRACT.json` SHA-256 `a1b6ce4c38862acb955606d62f790532e60566ee752cd2521f29dd3beacc8bfd` | 16 |
| `gt_adapters/arkit/` | `/home/jjyeung/agent_project/agent/scratch/devin_lanes/arkit_gt_adapter_20260918/work/r1313_vsi_distill_gt_training_arkit_v1/` | No CONTRACT exists; untracked source, inventory SHA-256 `4d5de411e7e610b973bfc561c55ab71c309f55d79c52f91375f115d262325c72` | 45 |
| `gt_adapters/adt/README.md` | `/home/jjyeung/agent_project/agent/scratch/devin_lanes/adt_gt_adapter_20260918/` | New placeholder; source has no implementation or commit to import | 1 |

ScanNet inventories:

- `scannetpp_multilabel`: `PREP_CONTRACT.json`, `PREP_V2.md`, `donor_grounding.py`, `mesh_membership.py`, `prep_contract.py`, `prepare_gt_scene.py`, `test_prep_v2.py`, and the five inherited tests below.
- `scannet_v1`: `SCANNET_CONVENTION.md`, `prepare_gt_scene.py`, `scannet_adapter.py`, `scannet_contract.py`, `scannet_sens.py`, `test_scannet_adapter.py`, `validate_scannet.py`, and the five inherited tests.
- `scannet_v2`: `CONTRACT.json`, `SCANNET_CONVENTION.md`, `gt_scene_assets.py`, `prepare_gt_scene.py`, `scannet_adapter.py`, `scannet_checks.py`, `scannet_contract.py`, `scannet_sens.py`, `test_scannet_adapter.py`, `validate_scannet.py`, `verify_scannet_assets.py`, and the five inherited tests.
- The five inherited tests are `test_admission.py`, `test_collector.py`, `test_gt_tools.py`, `test_runner_transport.py`, and `test_trace_archive.py`.
- ARKit includes all root `*.py`, `README*`, and `pool_harness/*.py` files. Its sole non-code prompt, `prompt_base_1313.txt`, is excluded by the requested code/tests/README-only rule. No selected ARKit file exceeds 5,000,000 bytes.

No requested `README_DELTA.md` exists in the three ScanNet source directories. Neither `CONTRACT.json` nor a source commit exists for the untracked ScanNet v1 and ARKit snapshots; these omissions are disclosed rather than replaced with invented contracts. The main repository HEAD at inspection was `b3500228fa175058df3fd1d910b189beb4d67399`, which is context only for untracked files.

The source inventory hashes above bind the concatenated `sha256sum` output for copied files, in root `*.py`, `*.md`, `*.json`, then `pool_harness/*.py` glob order, retaining absolute source paths. Full inventories are retained in `agent/scratch/devin_lanes/repo_migration_20260918/out/{scannetpp_multilabel,scannet_v1,scannet_v2,arkit}-source.sha256`. The multilabel inventory hash is `0098e8a95c29092be9eef623438cfbf1cee4f3c521792cca245b1ca9ce412a5e`; the ScanNet v2 inventory hash is `5f9cb8cc810f656fe6aad755da576a31d128067b9e5872db921bce5ea4fa8a1f`.

The ScanNet delta directories deliberately omit unchanged runtime modules. They are not standalone sealed packages, and copying their contracts does not grant admission. The ADT placeholder grants no runtime capability.

## Materialization wrappers

All three variants were copied on 2026-09-18 from `/data2/jjyeung/agent_project_data/vsi_distill_training_20260917/runtime_control/gt_teacher_r1313/materialization_v2/`. Each destination has exactly six source files: `common.py`, `run_batch.py`, `validate_scene.py`, `launch_cpu.sh`, `test_wrapper.py`, and `CONFIG.json`. Each file compares byte-identically with its source. `materialize/README.md` is new integration documentation.

| Destination | Source directory below the root above | Source CONTRACT.json SHA-256 |
|---|---|---|
| `materialize/wrapper_codex_v1/` | `wrapper_codex_v1/` | `55f03e2c0c7484add0aa19e51a6f2236b3d1b45e119c20a7d5c746a1b94350ed` |
| `materialize/wrapper_prep_v2/` | `wrapper_prep_v2/` | `ef46fbfa744bbdd36d6fbeff2fc982cd3ca52ddd3e5d4faa325fd82bfc2fa56b` |
| `materialize/wrapper_scannet_v1/` | `wrapper_scannet_v1/` | `88ede2fb3f8567e544fbc77e00bb6134cd6445243f6e134df80530eee2f3ced3` |

Every other source entry is excluded: runtime and generated-test directories, plans, contracts, status/health files, receipts, locks, PID files, logs, and dry-run outputs. The source contract files are hashed above, not copied. The variants have different implementations; keeping three subdirectories under one `materialize/` root preserves each config's code pairing without an unreviewed rewrite. Their original absolute paths and launch identities remain examples, not admission for a new run.

## Student histories

The source repository is `/data2/jjyeung/agent_project_data/student_diagnostic_pilot_20260918/trainer_repo`. Imports use committed branch trees, not its dirty working tree. `git subtree` is unavailable on this node, so the migration uses `git fetch <source> <branch>`, a history-preserving `git merge --allow-unrelated-histories -s ours --no-commit`, and `git read-tree --prefix=<destination>/ -u FETCH_HEAD`. Each imported subtree must have the same Git tree object as its source before committing. An already-reachable ancestor needs only its prefixed tree added; its history is already preserved.

| Destination | Source branch | Source commit | Import date |
|---|---|---|---|
| `student/landing/` | `landing-20260918` | `7ba0394dc83c34dc903f9d972e0ddce27024614f` | 2026-09-18 |
| `student/eval-harness/` | `eval-harness-landing-20260918` | `ded50d39bbebf7c2c8f0fb1d4c3c4e95d0d26c81` | 2026-09-18 |
| `student/shakedown/` | `shakedown-20260918` | `a1dca361d403e3c92b16d8624ff800983b5bc358` | 2026-09-18 |

The landing source/import tree is `c8de144b3b99c0da40cb7162931d04c049c6b924` (66 files). The evaluation source/import tree is `2997558e82a4906c8d2f196b2244396777652e5f` (48 files). The shakedown source/import tree is `fda7b7db7f28c6c1a46ec8c8c2111570fbd2cbea` (22 files); its commit was already an ancestor of the imported landing history. Original authors, commit messages, and parent relationships remain reachable through the merge history. The migration does not reset, amend, rebase, or edit the source repository.

### Student exclusions

- `<source repository>/artifacts/`: all runtime artifacts; present but untracked/ignored.
- `<source repository>/.cache/`: all caches; present but untracked/ignored.
- `<source repository>/.tmp/`: all temporary outputs; present but untracked/ignored.
- `<source repository>/venv/`: excluded by policy; absent at inspection. The sibling private environment is also not part of the source repository or import.
- Files over 5,000,000 bytes: none occur in the three requested branch tips or their reachable history. The bounded history audit checked 82 unique blob objects totaling 1,063,008 bytes and found zero excluded paths or oversized blobs. No history filtering is needed.
- Source working-tree edits and untracked files: excluded from the branch imports. If a path exists in a selected branch, only that branch's committed bytes are imported. The explicit support-file supplement below is the sole exception.
- The source `.git/` directory is never copied. Git transfers only the objects needed to preserve the requested histories.

### Clean-adapter support file

The committed landing branch imports a support module that was absent from its Git tree. Native integration reproduced `ModuleNotFoundError: student_pilot.detailed_audit` before any test could run. On 2026-09-18, `student/landing/student_pilot/detailed_audit.py` was copied verbatim from `/data2/jjyeung/agent_project_data/student_diagnostic_pilot_20260918/trainer_repo/student_pilot/detailed_audit.py`. Its source and copied SHA-256 is `c96ca6a21691c353cbbc381356856d77f40796ed871f4af04106267391a45b5b`. The source file is untracked, so no source commit or CONTRACT can pin it; its exact file hash and this repository's supplemental commit preserve it instead. No existing converter, admission, or scoring code was rewritten. The original branch tree remains preserved in its import commit.

## Student patches

On 2026-09-18, the dataset-builder patch `/home/jjyeung/agent_project/agent/scratch/devin_lanes/student_dataset_builder_20260918/out/patches/0001-Keep-admitted-student-datasets-reproducible-and-scen.patch` applied cleanly and unchanged with `git apply --index --directory=student/landing`. Its SHA-256 is `fe4ba358ffc18a2b38ed4503caf85bd72a187b7a596982d66ff462f9e1df390d`; its format-patch source commit is `987538e2c59259bbfeade3264902e73c0b22ba90`.

The patch adds these eight paths below `student/landing/`: `student_pilot/dataset_admission.py`, `student_pilot/dataset_builder.py`, `student_pilot/dataset_loader.py`, `tests/dataset_builder_fixture.py`, `tests/fixtures/dataset_builder_sources.json`, `tests/test_dataset_builder.py`, `tests/test_dataset_loader.py`, and `tests/test_dataset_native.py`. No source hunk was edited, and no conflicting patch required quarantine. Test results are recorded in the final verification section.

## Additional documentation

On 2026-09-18, `docs/VSI_DISTILLATION_GT_TEACHER_FEASIBILITY_RESULT.md` was copied byte-for-byte from `/home/jjyeung/agent_project/agent/agentic_information_5.0/VSI_DISTILLATION_GT_TEACHER_FEASIBILITY_RESULT.md`. Source and destination SHA-256: `be8365e220f5c3bfab503b5839cf6db974d41ab1615260b5d5baddf4cdc17863`. The source is untracked and has no source commit or contract; its exact file hash is the import pin. The main repository HEAD was `b3500228fa175058df3fd1d910b189beb4d67399` at inspection. Other imported documentation is preserved in the initial assembly commit or the pinned student branch trees above.

## Missing requested inputs

At initial inspection on 2026-09-18, these patch directories were empty:

- `/home/jjyeung/agent_project/agent/scratch/devin_lanes/qwen35_student_trainer_20260918/out/patches/`
- `/home/jjyeung/agent_project/agent/scratch/devin_lanes/student_fullscale_trainer_20260918/out/patches/`

The fallback patch directories were absent:

- `/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/codex_qwen35_student_trainer_fallback/out/patches/`
- `/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/codex_student_fullscale_trainer_fallback/out/patches/`

The student-import recheck confirmed the same empty primary directories and absent fallback directories. No patch bytes exist to apply or preserve under `student/patches_pending/`; no Qwen3.5-specific or full-scale trainer implementation is fabricated. Those two requested imports remain blocked on their producing lanes.
