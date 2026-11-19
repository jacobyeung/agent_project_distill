# Read-only review: export-parameterised rebuild of a sealed GPU forward package (model Astra, high effort)

Work only in this directory; read files here only. No ssh, network, git, GPU, edits outside REVIEW.md. Write your verdict to REVIEW.md (at most 60 lines): GO, GO AFTER FIXES (list), or NO-GO, with each finding citing file:line.

## Context
A sealed Slurm package (job 170235) ran an "own" phase: it loads a VLM checkpoint (step-544 export) through `read_runtime.load_model` and dumps per-capture depth grids (32x51x51 float64) and gravity into own.npz (`k1_phases.py own()`, `boundaries.py GPU.own()`). We now need the same grids from a step-400 export trained by a different trainer tree (b83a8a35 instead of tree_s1_admissionfix_168872). The approved design (D1): each export is loaded by the trainer tree that trained it; change only the step guard, the selected trainer tree, and the pins that follow from the export; the grid code (51x51 query, gravity, projection, what own.npz holds) must stay byte-identical. A step-544 parity run of the same changed package must first reproduce job 170235's grids.

## Files
- `build.py`: the builder (ran on the cluster). It decodes the old batch payload, patches three wrappers and the kit's `boundaries.py` by exact-anchor replacement, writes two manifests (p544: old manifest + `gpu.export_step=544`; p400: also `gpu.artifact/config/data_receipt` -> step-400 pins and `gpu.trainer_selection='export_seal'`), overlay tars, a.json configs and two batch scripts. `BUILD.json` is its receipt.
- `diff_*.txt`: unified diffs old -> new for stage_job.py, batch_entry.py, phase_worker.py (job wrappers) and boundaries.py (kit). Full old_/new_ files are present.
- `tree_diff.txt`: diff of the only 4 files that differ between the two trainer trees (7 files are new in b83a8a35; none removed).
- Context (unchanged): bindings.py, k1_phases.py, k1_pipeline.py, read_runtime.py, common.py, runtime_tree.py, evalpath_runtime.py (verify_trainer), native_stage.py, job_support.py.

## Check
1. Does any change alter what the grid code computes for a given loaded model (k1_phases.own, boundaries GPU.own after load, GRID_UV source)? Is p544 executing exactly 170235's code path apart from the step-guard expression and the identity/transport plumbing?
2. With `trainer_selection='export_seal'`, `selected_trainer=None` makes `verify_trainer` derive pins from the export config's code seal. Is that a correct, non-weakened authentication of tree b83a8a35, given LEGS1_TREE points bindings/common at the new tree root? Any path where the old tree's modules could be imported instead?
3. `same_kit()` in phase_worker replaces `assert all(reference[k]==v ...)`. Is it strict (same key set after the declared tree-root mapping; only the declared boundaries.py hash may differ)?
4. `closure()` in stage_job: strict enough (pinned archive sha, refuses differing collisions, skips only the export's own m400 dir)? Ordering after depth/runtime staging correct?
5. CPU-check mode in batch_entry (no CUDA_VISIBLE_DEVICES): stops before GPU work, returns no grids, cannot advance the pointer or publish a misleading COMPLETE?
6. Anything that would make the p400 run fail at staging/admission that you can see from these files.
Report only verified problems; do not redesign.
