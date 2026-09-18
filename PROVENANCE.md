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

## Missing requested inputs

At initial inspection on 2026-09-18, these patch directories were empty:

- `/home/jjyeung/agent_project/agent/scratch/devin_lanes/qwen35_student_trainer_20260918/out/patches/`
- `/home/jjyeung/agent_project/agent/scratch/devin_lanes/student_fullscale_trainer_20260918/out/patches/`

The fallback patch directories were absent:

- `/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/codex_qwen35_student_trainer_fallback/out/patches/`
- `/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/codex_student_fullscale_trainer_fallback/out/patches/`

These inputs will be checked again at the student-import step. No patch or trainer implementation is fabricated.
