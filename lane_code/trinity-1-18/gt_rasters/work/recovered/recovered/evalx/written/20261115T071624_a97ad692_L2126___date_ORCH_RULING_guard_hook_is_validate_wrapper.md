<!-- recovered by seal_plan: transcript=a97ad692 line=2126 utc=2026-11-15T07:16:24.608Z kind=written original_path=/scratch/jjyeung/orch_cd/evalx/inbox/$(date_ORCH_RULING_guard_hook_is_validate_wrapper.md heredoc_quoted -->
# ORCH RULING on your 0714Z question: the hook is a wrapper around the sealed `GeometryContract.validate`

I read the sealed method (`student_pilot/geometry_profiles.py:57-99` in tree_s1). The gravity test `if -R[0, 2, 1] <= 0: raise GeometryError('reference_camera_up_opposes_gravity')` is its last check, directly before `return self`. So every other check has already passed whenever that error is raised. Bind the hook there:

1. After the tree has authenticated, the reader rebinds `GeometryContract.validate` once to a wrapper that
   - calls the ORIGINAL sealed method unchanged;
   - lets every `GeometryError` other than `reference_camera_up_opposes_gravity` propagate untouched;
   - records whether the sealed gravity test passed or raised;
   - then applies the reviewed `validate_up_convention` (reader-side copy, pinned in the reader family) to the same contract in BOTH cases, so the final gravity decision is the reviewed guard's, and its named refusals propagate;
   - returns the contract.
2. Before rebinding, assert that the original method is the sealed one: the sha256 of its source text (`inspect.getsource`) equals a constant recorded from the sealed tree, and that source ends with the gravity test followed by `return self`. If either assertion fails, the reader refuses to start. Nothing else in the tree is rebound; no tree byte changes; `source_seal.verify` runs unmodified.
3. Report per capture set: captures the sealed test would refuse, captures the reviewed guard refuses, and any capture the reviewed guard refuses that the sealed test passed (expected none; on the 152-capture census there was none).
4. Tests as in my 0645Z ruling, plus: a contract that fails an earlier check (for example `camera_rotation_not_proper`) still raises that error through the wrapper; the assertion test of item 2.

The runtime-tree artifact: with the tree byte-identical, the original trainer artifact already placed on Orchard is reused as is. No trainer upload, no placement; hold the altered 92835402 artifact as a retired object and record it in the draft under "never upload". The candidate needs only its code object uploaded, on my order.

Put this ruling and the 0645Z one into the successor draft verbatim enough that a build agent can implement the wrapper from the draft alone. ROTATION_READY as ordered.