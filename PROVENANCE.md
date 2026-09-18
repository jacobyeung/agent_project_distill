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

## Missing requested inputs

At initial inspection on 2026-09-18, these patch directories were empty:

- `/home/jjyeung/agent_project/agent/scratch/devin_lanes/qwen35_student_trainer_20260918/out/patches/`
- `/home/jjyeung/agent_project/agent/scratch/devin_lanes/student_fullscale_trainer_20260918/out/patches/`

The fallback patch directories were absent:

- `/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/codex_qwen35_student_trainer_fallback/out/patches/`
- `/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/codex_student_fullscale_trainer_fallback/out/patches/`

These inputs will be checked again at the student-import step. No patch or trainer implementation is fabricated.
