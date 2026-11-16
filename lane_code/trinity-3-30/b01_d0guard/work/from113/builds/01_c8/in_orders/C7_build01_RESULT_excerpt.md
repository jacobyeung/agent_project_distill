
**Diff for you:** `work/milestone/C7_INCREMENTAL_DIFF_vs_C6_code.patch` (1,668 lines, 33 files, sha256 049f5541...). It leaves out the 11,416-line regenerated `CANDIDATE_FAMILY_06.json`; the builder's full diff is `builds/01_guard_wrapper/out/INCREMENTAL_DIFF_vs_C6.patch` (0fad46e0...). One sentence per file explains each change in `builds/01_guard_wrapper/out/DIFF_FILES.md`.

**What C7 is** (`work/milestone/native_package_s24_07`):
- The runtime is the sealed tree, byte-identical. The source-map constants are back to b01ce449 in `native_bootstrap.py` and `runtime_tree.py`. The namespace binds the real tree read-only. `guard_tree_scope` and the edited-trainer exception are removed from `native_pin_graph.py` and `native_local_check.py`, and trainer assets must again equal the baseline.
- `native/out2/gravity_guard.py` (sha256 a62e3975...) holds the reviewed `validate_up_convention`, copied exactly, and `install()`. `install()` checks the `inspect.getsource` sha256 05cc553d, checks the terminal gravity test plus `return self` by AST comparison, refuses a second call, and rebinds only `GeometryContract.validate`.
- The wrapper lets every other error propagate, recomputes `R = camera_to_world[:, :3, :3]` as the sealed method does, and gives the final verdict to the reviewed guard. It counts distinct captures, keyed by (capture set, native).
- The worker installs the guard after the real restore, in both `pilot` and `prepare_full_geometry`. An install refusal writes `native/GUARD_INSTALL_REFUSAL.json` before any forward pass.
- The packet, the request and the report carry both guard hashes. `native_metrics.validate_gravity_guard` checks the three per-set lists against the geometry dispositions.
- The R1, 6,000 s and selector changes are byte-unchanged, per `builds/01_guard_wrapper/out/FINAL_AUDIT.json`.
- The local code object is `C7/packages/code_override_05.tar` (3,594,240 bytes, sha256 fc57a805...). It is not uploaded.
== /scratch/jjyeung/orch_cd/official544/events/20261115T0802Z_RESULT_direct_six_reviewed.md
# RESULT: six-task step-544 kit is CPU-rehearsed; owner review and deployment admission remain

The sealed kit reads 4,008 official VSI-Bench questions across six direct tasks and 288 scenes. It passes sixteen real-item CPU cases, the actual namespace/PREPARE/generation/scoring sequence, resume, injected errors and process-group stop tests. The engine and stored model tensors are synthetic. **No official step-544 model score, GPU validation or launch approval exists.**

**Action:** review the launcher/admission/scoring changes, then let the Orchard owner adopt and submit the packet. This lane made no Orchard call or GPU launch. Absolute distance (834 items) and room size (288) are **not read here: native reader required**. They receive neither generated answers nor layout probes in this read. All eight released direct subtypes retain two first-item probes.

## Protocol and comparison

| Setting | Accepted step-544 dev-S1 read | This official read | Reference comparison |
|---|---|---|---|
