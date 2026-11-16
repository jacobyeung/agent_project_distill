# C8 native routed read

## Question and answer

Can pilot-9 code support the ordered refusal, limit, selector, and gravity changes without altering the authenticated trainer tree?

The draft implements those changes and preserves the sealed tree. Core logic tests and static pins pass where the inputs permit evaluation. The candidate cannot be admitted: the required Python environment is absent, and the streamed masks, raw geometry, NumPy overlay, and frames have no completion markers. Whole-worker pilot/full execution and production branch coverage remain unproved.

## Implementation

Program refusals remain scored rows and retain their denominators. The pilot projection excludes them from token and timing validation and reports counts. A family with no timed sample cannot supply an admissible full-read timing projection. The full report counts unflagged program-refusal rows.

The pilot limit is 6000 seconds, and the scheduler request is two hours so it can cover that limit. The full limit remains 21600 seconds. These values are implemented in `out/c8/sources/sj/orch_cd/evalx/work/milestone/orchard_native/native_launcher.py` and checked by `out/tests/test_core.py`.

The selector records the first sorted key in each present family in the fixed `FAMILIES` order. It uses camera displacement for parity when present and the first present family otherwise. The dev-S1 probe remains `devrows:devs1cam-0020d0cefc26c693abeb6c4e5951cc07` (`out/SELECTOR_PROOF.json`). The camera-free fixture comes from the real dev-S1 task members in the metadata archive; no official items were read (`out/tests/CAMERA_FREE_FIXTURE.json`).

The guard wraps the sealed validator only after restore. Installation checks the sealed source hash, terminal AST, exception-class identity, and single installation. Other geometry errors propagate unchanged. Preparation and reload paths bind contracts to their capture; an already-bound contract can be checked by GroundV3 outside that context. The request, packet, and reports carry both identities. `out/GUARD_CALL_SITES.md` lists each path and its missing execution evidence.

The pilot retains the existing selection rule: one refused distance pair if a capture refuses, otherwise ten passing pairs with the registered family and dataset coverage. Both branches pass the core tests (`out/tests/core.log`).

## Evidence and limits

- The core suite passes 14 tests under system Python, with a test-only gzip compatibility shim (`out/tests/core.log`, `out/tests/test_core.py`). This does not establish production-runtime compatibility.
- Independent stdlib arithmetic over all 84 real camera-to-world arrays reproduces 11 sealed refusals and finds one reviewed refusal, `d3/41254810` (`out/GUARD_CENSUS.json`). This is not execution of the NumPy wrapper. The reviewed predicate accepts `d3/41069053`.
- The sealed tree's 792 pinned files match their supplied hashes (`out/PIN_AUDIT.json`). The build changes no tree bytes.
- The audit passes 9 checks and marks 37 N/E, including checks with partial local evidence (`out/PIN_TABLE.md`, `out/PIN_AUDIT.json`). Unavailable deployment authority and runtime assets are not inferred from earlier pilots.
- The draft code archive contains 46 members: the original member set, the guard, and the separately named mask receipt (`out/PACKAGE_STATUS.json`). The executable shell-script modes are fixed without changing their source bytes.
- The real launcher seal function executed with a local numeric-generation fixture (`out/PACKAGE_STATUS.json`). `FAMILY_C8.json` retains `PENDING_UPLOAD` in the code object's generation and md5 fields; this deliberately fails cloud admission until the operator fills both fields.
- The mask receipt currently contains a producer-only scalar rebind. The actual cache-bind CLI has not run, so the receipt remains unverified (`out/MASK_REBIND_STATUS.json`). The rehearsal harness requires the CLI to reproduce it exactly before worker execution.
- Both rehearsal preflights record their free-space readings, required inputs, and storage limits (`work/rehearsal_pilot/LIMITS.json`, `work/rehearsal_full/LIMITS.json`). Both stop before worker execution (`work/rehearsal_pilot/RESULT.json`, `work/rehearsal_full/RESULT.json`).
- `out/coverage/UNEXECUTED.md` inventories unexecuted source lines conservatively. The full worker body, report tail, and IN_JOB_ADMISSION are explicit findings. Neither mode has a whole-worker coverage pass.

## Options rejected

Editing the trainer tree would invalidate its authentication. Relaxing the sealed validator's earlier checks would change more than the ordered gravity decision. Removing refusal rows would change denominators. Inventing upload generations, treating metadata equality as execution, or weakening validators to accommodate missing inputs would misstate admission.

The production interpreter is inaccessible in this execution environment; its shared-memory symlink target may exist outside the sandbox. The build cannot repair that access within the task's constraints. System Python is used only for source assembly and explicitly labelled diagnostic tests. Production numerical tests and rehearsals must use the specified runtime.

## What may fail and how it will be detected

The wrapper may expose an unbound contract path; its recorder raises `gravity_guard_capture_context_missing`. Unexpected sealed-source or exception identities refuse installation and write the dedicated receipt before forward execution. Geometry errors other than the named gravity refusal remain fatal. Per-set recorder/disposition checks detect missing or inconsistent refusal accounting.

The CPU harness is supplied but has not executed beyond preflight. Its GPU-boundary fixtures, production processor imports, parity, real mask replay, geometry conversion, full-mode fixture projection, and return chain may require harness corrections. Such corrections must stay outside shipped sources unless they identify an independently authorized production defect. No claim is made that the harness is validated.

The historical APPROVED/P5 references in local admission helpers are not supplied here. Their checks cannot be completed from the available objects; the build does not weaken them or replace historical authority with a fabricated receipt (`out/NATIVE_LOCAL_CHECK.json`).

## Status and remaining gate

Status: **DRAFT_NOT_ADMITTED**. The operator must make the named runtime accessible, supply completed streamed inputs, run the numerical tests and both whole-worker modes, resolve every execution finding, reproduce the mask rebind, and complete upload metadata and review before any seal or launch. `out/DECISIONS.md` records the defaults used in this build. The bounded input poll ended before its maximum wait because the runtime independently blocks the proofs (`out/INPUT_WAIT_STOP.json`). No input timeout or governor failure is inferred.

The comparison to pilot 9 is retained because the user explicitly requires a bounded four-change reconstruction and a source diff; it is evidence of scope, not narrative history.
